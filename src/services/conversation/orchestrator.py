"""Conversation orchestration service with LangGraph graph execution."""

import os
from typing import List, Dict, Any, Optional
from uuid import UUID
from langgraph.graph import StateGraph, END

from ...agents.state.agent_state import AgentState
from ...services.recommendation.requirement_extractor import RequirementExtractor
from ...services.recommendation.recommender import ArchitectureRecommender
from ...services.diagram.generator import DiagramGenerator
from ...services.diagram.storage import DiagramStorage
from ...services.intent.classifier import MultiIntentClassifier
from ...services.intent.processor import IntentProcessor
from ...services.intent.aggregator import IntentResultAggregator
from ...services.conversation.formatter import MultiIntentResponseFormatter
from ...services.conversation.context_retriever import ContextRetriever
from ...services.conversation.context_updater import ContextUpdater
from ...services.conversation.history_manager import HistoryManager
from ...repositories.conversation_repository import ConversationRepository
from ...repositories.message_repository import MessageRepository


class ConversationOrchestrator:
    """Orchestrates conversation flow using LangGraph."""

    def __init__(
        self,
        llm_provider: str = "openai",
    ):
        """Initialize orchestrator.

        Args:
            llm_provider: LLM provider name
        """
        self.llm_provider = llm_provider
        self.requirement_extractor = RequirementExtractor(llm_provider=llm_provider)
        self.recommender = ArchitectureRecommender(llm_provider=llm_provider)
        self.diagram_generator = DiagramGenerator()
        self.diagram_storage = DiagramStorage()
        self.intent_classifier = MultiIntentClassifier(llm_provider=llm_provider)
        self.intent_processor = IntentProcessor()
        self.intent_aggregator = IntentResultAggregator()
        self.response_formatter = MultiIntentResponseFormatter()
        self.context_retriever = ContextRetriever()
        self.context_updater = ContextUpdater()
        self.history_manager = HistoryManager()
        self.conversation_repo = ConversationRepository()
        self.message_repo = MessageRepository()

        # Build LangGraph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph conversation graph.

        Returns:
            LangGraph StateGraph
        """
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("classify_intents", self._classify_intents_node)
        workflow.add_node("extract_requirements", self._extract_requirements_node)
        workflow.add_node("generate_recommendation", self._generate_recommendation_node)
        workflow.add_node("generate_diagram", self._generate_diagram_node)
        workflow.add_node("format_response", self._format_response_node)

        # Define edges
        workflow.set_entry_point("classify_intents")
        workflow.add_edge("classify_intents", "extract_requirements")
        workflow.add_edge("extract_requirements", "generate_recommendation")
        workflow.add_edge("generate_recommendation", "generate_diagram")
        workflow.add_edge("generate_diagram", "format_response")
        workflow.add_edge("format_response", END)

        return workflow.compile()

    async def process_message(
        self,
        session_id: UUID,
        user_message: str,
        conversation_context: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Process user message through conversation graph.

        Args:
            session_id: Conversation session ID
            user_message: User's message
            conversation_context: Previous conversation context

        Returns:
            Response data with content and metadata
        """
        # Retrieve existing context
        existing_context = await self.context_retriever.retrieve_context(session_id)

        # Get conversation history if not provided
        if not conversation_context:
            conversation_context = await self.history_manager.get_context_messages(session_id)

        # Initialize agent state with context
        initial_state = AgentState(
            session_id=session_id,
            current_message=user_message,
            conversation_history=conversation_context,
        )

        # Load previous requirements if available
        if existing_context and existing_context.extracted_requirements:
            initial_state.extracted_requirements = existing_context.extracted_requirements

        # Run graph
        final_state = await self.graph.ainvoke(initial_state)

        # Build response
        response_content = final_state.get("response_content", "")
        recommendation = final_state.get("current_recommendation")

        metadata = {}
        if recommendation:
            metadata["recommendation_id"] = str(recommendation.recommendation_id)
            if recommendation.diagram_url:
                metadata["diagram_url"] = recommendation.diagram_url

        return {
            "content": response_content,
            "metadata": metadata,
        }

    async def _classify_intents_node(self, state: AgentState) -> AgentState:
        """Classify intents from user message.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        # Create temporary message for intent classification
        from uuid import uuid4
        temp_message_id = str(uuid4())

        intents = await self.intent_classifier.classify_intents(
            state.current_message or "",
            temp_message_id,
            state.conversation_history,
        )
        state.recognized_intents = intents
        return state

    async def _extract_requirements_node(self, state: AgentState) -> AgentState:
        """Extract requirements from user message with context awareness.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        # Extract requirements, merging with previous if available
        requirements = await self.requirement_extractor.extract_requirements(
            state.current_message or "",
            state.conversation_history,
            previous_requirements=state.extracted_requirements,
        )
        state.extracted_requirements = requirements

        # Update context with new requirements
        await self.context_updater.update_context(
            state.session_id,
            new_requirements=requirements,
        )

        return state

    async def _generate_recommendation_node(self, state: AgentState) -> AgentState:
        """Generate architecture recommendation.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        recommendation = await self.recommender.recommend_architecture(
            state.extracted_requirements,
            state.session_id,
            state.conversation_history,
        )
        state.current_recommendation = recommendation
        return state

    async def _generate_diagram_node(self, state: AgentState) -> AgentState:
        """Generate diagram for recommendation.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        if not state.current_recommendation:
            return state

        # Generate Mermaid diagram
        mermaid_source = self.diagram_generator.generate_mermaid(
            state.current_recommendation,
            diagram_type="flowchart",
        )
        state.current_recommendation.diagram_data = mermaid_source

        # Save diagram and get URL
        diagram_url = self.diagram_storage.save_diagram(
            state.current_recommendation,
            format="svg",
        )
        state.current_recommendation.diagram_url = diagram_url

        return state

    async def _format_response_node(self, state: AgentState) -> AgentState:
        """Format final response with multi-intent support.

        Args:
            state: Current agent state

        Returns:
            Updated agent state
        """
        # Process intents if available
        intent_results = {}
        if state.recognized_intents:
            from ...services.intent.orchestrator import IntentOrchestrator
            intent_orchestrator = IntentOrchestrator()
            intent_results = await intent_orchestrator.process_intents(
                state.recognized_intents,
                state.session_id,
                {"recommendation": state.current_recommendation},
            )

        # Update context with recommendation and intents
        await self.context_updater.update_context(
            state.session_id,
            new_intents=state.recognized_intents,
            current_recommendation=state.current_recommendation,
        )

        # Format response using multi-intent formatter
        if state.recognized_intents and intent_results:
            state.response_content = self.response_formatter.format_response(
                state.recognized_intents,
                intent_results,
                state.current_recommendation,
            )
        elif state.current_recommendation:
            # Fallback to single-intent formatting
            response_parts = [
                "根据您的需求，我为您推荐以下AWS架构方案：\n",
                "**推荐的服务：**\n",
            ]
            for service in state.current_recommendation.services:
                response_parts.append(f"- **{service.aws_service_name}**: {service.role}\n")
            response_parts.append(f"\n**架构说明：**\n{state.current_recommendation.explanation}\n")
            if state.current_recommendation.diagram_url:
                response_parts.append(f"\n**架构图：**\n架构图已生成，可通过以下链接查看：{state.current_recommendation.diagram_url}\n")
            state.response_content = "".join(response_parts)
        else:
            state.response_content = "抱歉，我无法生成架构推荐。请提供更多详细信息。"

        state.processing_complete = True
        return state

