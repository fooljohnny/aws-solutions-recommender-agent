"""Interactive chat session for CLI."""

import asyncio
from typing import Optional
from uuid import UUID
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.syntax import Syntax

from typing import Optional
from uuid import UUID
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown

from ..services.conversation.orchestrator import ConversationOrchestrator
from ..repositories.conversation_repository import ConversationRepository
from ..repositories.message_repository import MessageRepository
from ..models.conversation import Conversation
from ..models.message import Message, MessageRole


class ChatSession:
    """Interactive chat session handler."""

    def __init__(
        self,
        session_id: Optional[str] = None,
        llm_provider: str = "openai",
    ):
        """Initialize chat session.

        Args:
            session_id: Optional session ID to resume conversation
            llm_provider: LLM provider name
        """
        self.console = Console()
        self.llm_provider = llm_provider
        self.session_id = UUID(session_id) if session_id else None
        self.orchestrator = ConversationOrchestrator(llm_provider=llm_provider)
        self.conversation_repo = ConversationRepository()
        self.message_repo = MessageRepository()

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

        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
                if user_input.lower() in ["exit", "quit", "退出"]:
                    self.console.print("[yellow]Goodbye![/yellow]")
                    break

                if not user_input.strip():
                    continue

                # Process message
                self.console.print("[dim]Processing...[/dim]")
                response = asyncio.run(self._process_message(conversation, user_input))

                # Display response
                self._display_response(response)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
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
        asyncio.run(self.message_repo.create(user_msg))

        # Process through orchestrator
        response_data = await self.orchestrator.process_message(
            session_id=conversation.session_id,
            user_message=user_message,
            conversation_context=conversation.conversation_history,
        )

        # Create assistant message
        assistant_msg = Message(
            session_id=conversation.session_id,
            role=MessageRole.ASSISTANT,
            content=response_data.get("content", ""),
            metadata=response_data.get("metadata", {}),
        )
        asyncio.run(self.message_repo.create(assistant_msg))

        # Update conversation
        conversation.conversation_history.append(user_msg)
        conversation.conversation_history.append(assistant_msg)
        conversation.last_accessed_at = user_msg.timestamp
        asyncio.run(self.conversation_repo.update(conversation))

        return response_data.get("content", "")

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

