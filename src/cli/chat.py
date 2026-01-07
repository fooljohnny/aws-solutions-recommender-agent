"""Interactive chat session for CLI."""

import sys
import asyncio
import json
import shlex
from typing import Optional
from uuid import UUID
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.syntax import Syntax

from ..services.conversation.orchestrator import ConversationOrchestrator
from ..repositories.conversation_repository import ConversationRepository
from ..repositories.message_repository import MessageRepository
from ..models.conversation import Conversation
from ..models.message import Message, MessageRole
from ..skills.base import SkillContext
from ..skills.defaults import create_default_registry
from ..skills.registry import SkillRegistry


class ChatSession:
    """Interactive chat session handler."""

    def __init__(
        self,
        session_id: str | UUID | None = None,
        llm_provider: str = "openai",
        skills_registry: SkillRegistry | None = None,
    ):
        """Initialize chat session.

        Args:
            session_id: Optional session ID to resume conversation
            llm_provider: LLM provider name
            skills_registry: Optional skills registry for slash-commands/tooling
        """
        self.console = Console()
        self.llm_provider = llm_provider
        if isinstance(session_id, UUID):
            self.session_id = session_id
        else:
            self.session_id = UUID(str(session_id)) if session_id else None
        self.orchestrator = ConversationOrchestrator(llm_provider=llm_provider)
        self.conversation_repo = ConversationRepository()
        self.message_repo = MessageRepository()
        self.skills = skills_registry or create_default_registry()

    def start(self):
        """Start interactive chat session."""
        # Load or create conversation
        if self.session_id:
            self.console.print(f"[dim]Resuming session: {self.session_id}[/dim]")
            conversation = asyncio.run(self.conversation_repo.get_by_session_id(self.session_id))
            if not conversation:
                self.console.print(f"[red]Session {self.session_id} not found. Creating new session.[/red]")
                conversation = None
        else:
            conversation = None

        if not conversation:
            conversation = Conversation()
            asyncio.run(self.conversation_repo.create(conversation))
            self.session_id = conversation.session_id
            self.console.print(f"[green]New session created: {self.session_id}[/green]")

        self.console.print("\n[bold]Enter your requirements in Chinese. Type 'exit' or 'quit' to end.[/bold]\n")

        # Check if running in interactive mode
        is_interactive = sys.stdin.isatty()

        # Main chat loop
        while True:
            try:
                # Get user input
                try:
                    if is_interactive:
                        user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
                    else:
                        # Fallback to standard input for non-interactive environments
                        self.console.print("[bold cyan]You[/bold cyan]: ", end="")
                        user_input = input()
                except (EOFError, KeyboardInterrupt):
                    # Handle EOF gracefully
                    self.console.print("\n[yellow]Goodbye![/yellow]")
                    break

                if user_input.lower() in ["exit", "quit", "退出"]:
                    self.console.print("[yellow]Goodbye![/yellow]")
                    break

                if not user_input.strip():
                    continue

                # Slash commands (do not hit the LLM pipeline)
                if user_input.strip().startswith("/"):
                    if self._handle_slash_command(conversation, user_input.strip()):
                        continue

                # Process message
                self.console.print("[dim]Processing...[/dim]")
                response = asyncio.run(self._process_message(conversation, user_input))

                # Display response
                self._display_response(response)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
            except EOFError:
                # Handle EOF in the outer loop as well
                self.console.print("\n[yellow]Input stream closed. Goodbye![/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")

    async def _process_message(
        self,
        conversation: Conversation,
        user_message: str,
    ) -> str:
        """Process user message and get response.

        Args:
            conversation: Current conversation
            user_message: User's message

        Returns:
            Agent response
        """
        # Create user message
        user_msg = Message(
            session_id=conversation.session_id,
            role=MessageRole.USER,
            content=user_message,
        )
        await self.message_repo.create(user_msg)

        # Convert Message objects to dict format for orchestrator
        conversation_context = [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat() if hasattr(msg.timestamp, "isoformat") else str(msg.timestamp),
            }
            for msg in conversation.conversation_history
        ]

        # Process through orchestrator
        response_data = await self.orchestrator.process_message(
            session_id=conversation.session_id,
            user_message=user_message,
            conversation_context=conversation_context,
        )

        # Create assistant message
        assistant_msg = Message(
            session_id=conversation.session_id,
            role=MessageRole.ASSISTANT,
            content=response_data.get("content", ""),
            metadata=response_data.get("metadata", {}),
        )
        await self.message_repo.create(assistant_msg)

        # Update conversation
        conversation.conversation_history.append(user_msg)
        conversation.conversation_history.append(assistant_msg)
        conversation.last_accessed_at = user_msg.timestamp
        await self.conversation_repo.update(conversation)

        return response_data.get("content", "")

    def _handle_slash_command(self, conversation: Conversation, raw: str) -> bool:
        """Handle CLI slash-commands. Returns True if handled."""
        cmdline = raw.strip()
        if cmdline in ["/help", "/?"]:
            self.console.print(
                Panel(
                    "\n".join(
                        [
                            "**Slash commands**",
                            "- `/skills`: list available skills",
                            "- `/skill <name> <json_args>`: execute a skill (json args optional)",
                            "  - Example: `/skill ping {\"message\": \"hello\"}`",
                        ]
                    ),
                    title="[bold cyan]Help[/bold cyan]",
                    border_style="cyan",
                )
            )
            return True

        if cmdline == "/skills":
            skills = list(self.skills.list())
            if not skills:
                self.console.print("[yellow]No skills registered.[/yellow]")
                return True
            lines = ["**Available skills:**"]
            for s in skills:
                lines.append(f"- **{s.name}**: {s.description}")
            self.console.print(
                Panel(Markdown("\n".join(lines)), title="[bold cyan]Skills[/bold cyan]", border_style="cyan")
            )
            return True

        if cmdline.startswith("/skill"):
            try:
                parts = shlex.split(cmdline)
            except ValueError as e:
                self.console.print(f"[red]Invalid command: {e}[/red]")
                return True

            if len(parts) < 2:
                self.console.print("[yellow]Usage: /skill <name> <json_args>[/yellow]")
                return True

            name = parts[1]
            args_str = " ".join(parts[2:]).strip() if len(parts) > 2 else ""

            # Accept either no args, or a JSON object string.
            args = {}
            if args_str:
                try:
                    args = json.loads(args_str)
                except json.JSONDecodeError as e:
                    self.console.print(f"[red]Invalid JSON args: {e}[/red]")
                    return True
                if not isinstance(args, dict):
                    self.console.print("[red]JSON args must be an object (e.g. {\"k\": \"v\"}).[/red]")
                    return True

            ctx = SkillContext(session_id=conversation.session_id, llm_provider=self.llm_provider)
            result = asyncio.run(self.skills.dispatch(name=name, args=args, context=ctx))

            if result.ok:
                self.console.print(
                    Panel(
                        Syntax(json.dumps(result.data, ensure_ascii=False, indent=2), "json"),
                        title=f"[bold green]Skill OK[/bold green] {name}",
                        border_style="green",
                    )
                )
            else:
                self.console.print(
                    Panel(
                        result.error or "Unknown error",
                        title=f"[bold red]Skill Error[/bold red] {name}",
                        border_style="red",
                    )
                )
            return True

        return False

    def _display_response(self, response: str):
        """Display agent response.

        Args:
            response: Response text
        """
        # Try to parse as markdown
        try:
            self.console.print(Panel(
                Markdown(response),
                title="[bold green]Agent[/bold green]",
                border_style="green",
            ))
        except Exception:
            # Fallback to plain text
            self.console.print(Panel(
                response,
                title="[bold green]Agent[/bold green]",
                border_style="green",
            ))

