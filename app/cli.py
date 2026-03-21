"""
Command Line Interface (CLI) for the Health Coordinator.

Uses Typer to expose commands: `hc server start`, `hc tasks list`, `hc audit`.
"""
import typer
import asyncio
from sqlalchemy.orm import Session
from rich.console import Console
from rich.table import Table
from rich.json import JSON

from app.config import settings
from app.database import SessionLocal, Base, engine
from app.models import DBTaskRecord, SubagentAuditOutput, TaskRecord
from app.orchestrator.registry import load_contract, list_domains
from app.orchestrator.qwen_subprocess import run_subagent_audit
from app.logger import setup_global_logger, get_logger

setup_global_logger()
logger = get_logger(__name__)
Base.metadata.create_all(bind=engine)

app = typer.Typer(
    help="Health Coordinator CLI - orchestrates Qwen subagents for repository audits."
)
console = Console()


@app.command("server")
def start_server(port: int = 8000, host: str = "127.0.0.1") -> None:
    """Start the FastAPI server."""
    console.print(f"[bold green]Starting server at {host}:{port}...[/]")
    import uvicorn
    logger.info(f"Starting server at {host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)


@app.command("tasks")
def list_tasks(
    domain: str = typer.Option(None, "--domain", help="Filter by domain"),
    state: str = typer.Option(None, "--state", help="Filter by execution state")
) -> None:
    """Display tasks from the database in a table format."""
    db_session: Session = SessionLocal()

    try:
        query = db_session.query(DBTaskRecord)
        if domain:
            query = query.filter_by(domain=domain)
        if state:
            query = query.filter_by(executionState=state)

        records = query.all()
        logger.info(f"Retrieved {len(records)} tasks from database")

        # Sort by severity (critical first)
        severity_weight = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        records.sort(key=lambda r: severity_weight.get(str(r.raw_payload.get("severity", "info")).lower(), 99))

        table = Table(title="Health Coordinator Tasks")
        table.add_column("ID", style="cyan")
        table.add_column("Domain")
        table.add_column("Location", style="magenta")
        table.add_column("Details", overflow="ellipsis", no_wrap=True)
        table.add_column("Severity")
        table.add_column("Status", style="blue")

        for record in records:
            payload = record.raw_payload
            tags = payload.get("tags", [])
            location = tags[0] if tags else payload.get("domain", record.domain)
            title = str(payload.get("title", record.title)).replace('\n', ' ').strip()

            severity = str(payload.get("severity", "info")).lower()
            severity_styles = {
                "critical": "[bold red blink]critical[/]",
                "high": "[red]high[/]",
                "medium": "[orange3]medium[/]",
                "low": "[yellow]low[/]",
                "info": "[cyan]info[/]"
            }
            styled_severity = severity_styles.get(severity, f"[cyan]{severity}[/]")

            status = str(payload.get("approvalState", record.approvalState))

            table.add_row(
                str(record.id),
                str(record.domain),
                str(location),
                title,
                styled_severity,
                status
            )

        console.print(table)
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}", exc_info=e)
        console.print(f"[bold red]Error retrieving tasks:[/] {e}")
        raise typer.Exit(code=1)
    finally:
        db_session.close()


