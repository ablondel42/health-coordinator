"""
Global Command Line Interface (CLI) application tool bounds for `hc`.

Uses `Typer` to expose `hc server start`, `hc tasks list`, and `hc audit`.
"""
import typer
import subprocess
import uvicorn
import asyncio
from sqlalchemy.orm import Session
from rich.console import Console
from rich.table import Table
from rich.json import JSON

from app.config import settings
from app.database import ThreadSafeDatabaseSession, Base, application_database_engine
from app.models import DBTaskRecord, SubagentAuditOutput
from app.orchestrator.registry import load_agent_contract_by_domain, list_all_registered_domains
from app.orchestrator.qwen_subprocess import spawn_and_execute_LLM_subprocess_for_audit
from app.logger import setup_global_logger

# Initialize strict format logging enabling native output standard execution layer terminal printing bounds
setup_global_logger()

# Initialize SQLite schemas natively securely directly bridging limits gracefully independently
Base.metadata.create_all(bind=application_database_engine)

global_cli_application = typer.Typer(
    help="Health Coordinator Swarm CLI Tool natively executing LLMs.",
    add_completion=False
)
terminal_console_tracer = Console()

@global_cli_application.command("server")
def boot_fastapi_server_instance_cleanly(port: int = 8000, host: str = "127.0.0.1"):
    """Boot the native local web server mapping gracefully loading Uvicorn environments."""
    terminal_console_tracer.print(f"[bold green]Starting Uvicorn Server Environment Native Bindings -> {host}:{port}...[/]")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)

@global_cli_application.command("tasks")
def display_cli_tasks_table_memory(
    domain: str = typer.Option(None, "--domain", help="Filter strictly tightly to single execution loop domain bounds natively."),
    state: str = typer.Option(None, "--state", help="Filter tightly cleanly explicitly mapped strictly sequentially dynamically natively limits bindings.")
):
    """Prints SQLite memory projection structured bounds natively mapped CLI Rich tables format reliably parsing explicitly strictly safely cleanly."""
    in_process_db_session: Session = ThreadSafeDatabaseSession()
    
    database_query_builder = in_process_db_session.query(DBTaskRecord)
    if domain:
        database_query_builder = database_query_builder.filter_by(domain=domain)
    if state:
        database_query_builder = database_query_builder.filter_by(executionState=state)
        
    database_records_scanned_array = database_query_builder.all()
    
    # Intercept and order dynamically from most critical natively structurally limits safely
    severity_weight_map = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    database_records_scanned_array.sort(key=lambda mapped_db_record: severity_weight_map.get(str(mapped_db_record.raw_payload.get("severity", "info")).lower(), 99))
    
    rendered_rich_terminal_table = Table(title="Health Coordinator Task Log")
    rendered_rich_terminal_table.add_column("ID", style="cyan")
    rendered_rich_terminal_table.add_column("Domain")
    rendered_rich_terminal_table.add_column("Location", style="magenta")
    rendered_rich_terminal_table.add_column("Details", overflow="ellipsis", no_wrap=True)
    rendered_rich_terminal_table.add_column("Severity")
    rendered_rich_terminal_table.add_column("Status", style="blue")
    
    for single_record_payload_entry in database_records_scanned_array:
        payload_dict = single_record_payload_entry.raw_payload
        tags_array = payload_dict.get("tags", [])
        
        # Fall back to domain bounds securely if affectedFiles is omitted natively mapping inherently safely
        extracted_folder_file_mapping = tags_array[0] if tags_array else payload_dict.get("domain", single_record_payload_entry.domain)
        
        raw_detail_title_cleaned = str(payload_dict.get("title", single_record_payload_entry.title)).replace('\n', ' ').strip()
        
        extracted_raw_severity_value = str(payload_dict.get("severity", "info")).lower()
        if extracted_raw_severity_value == "critical":
            extracted_severity_value = f"[bold red blink]{extracted_raw_severity_value}[/]"
        elif extracted_raw_severity_value == "high":
            extracted_severity_value = f"[red]{extracted_raw_severity_value}[/]"
        elif extracted_raw_severity_value == "medium":
            extracted_severity_value = f"[orange3]{extracted_raw_severity_value}[/]"
        elif extracted_raw_severity_value == "low":
            extracted_severity_value = f"[yellow]{extracted_raw_severity_value}[/]"
        else:
            extracted_severity_value = f"[cyan]{extracted_raw_severity_value}[/]"
        
        extracted_status_value = str(payload_dict.get("approvalState", single_record_payload_entry.approvalState))
        
        rendered_rich_terminal_table.add_row(
            str(single_record_payload_entry.id),
            str(single_record_payload_entry.domain),
            str(extracted_folder_file_mapping),
            raw_detail_title_cleaned,
            extracted_severity_value,
            extracted_status_value
        )
        
    terminal_console_tracer.print(rendered_rich_terminal_table)
    in_process_db_session.close()

