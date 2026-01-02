"""Multi-intent classification service with LLM function calling for structured intent extraction."""

import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from anthropic import Anthropic
from ...models.intent import Intent, IntentType, IntentStatus


class MultiIntentClassifier:
    """Classifies multiple intents from a single user message using LLM function calling."""

    def __init__(self, llm_provider: str = "openai"):
        """Initialize intent classifier.

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

    async def classify_intents(
        self,
        user_message: str,
        message_id: str,
        conversation_context: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Intent]:
        """Classify multiple intents from user message.

        Args:
            user_message: User's message text
            message_id: Message identifier
            conversation_context: Previous conversation context

        Returns:
            List of recognized intents
        """
        # Build classification prompt
        prompt = self._build_classification_prompt(user_message, conversation_context)

        # Get intent classifications from LLM
        intent_data = await self._call_llm_for_classification(prompt)

        # Convert to Intent models
        intents = []
        for intent_info in intent_data.get("intents", []):
            intent_type = IntentType(intent_info["intent_type"])
            priority = self._get_priority_for_intent_type(intent_type)

            intent = Intent(
                message_id=message_id,
                intent_type=intent_type,
                priority=priority,
                confidence=float(intent_info.get("confidence", 0.8)),
                extracted_entities=intent_info.get("extracted_entities", {}),
                status=IntentStatus.PENDING,
            )
            intents.append(intent)

        # Sort by priority (lower number = higher priority)
        intents.sort(key=lambda x: x.priority)

        return intents

    def _build_classification_prompt(
        self,
        user_message: str,
        conversation_context: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Build prompt for intent classification.

        Args:
            user_message: User's message
            conversation_context: Conversation context

        Returns:
            Classification prompt
        """
        context_text = ""
        if conversation_context:
            context_text = "\n之前的对话：\n"
            for msg in conversation_context[-5:]:
                role = "用户" if msg.get("role") == "user" else "助手"
                context_text += f"{role}: {msg.get('content', '')}\n"

        prompt = f"""你是一个意图识别专家。请从用户消息中识别所有意图。

{context_text}

用户消息: {user_message}

请识别以下类型的意图：
1. architecture_request: 架构请求（请求推荐架构、修改架构等）
2. pricing_query: 价格查询（询问成本、价格等）
3. clarification: 澄清请求（需要更多信息、提问等）
4. modification: 修改请求（修改现有架构、调整配置等）

一个消息可能包含多个意图。请识别所有意图并按优先级排序（architecture_request > pricing_query > clarification）。

请以JSON格式返回，格式如下：
{{
  "intents": [
    {{
      "intent_type": "architecture_request",
      "confidence": 0.9,
      "extracted_entities": {{
        "services": ["EC2", "RDS"],
        "requirements": ["web应用", "1000用户"]
      }}
    }},
    {{
      "intent_type": "pricing_query",
      "confidence": 0.85,
      "extracted_entities": {{
        "query": "成本"
      }}
    }}
  ]
}}
"""
        return prompt

    async def _call_llm_for_classification(self, prompt: str) -> Dict[str, Any]:
        """Call LLM for intent classification.

        Args:
            prompt: Classification prompt

        Returns:
            Intent classification results
        """
        if self.llm_provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个意图识别专家。只返回JSON格式的结果。"},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            return json.loads(response.choices[0].message.content)
        elif self.llm_provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            content = response.content[0].text
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    def _get_priority_for_intent_type(self, intent_type: IntentType) -> int:
        """Get priority for intent type.

        Args:
            intent_type: Intent type

        Returns:
            Priority number (lower = higher priority)
        """
        priority_map = {
            IntentType.ARCHITECTURE_REQUEST: 1,
            IntentType.MODIFICATION: 1,
            IntentType.PRICING_QUERY: 2,
            IntentType.CLARIFICATION: 3,
        }
        return priority_map.get(intent_type, 3)

