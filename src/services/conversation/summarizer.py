"""Conversation summarization with LLM-based summarization for long conversations."""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from anthropic import Anthropic


class ConversationSummarizer:
    """Summarizes long conversations using LLM."""

    def __init__(self, llm_provider: str = "openai"):
        """Initialize conversation summarizer.

        Args:
            llm_provider: LLM provider ('openai' or 'anthropic')
        """
        self.llm_provider = llm_provider

        if llm_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-4"
        elif llm_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = Anthropic(api_key=api_key)
            self.model = "claude-3-opus-20240229"
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")

    async def summarize(
        self,
        messages: List[Dict[str, Any]],
        max_length: int = 500,
    ) -> str:
        """Summarize conversation messages.

        Args:
            messages: List of conversation messages
            max_length: Maximum summary length in characters

        Returns:
            Conversation summary
        """
        if not messages:
            return ""

        # Build conversation text
        conversation_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in messages[-20:]  # Last 20 messages
        ])

        prompt = f"""请总结以下对话的关键信息，包括：
1. 用户的主要需求
2. 推荐的架构方案
3. 讨论的关键点

对话内容：
{conversation_text}

请用中文总结，控制在{max_length}字符以内。"""

        if self.llm_provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个对话总结专家。请简洁准确地总结对话内容。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=200,
            )
            summary = response.choices[0].message.content
        elif self.llm_provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            summary = response.content[0].text

        # Truncate if needed
        if len(summary) > max_length:
            summary = summary[:max_length - 3] + "..."

        return summary

    async def summarize_incremental(
        self,
        previous_summary: Optional[str],
        new_messages: List[Dict[str, Any]],
        max_length: int = 500,
    ) -> str:
        """Create incremental summary by updating previous summary with new messages.

        Args:
            previous_summary: Previous conversation summary
            new_messages: New messages since last summary
            max_length: Maximum summary length

        Returns:
            Updated summary
        """
        if not new_messages:
            return previous_summary or ""

        new_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in new_messages
        ])

        prompt = f"""基于之前的对话总结，更新总结以包含新的对话内容。

之前的总结：
{previous_summary or "无"}

新的对话内容：
{new_text}

请更新总结，控制在{max_length}字符以内。"""

        if self.llm_provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个对话总结专家。请更新对话总结。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=200,
            )
            summary = response.choices[0].message.content
        elif self.llm_provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            summary = response.content[0].text

        if len(summary) > max_length:
            summary = summary[:max_length - 3] + "..."

        return summary