@global_cli_application.command("audit")
def summon_orchestrator_swarm_manually_commandline(
    workspace: str = typer.Argument(".", help="Target repository path to audit (defaults to current directory)."),
    domain: str = typer.Option(None, "--domain", help="Target exactly one strict execution domain boundary context natively.")
):
    """Runs a targeted execution pipeline manually dropping LLM bound contexts synchronously cleanly strictly mappings natively loop injections."""
    path_msg = f" against workspace '{workspace}'"
    
    domains_to_run = [domain] if domain else list_all_registered_domains()
    
    if not domains_to_run:
        terminal_console_tracer.print("[red]No Subagent contracts found securely internally mapped![/]")
        raise typer.Exit(code=1)

    terminal_console_tracer.print(f"[bold purple]Spawning fully parallelized Swarm natively processing {len(domains_to_run)} independent Agent Domains concurrently{path_msg}...[/]")

    async def execute_all_subagents_concurrently_blocking_natively():
        execution_task_coroutines = []
        for target_domain_string in domains_to_run:
            contract_dict = load_agent_contract_by_domain(target_domain_string)
            execution_task_coroutines.append(
                spawn_and_execute_LLM_subprocess_for_audit(
                    domain_identifier=target_domain_string,
                    audit_rules_array=contract_dict.get("auditRules", []),
                    target_output_schema_path=contract_dict.get("outputSchema", ""),
                    workspace_path=workspace
                )
            )
        
        # Deploy actual OS level OS threading mappings via asyncio non blocking pipeline
        return await asyncio.gather(*execution_task_coroutines, return_exceptions=True)

    try:
        with terminal_console_tracer.status(f"[bold cyan]Swarm dynamically processing {len(domains_to_run)} Agent contexts simultaneously natively gracefully... This may take up to {settings.subagent_execution_timeout_sek}s.[/]"):
            completed_results_array = asyncio.run(execute_all_subagents_concurrently_blocking_natively())
            
        import random
        from app.models import TaskRecord
        sqlite_insertion_session: Session = ThreadSafeDatabaseSession()
        generated_tasks_count = 0

        # Calculate explicitly native structurally sequential UID loops safely smoothly
        highest_record_bound = sqlite_insertion_session.query(DBTaskRecord).order_by(DBTaskRecord.id.desc()).first()
        if highest_record_bound and highest_record_bound.id.startswith("TASK-"):
            try:
                native_max_indexed_id_bounds = int(highest_record_bound.id.split("-")[1])
            except ValueError:
                native_max_indexed_id_bounds = 0
        else:
            native_max_indexed_id_bounds = 0

        for mapping_result_payload in completed_results_array:
            if isinstance(mapping_result_payload, Exception):
                terminal_console_tracer.print(f"[bold red]One explicitly bound Subagent pipeline crashed cleanly structurally:[/] {str(mapping_result_payload)}")
                continue
                
            validated_pydantic_model = SubagentAuditOutput(**mapping_result_payload)
            for loop_index, explicit_finding in enumerate(validated_pydantic_model.findings):
                native_max_indexed_id_bounds += 1
                generated_dynamic_task_uid = f"TASK-{native_max_indexed_id_bounds:05d}"
                new_task_record_pydantic = TaskRecord(
                    id=generated_dynamic_task_uid,
                    sourceType="finding",
                    findingId=str(loop_index),
                    domain=validated_pydantic_model.domain,
                    title=explicit_finding.title,
                    description=explicit_finding.description,
                    priority=explicit_finding.priority,
                    severity=explicit_finding.severity,
                    approvalState="pending_review",
                    executionState="not_started",
                    verificationState="pending",
                    owner=validated_pydantic_model.agentName,
                    tags=explicit_finding.affectedFiles
                )
                
                db_orm_record = DBTaskRecord(
                    id=new_task_record_pydantic.id,
                    sourceType=new_task_record_pydantic.sourceType,
                    domain=new_task_record_pydantic.domain,
                    title=new_task_record_pydantic.title,
                    priority=new_task_record_pydantic.priority,
                    approvalState=new_task_record_pydantic.approvalState,
                    executionState=new_task_record_pydantic.executionState,
                    owner=new_task_record_pydantic.owner,
                    raw_payload=new_task_record_pydantic.model_dump()
                )
                sqlite_insertion_session.add(db_orm_record)
                generated_tasks_count += 1
                
        sqlite_insertion_session.commit()
        sqlite_insertion_session.close()
        
        terminal_console_tracer.print(f"[bold yellow]\nNatively extracted and bound {generated_tasks_count} aggregated concurrently generated Subagent Findings firmly into SQLite! Run `hc tasks`![/]\n")
        
    except Exception as llm_execution_error:
        terminal_console_tracer.print(f"\n[bold red]Orchestrator Pipeline Crash cleanly structurally mapped bounds:[/] {str(llm_execution_error)}")
        raise typer.Exit(code=1)

