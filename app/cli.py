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
from app.database import ThreadSafeDatabaseSession
from app.models import DBTaskRecord, SubagentAuditOutput
from app.orchestrator.registry import load_agent_contract_by_domain
from app.orchestrator.qwen_subprocess import spawn_and_execute_LLM_subprocess_for_audit

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
def display_cli_tasks_table_memory():
    """Prints SQLite memory projection structured bounds natively mapped CLI Rich tables format reliably parsing explicitly strictly safely cleanly."""
    in_process_db_session: Session = ThreadSafeDatabaseSession()
    database_records_scanned_array = in_process_db_session.query(DBTaskRecord).all()
    
    rendered_rich_terminal_table = Table(title="Health Coordinator Active Track Task Log")
    rendered_rich_terminal_table.add_column("ID Bounds", style="cyan")
    rendered_rich_terminal_table.add_column("Domain Scope")
    rendered_rich_terminal_table.add_column("Title Detail Block")
    rendered_rich_terminal_table.add_column("Priority Strict")
    rendered_rich_terminal_table.add_column("Human Approval Tracking Gate", style="yellow")
    
    for single_record_payload_entry in database_records_scanned_array:
        rendered_rich_terminal_table.add_row(
            single_record_payload_entry.id,
            single_record_payload_entry.domain,
            single_record_payload_entry.title[:50] + "..." if len(single_record_payload_entry.title) > 50 else single_record_payload_entry.title,
            single_record_payload_entry.priority,
            single_record_payload_entry.approvalState
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
    
    if not domain:
        terminal_console_tracer.print("[red]Full generic Swarm spawn not yet integrated strictly for CLI. Please target bindings safely via --domain.[/]")
        raise typer.Exit(code=1)

    try:
        loaded_agent_contract = load_agent_contract_by_domain(domain)
    except Exception as registry_error:
        terminal_console_tracer.print(f"[bold red]Failed mapping registry definitions natively:[/] {str(registry_error)}")
        raise typer.Exit(code=1)
        
    terminal_console_tracer.print(f"[bold blue]Summoning specific `{domain}` auditor ({loaded_agent_contract.get('name')}){path_msg}...[/]")
    
    try:
        # Use rich status spinners to provide visual feedback while asyncio blocks natively gracefully!
        with terminal_console_tracer.status(f"[bold cyan]Subagent '{loaded_agent_contract.get('name')}' is actively auditing... This may take up to {settings.subagent_execution_timeout_sek}s.[/]"):
            completed_json_payload = asyncio.run(spawn_and_execute_LLM_subprocess_for_audit(
                domain_identifier=domain,
                audit_rules_array=loaded_agent_contract.get("auditRules", []),
                target_output_schema_path=loaded_agent_contract.get("outputSchema", ""),
                workspace_path=workspace
            ))
        
        # Enforce Zero-Tolerance Strict Schema Validation bounds locally in the CLI natively!
        validated_pydantic_model = SubagentAuditOutput(**completed_json_payload)
        
        terminal_console_tracer.print("\n[bold green]Audit Phase LLM Execution Completed Successfully. Extracted Findings Payload:[/]\n")
        terminal_console_tracer.print(JSON.from_data(validated_pydantic_model.model_dump()))
        
    except Exception as llm_execution_error:
        terminal_console_tracer.print(f"\n[bold red]Orchestrator Pipeline Crash cleanly structurally mapped bounds:[/] {str(llm_execution_error)}")
        raise typer.Exit(code=1)

app = global_cli_application
