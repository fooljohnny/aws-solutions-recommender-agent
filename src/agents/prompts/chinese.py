"""Chinese language prompt templates with optimized prompts for requirement extraction and recommendation."""

from typing import List, Dict, Any, Optional


class ChinesePrompts:
    """Chinese language prompt templates."""

    @staticmethod
    def requirement_extraction_system_prompt() -> str:
        """System prompt for requirement extraction.

        Returns:
            System prompt text
        """
        return """你是一个AWS架构需求提取专家。你的任务是从用户的中文自然语言描述中提取结构化需求信息。

你需要识别以下类型的需求：
1. application_type: 应用类型（如：Web应用、移动应用、数据分析平台等）
2. scale: 规模要求（如：1000用户、1TB数据、10000请求/秒等）
3. constraint: 约束条件（如：高可用性、安全性、成本优化、低延迟等）
4. preference: 用户偏好（如：特定AWS区域、特定服务偏好等）

请准确提取用户需求，并以JSON格式返回。"""

    @staticmethod
    def requirement_extraction_user_prompt(
        user_message: str,
        conversation_context: Optional[List[Dict[str, Any]]] = None,
        previous_requirements: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """User prompt for requirement extraction with context awareness.

        Args:
            user_message: User's message
            conversation_context: Previous conversation context
            previous_requirements: Previously extracted requirements

        Returns:
            User prompt text
        """
        context_text = ""
        if conversation_context:
            context_text = "\n\n之前的对话：\n"
            for msg in conversation_context[-5:]:
                role = "用户" if msg.get("role") == "user" else "助手"
                context_text += f"{role}: {msg.get('content', '')}\n"

        previous_req_text = ""
        if previous_requirements:
            previous_req_text = "\n\n之前提取的需求：\n"
            for req in previous_requirements:
                if isinstance(req, dict):
                    previous_req_text += f"- {req.get('requirement_type', '')}: {req.get('requirement_value', '')}\n"
                else:
                    previous_req_text += f"- {req.requirement_type.value}: {req.requirement_value}\n"

        return f"""{context_text}{previous_req_text}

当前用户消息：{user_message}

请提取需求信息（可以更新之前的需求或添加新需求），返回JSON格式：
{{
  "requirements": [
    {{
      "requirement_type": "application_type",
      "requirement_value": "Web应用",
      "confidence": 0.9
    }}
  ]
}}"""

    @staticmethod
    def architecture_recommendation_system_prompt() -> str:
        """System prompt for architecture recommendation.

        Returns:
            System prompt text
        """
        return """你是一个AWS架构推荐专家。你的任务是根据用户需求推荐合适的AWS服务架构。

你需要：
1. 分析用户需求
2. 选择合适的AWS服务
3. 设计合理的架构
4. 提供配置建议
5. 解释推荐理由

请用中文回复，确保推荐符合AWS最佳实践和Well-Architected Framework。"""

    @staticmethod
    def architecture_recommendation_user_prompt(
        requirements: List[Dict[str, Any]],
        available_services: Optional[List[str]] = None,
        previous_recommendation: Optional[Dict[str, Any]] = None,
    ) -> str:
        """User prompt for architecture recommendation.

        Args:
            requirements: Extracted requirements
            available_services: List of available AWS services

        Returns:
            User prompt text
        """
        req_text = "\n".join([
            f"- {req.get('requirement_type', '')}: {req.get('requirement_value', '')}"
            for req in requirements
        ])

        services_text = ""
        if available_services:
            services_text = f"\n\n可用AWS服务：{', '.join(available_services[:20])}"

        previous_rec_text = ""
        if previous_recommendation:
            previous_rec_text = "\n\n之前的推荐架构：\n"
            if isinstance(previous_recommendation, dict):
                prev_services = previous_recommendation.get("services", [])
                for svc in prev_services:
                    if isinstance(svc, dict):
                        previous_rec_text += f"- {svc.get('aws_service_name', '')}: {svc.get('role', '')}\n"
                    else:
                        previous_rec_text += f"- {svc.aws_service_name}: {svc.role}\n"

        return f"""用户需求：
{req_text}{previous_rec_text}{services_text}

请推荐AWS架构，返回JSON格式：
{{
  "services": [
    {{
      "name": "EC2",
      "type": "compute",
      "role": "Web服务器",
      "region": "us-east-1",
      "configurations": [
        {{
          "type": "instance_type",
          "value": "t3.medium",
          "details": {{}}
        }}
      ]
    }}
  ],
  "explanation": "推荐使用EC2作为Web服务器，因为..."
}}"""

    @staticmethod
    def multi_intent_classification_prompt() -> str:
        """System prompt for multi-intent classification.

        Returns:
            System prompt text
        """
        return """你是一个多意图识别专家。用户的一条消息可能包含多个意图，你需要识别所有意图。

意图类型：
1. architecture_request: 架构请求（请求推荐架构、创建新架构）
2. modification: 修改请求（修改现有架构、调整配置）
3. pricing_query: 价格查询（询问成本、价格估算）
4. clarification: 澄清请求（需要更多信息、提问）

优先级：architecture_request/modification (1) > pricing_query (2) > clarification (3)

请识别消息中的所有意图，并按优先级排序。"""

    @staticmethod
    def response_formatting_prompt(
        recommendation: Dict[str, Any],
        diagram_url: Optional[str] = None,
    ) -> str:
        """Prompt for formatting final response.

        Args:
            recommendation: Architecture recommendation data
            diagram_url: Optional diagram URL

        Returns:
            Formatted response text
        """
        response = f"""根据您的需求，我为您推荐以下AWS架构方案：

**推荐的服务：**
"""
        for service in recommendation.get("services", []):
            response += f"- **{service.get('name', '')}**: {service.get('role', '')}\n"

        response += f"\n**架构说明：**\n{recommendation.get('explanation', '')}\n"

        if diagram_url:
            response += f"\n**架构图：**\n您可以通过以下链接查看架构图：{diagram_url}\n"

        return response

