"""Main CLI entry point using Typer."""

import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

app = typer.Typer(help="AWS Solution Architecture Recommendation Agent CLI")
console = Console()


@app.command()
def chat(
    session_id: Optional[str] = typer.Option(None, "--session-id", "-s", help="Session ID to resume conversation"),
    llm_provider: str = typer.Option("openai", "--llm", help="LLM provider (openai or anthropic)"),
):
    """Start interactive chat session with the agent."""
    from .chat import ChatSession

    console.print(Panel.fit(
        "[bold cyan]AWS Solution Architecture Recommendation Agent[/bold cyan]\n"
        "智能云解决方案推荐智能体",
        border_style="cyan"
    ))

    session = ChatSession(session_id=session_id, llm_provider=llm_provider)
    session.start()


@app.command()
def version():
    """Show version information."""
    console.print("[bold]AWS Solution Architecture Recommendation Agent[/bold]")
    console.print("Version: 0.1.0")


if __name__ == "__main__":
    app()

