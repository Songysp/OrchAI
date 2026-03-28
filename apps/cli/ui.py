from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner

console = Console()

def display_banner():
    banner_text = Text("OrchAI", style="bold magenta")
    banner_text.append(" HiveMind", style="bold cyan")
    console.print(Panel(banner_text, subtitle="CLI-First AI Orchestrator", border_style="bright_blue"))

def display_status(agent: str, status: str):
    console.print(f"[bold yellow]▶ {agent}:[/bold yellow] [italic white]{status}...[/italic white]")

def display_result(role: str, content: str):
    table = Table(show_header=True, header_style="bold green", box=None)
    table.add_column(role.upper(), style="white")
    table.add_row(content)
    console.print(table)
    console.print("---" * 10)

def display_config(config: dict):
    table = Table(title="OrchAI Current Configuration", border_style="dim")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    for k, v in config.items():
        table.add_row(k, str(v))
    console.print(table)