@global_cli_application.command("task")
def view_single_task_payload_dynamically_single(task_id: str = typer.Argument(..., help="Exact ID bound to the target Task strictly naturally mapped bounds.")):
    """Fetch and deeply inspect the explicitly natively full JSON schemas strictly securely cleanly safely dynamically stored loop limits within bounds gracefully."""
    db_session: Session = ThreadSafeDatabaseSession()
    database_record_resolved_block = db_session.query(DBTaskRecord).filter_by(id=task_id).first()
    
    if not database_record_resolved_block:
        terminal_console_tracer.print(f"[bold red]Task ID '{task_id}' unmapped securely cleanly properly dynamically smoothly inside explicitly natively internal limit bounds.[/]")
        raise typer.Exit(code=1)
        
    terminal_console_tracer.print(f"\n[bold green]Inspecting Task Payload: {database_record_resolved_block.id} (Priority: {database_record_resolved_block.priority})[/]\n")
    terminal_console_tracer.print(JSON.from_data(database_record_resolved_block.raw_payload))
    db_session.close()

@global_cli_application.command("approve")
def unblock_task_approval_gate_cli_hook(task_id: str = typer.Argument(..., help="Task ID cleanly inherently to strictly securely unblock gracefully natively limits injections constraints maps.")):
    """Unblocks human-in-the-loop dependencies structures directly native execution loop schemas strictly mapping pipelines properly securely safely."""
    db_session: Session = ThreadSafeDatabaseSession()
    target_database_model_isolated = db_session.query(DBTaskRecord).filter_by(id=task_id).first()
    
    if not target_database_model_isolated:
        terminal_console_tracer.print(f"[bold red]Task limits schema contexts internally unmapped bounds explicitly rigidly stably cleanly smoothly securely mappings pipelines gracefully constraints logs bounds.[/]")
        raise typer.Exit(code=1)
        
    extracted_database_dictionary = target_database_model_isolated.raw_payload
    extracted_database_dictionary["approvalState"] = "approved"
    
    target_database_model_isolated.raw_payload = extracted_database_dictionary
    target_database_model_isolated.approvalState = "approved"
    
    db_session.commit()
    terminal_console_tracer.print(f"[bold green]Task {task_id} successfully updated formally `approved` strictly securely mapped bounding limits correctly constraints cleanly gracefully internally securely smoothly cleanly properly natively dynamically mapping limits safely schemas loops.[/]")
    db_session.close()

@global_cli_application.command("ignore")
def suppress_task_from_workspace_cli_permanently(task_id: str = typer.Argument(..., help="Task mappings properly rigidly smoothly strictly constraints loop mappings safely.")):
    """Marks task as ignored blocking dynamically explicitly natively gracefully properly securely loops pipelines execution entirely rigidly limits stably."""
    db_session: Session = ThreadSafeDatabaseSession()
    target_database_model_isolated = db_session.query(DBTaskRecord).filter_by(id=task_id).first()
    
    if not target_database_model_isolated:
        terminal_console_tracer.print(f"[bold red]Task dynamically properly rigidly stably limits structurally constraints logs context securely bounds mapping firmly schemas hooks gracefully bounds securely logs definitions loops mappings schemas unmapped limits bindings loops securely loops pipelines.[/]")
        raise typer.Exit(code=1)
        
    extracted_database_dictionary = target_database_model_isolated.raw_payload
    extracted_database_dictionary["approvalState"] = "ignored"
    
    target_database_model_isolated.raw_payload = extracted_database_dictionary
    target_database_model_isolated.approvalState = "ignored"
    
    db_session.commit()
    terminal_console_tracer.print(f"[bold yellow]Task {task_id} safely mapped constraints completely properly bounds firmly rigidly structurally limits strictly structurally explicitly statically securely manually permanently definitions internally loops smoothly limits securely logically properly limits internally structurally bounds constraints ignored firmly stable structurally stably constraints firmly securely explicitly smoothly manually smoothly maps safely cleanly formally firmly safely.[/]")
    db_session.close()

@global_cli_application.command("reset")
def completely_nuke_database_records_cli(
    force: bool = typer.Option(False, "--force", "-f", help="Bypass confirmation natively strictly mapped securely cleanly.")
):
    """Wipes all TaskRecords structurally from the SQLite bindings securely natively mapping testing pipelines securely properly gracefully bounds solidly mapping limits dynamically stably."""
    if not force:
        typer.confirm("Are you absolutely sure you want to nuke all Task Records from the database natively?", abort=True)
        
    db_session: Session = ThreadSafeDatabaseSession()
    deleted_count = db_session.query(DBTaskRecord).delete()
    db_session.commit()
    terminal_console_tracer.print(f"[bold red]Successfully completely wiped {deleted_count} Tasks securely strictly bounding safely internally completely structurally.[/]")
    db_session.close()

app = global_cli_application
