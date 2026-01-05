#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
演示脚本：模拟一次对话交互
Demo script: Simulate a conversation interaction
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.cli.chat import ChatSession
from rich.console import Console

async def demo_conversation():
    """演示对话交互"""
    console = Console()
    
    console.print("\n[bold cyan]=== AWS Solution Architecture Recommendation Agent Demo ===[/bold cyan]")
    console.print("[dim]使用 Groq LLM 进行演示[/dim]\n")
    
    # 创建会话
    session = ChatSession(session_id=None, llm_provider="groq")
    
    # 模拟创建会话
    from src.models.conversation import Conversation
    from src.repositories.conversation_repository import ConversationRepository
    
    conversation_repo = ConversationRepository()
    conversation = Conversation()
    await conversation_repo.create(conversation)
    session.session_id = conversation.session_id
    
    console.print(f"[green]新会话已创建: {session.session_id}[/green]\n")
    
    # 演示消息
    demo_messages = [
        "我需要一个Web应用架构，支持高并发访问",
    ]
    
    for user_message in demo_messages:
        console.print(f"[bold cyan]You:[/bold cyan] {user_message}\n")
        console.print("[dim]Processing...[/dim]")
        
        try:
            # 处理消息
            response = await session._process_message(conversation, user_message)
            
            # 显示响应
            session._display_response(response)
            console.print()  # 空行
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            break
    
    console.print("[yellow]演示完成！[/yellow]")
    console.print("\n[dim]提示：要体验完整交互，请在终端运行: python start.py --llm groq[/dim]\n")

if __name__ == "__main__":
    asyncio.run(demo_conversation())