@app.command("audit")
def run_audit(
    workspace: str = typer.Argument(".", help="Repository path to audit"),
    domain: str = typer.Option(None, "--domain", help="Audit specific domain only")
) -> None:
    """Run an audit using Qwen subagents."""
    domains = [domain] if domain else list_domains()

    if not domains:
        logger.error("No subagent contracts found in agent-registry/")
        console.print("[red]No subagent contracts found in agent-registry/[/]")
        raise typer.Exit(code=1)

    logger.info(f"Starting audit on domains: {domains}")
    console.print(f"[bold purple]Running audit on {len(domains)} domain(s) against workspace '{workspace}'...[/]")

    async def run_all_subagents():
        tasks = []
        for target_domain in domains:
            contract = load_contract(target_domain)
            tasks.append(
                run_subagent_audit(
                    domain=target_domain,
                    rules=contract.get("auditRules", []),
                    schema_path=contract.get("outputSchema", ""),
                    workspace=workspace
                )
            )
        return await asyncio.gather(*tasks, return_exceptions=True)

    db_session: Session = None
    try:
        with console.status(f"[bold cyan]Running audit... (timeout: {settings.subagent_execution_timeout_sec}s)[/]"):
            results = asyncio.run(run_all_subagents())

        db_session = SessionLocal()
        task_count = 0

        # Get next task ID
        last_record = db_session.query(DBTaskRecord).order_by(DBTaskRecord.id.desc()).first()
        next_id = 0
        if last_record and last_record.id.startswith("TASK-"):
            try:
                next_id = int(last_record.id.split("-")[1])
            except ValueError:
                logger.warning(f"Invalid task ID format: {last_record.id}")
                next_id = 0

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Subagent failed: {result}", exc_info=result)
                console.print(f"[bold red]Subagent failed:[/] {result}")
                continue

            try:
                audit_output = SubagentAuditOutput(**result)
            except Exception as validation_error:
                logger.error(f"Invalid subagent output: {validation_error}", exc_info=validation_error)
                console.print(f"[bold red]Invalid subagent output:[/] {validation_error}")
                continue

            for index, finding in enumerate(audit_output.findings):
                next_id += 1
                task_id = f"TASK-{next_id:05d}"

                task = TaskRecord(
                    id=task_id,
                    sourceType="finding",
                    findingId=str(index),
                    domain=audit_output.domain,
                    title=finding.title,
                    description=finding.description,
                    priority=finding.priority,
                    severity=finding.severity,
                    approvalState="pending_review",
                    executionState="not_started",
                    verificationState="pending",
                    owner=audit_output.agentName,
                    tags=finding.affectedFiles
                )

                db_record = DBTaskRecord(
                    id=task.id,
                    sourceType=task.sourceType,
                    domain=task.domain,
                    title=task.title,
                    priority=task.priority,
                    approvalState=task.approvalState,
                    executionState=task.executionState,
                    owner=task.owner,
                    raw_payload=task.model_dump()
                )
                db_session.add(db_record)
                task_count += 1

        db_session.commit()
        logger.info(f"Successfully saved {task_count} tasks to database")
        console.print(f"[bold green]\nFound {task_count} issues. Run `hc tasks` to view.[/]\n")

    except Exception as e:
        if db_session:
            db_session.rollback()
        logger.error(f"Audit failed: {e}", exc_info=e)
        console.print(f"[bold red]Audit failed:[/] {e}")
        raise typer.Exit(code=1)
    finally:
        if db_session:
            db_session.close()


@app.command("task")
def view_task(task_id: str = typer.Argument(..., help="Task ID to view")) -> None:
    """Display full JSON payload for a single task."""
    db_session: Session = SessionLocal()

    try:
        record = db_session.query(DBTaskRecord).filter_by(id=task_id).first()

        if not record:
            logger.warning(f"Task not found: {task_id}")
            console.print(f"[bold red]Task '{task_id}' not found.[/]")
            raise typer.Exit(code=1)

        logger.info(f"Viewing task: {task_id}")
        console.print(f"\n[bold green]Task {record.id} (Priority: {record.priority})[/]\n")
        console.print(JSON.from_data(record.raw_payload))
    except typer.Exit:
        raise
    except Exception as e:
        logger.error(f"Failed to view task {task_id}: {e}", exc_info=e)
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(code=1)
    finally:
        db_session.close()


@app.command("approve")
def approve_task(task_id: str = typer.Argument(..., help="Task ID to approve")) -> None:
    """Approve a task for the fix phase."""
    db_session: Session = SessionLocal()

    try:
        record = db_session.query(DBTaskRecord).filter_by(id=task_id).first()

        if not record:
            logger.warning(f"Task not found for approval: {task_id}")
            console.print(f"[bold red]Task '{task_id}' not found.[/]")
            raise typer.Exit(code=1)

        payload = record.raw_payload
        payload["approvalState"] = "approved"
        record.raw_payload = payload
        record.approvalState = "approved"

        db_session.commit()
        logger.info(f"Task {task_id} approved")
        console.print(f"[bold green]Task {task_id} approved.[/]")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to approve task {task_id}: {e}", exc_info=e)
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(code=1)
    finally:
        db_session.close()


@app.command("ignore")
def ignore_task(task_id: str = typer.Argument(..., help="Task ID to ignore")) -> None:
    """Mark a task as ignored (will not be fixed)."""
    db_session: Session = SessionLocal()

    try:
        record = db_session.query(DBTaskRecord).filter_by(id=task_id).first()

        if not record:
            logger.warning(f"Task not found for ignore: {task_id}")
            console.print(f"[bold red]Task '{task_id}' not found.[/]")
            raise typer.Exit(code=1)

        payload = record.raw_payload
        payload["approvalState"] = "ignored"
        record.raw_payload = payload
        record.approvalState = "ignored"

        db_session.commit()
        logger.info(f"Task {task_id} ignored")
        console.print(f"[bold yellow]Task {task_id} ignored.[/]")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to ignore task {task_id}: {e}", exc_info=e)
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(code=1)
    finally:
        db_session.close()


@app.command("reset")
def reset_database(force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")) -> None:
    """Delete all tasks from the database."""
    if not force:
        typer.confirm("Delete all tasks from the database?", abort=True)

    db_session: Session = SessionLocal()

    try:
        count = db_session.query(DBTaskRecord).delete()
        db_session.commit()
        logger.info(f"Deleted {count} tasks from database")
        console.print(f"[bold red]Deleted {count} tasks.[/]")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Failed to reset database: {e}", exc_info=e)
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(code=1)
    finally:
        db_session.close()
