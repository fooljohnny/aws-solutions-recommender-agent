"""Requirement extraction service with LLM-based natural language understanding."""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from anthropic import Anthropic
from ..aws_knowledge.catalog import AWSServiceCatalog
from ...models.user_requirement import UserRequirement, RequirementType


class RequirementExtractor:
    """Extracts user requirements from natural language using LLM."""

    def __init__(
        self,
        llm_provider: str = "openai",
        catalog: Optional[AWSServiceCatalog] = None,
    ):
        """Initialize requirement extractor.

        Args:
            llm_provider: LLM provider ('openai' or 'anthropic')
            catalog: AWS service catalog for context
        """
        self.llm_provider = llm_provider
        self.catalog = catalog or AWSServiceCatalog()

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

    async def extract_requirements(
        self,
        user_message: str,
        conversation_context: Optional[List[Dict[str, Any]]] = None,
        previous_requirements: Optional[List[UserRequirement]] = None,
    ) -> List[UserRequirement]:
        """Extract requirements from user message with context awareness.

        Args:
            user_message: User's natural language message
            conversation_context: Previous conversation messages for context
            previous_requirements: Previously extracted requirements for integration

        Returns:
            List of extracted requirements (merged with previous if provided)
        """
        # Build prompt for requirement extraction
        prompt = self._build_extraction_prompt(user_message, conversation_context)

        # Call LLM for requirement extraction
        extracted_data = await self._call_llm_for_extraction(prompt)

        # Convert to UserRequirement models
        requirements = []
        for req_data in extracted_data.get("requirements", []):
            requirement = UserRequirement(
                session_id=req_data.get("session_id", ""),  # Will be set by caller
                requirement_type=RequirementType(req_data["requirement_type"]),
                requirement_value=req_data["requirement_value"],
                confidence=req_data.get("confidence", 0.8),
            )
            requirements.append(requirement)

        # Merge with previous requirements if provided
        if previous_requirements:
            # Avoid duplicates based on requirement_value
            existing_values = {req.requirement_value for req in previous_requirements}
            for req in requirements:
                if req.requirement_value not in existing_values:
                    previous_requirements.append(req)
            return previous_requirements

        return requirements

    def _build_extraction_prompt(
        self,
        user_message: str,
        conversation_context: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Build prompt for requirement extraction.

        Args:
            user_message: User's message
            conversation_context: Previous conversation context

        Returns:
            Formatted prompt
        """
        context_text = ""
        if conversation_context:
            context_text = "\nPrevious conversation:\n"
            for msg in conversation_context[-5:]:  # Last 5 messages
                context_text += f"{msg.get('role', 'user')}: {msg.get('content', '')}\n"

        prompt = f"""你是一个AWS架构专家。请从用户的消息中提取需求信息。

{context_text}

用户消息: {user_message}

请提取以下类型的需求：
1. application_type: 应用类型（如：web应用、移动应用、数据分析等）
2. scale: 规模要求（如：用户数量、数据量、请求量等）
3. constraint: 约束条件（如：高可用性、安全性、成本优化等）
4. preference: 用户偏好（如：特定区域、特定服务等）

请以JSON格式返回提取的需求，格式如下：
{{
  "requirements": [
    {{
      "requirement_type": "application_type",
      "requirement_value": "web应用",
      "confidence": 0.9
    }},
    {{
      "requirement_type": "scale",
      "requirement_value": "1000用户",
      "confidence": 0.85
    }}
  ]
}}
"""
        return prompt

    async def _call_llm_for_extraction(self, prompt: str) -> Dict[str, Any]:
        """Call LLM for requirement extraction.

        Args:
            prompt: Extraction prompt

        Returns:
            Extracted requirements as dictionary
        """
        if self.llm_provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个AWS架构需求提取专家。只返回JSON格式的结果。"},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            import json
            return json.loads(response.choices[0].message.content)
        elif self.llm_provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt},
                ],
            )
            import json
            # Extract JSON from response
            content = response.content[0].text
            # Try to extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

