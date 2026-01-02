<!--
Sync Impact Report:
Version change: 1.0.0 → 1.1.0 (added user interface guidance)
Modified principles: N/A
Added sections: User Interface Requirements (within Architecture Requirements)
Removed sections: N/A
Templates requiring updates:
  ✅ plan-template.md - Updated to clarify CLI-only interface option
  ⚠ tasks-template.md - No changes needed, already supports CLI path conventions
Follow-up TODOs: None
-->

# AWS Solution Architecture Agent Constitution

## Core Principles

### I. Natural Language First (NON-NEGOTIABLE)
All user interactions MUST be through natural language conversation. The system MUST accept free-form text input and respond in conversational, human-readable format. Technical jargon and structured commands are acceptable only when explicitly requested by the user. The agent MUST maintain conversational context across multiple turns without requiring users to restate information.

**Rationale**: The primary value proposition is enabling non-technical users to describe their needs in plain language and receive expert-level AWS architecture recommendations. Forcing structured input defeats this purpose.

### II. Multi-Intent Recognition (NON-NEGOTIABLE)
The system MUST support simultaneous recognition and handling of multiple user intents within a single conversation turn. Users may combine architecture requests, pricing queries, configuration changes, and clarification requests in one message. The agent MUST parse, prioritize, and address all identified intents appropriately.

**Rationale**: Real conversations are not single-intent. Users naturally mix questions, requests, and clarifications. Supporting this complexity is essential for natural interaction.

### III. Contextual Multi-Turn Dialogue
The agent MUST maintain conversation state, including: user requirements extracted from previous turns, recommended architecture components, pricing calculations, and user preferences. The system MUST support conversation resumption, clarification requests, and iterative refinement of recommendations without losing context.

**Rationale**: Architecture recommendations evolve through dialogue. Users refine requirements, ask follow-ups, and compare options. Context loss forces repetition and degrades user experience.

### IV. Architecture Diagram Generation
Every recommended AWS solution MUST include a visual architecture diagram. Diagrams MUST use AWS Architecture Icons and follow AWS Well-Architected Framework conventions. Diagrams MUST be machine-readable (e.g., Mermaid, PlantUML, or AWS-native formats) and human-viewable (rendered images). The system MUST generate diagrams automatically from the recommended architecture components.

**Rationale**: Visual representation is essential for understanding cloud architectures. Automated generation ensures consistency and accuracy while reducing manual effort.

### V. Configuration and Pricing Transparency
All architecture recommendations MUST include detailed configuration specifications and cost estimates. Pricing MUST be calculated using current AWS Pricing API data or validated pricing models. Cost breakdowns MUST be itemized by service and include usage assumptions. The system MUST support "what-if" scenarios for different configurations and usage patterns.

**Rationale**: Cost is a critical decision factor for cloud architecture. Transparent, accurate pricing enables informed decisions and builds trust.

### VI. AWS Service Knowledge Accuracy
The agent MUST maintain up-to-date knowledge of AWS services, their capabilities, limitations, and best practices. Service recommendations MUST align with AWS Well-Architected Framework pillars (Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability). The system MUST validate service compatibility and account for service dependencies.

**Rationale**: Incorrect or outdated AWS knowledge leads to poor recommendations, wasted costs, and security risks. Accuracy is non-negotiable for a trusted advisor system.

### VII. Testability and Observability
All conversation flows, intent recognition, and recommendation logic MUST be testable through automated tests. The system MUST log all user interactions, recognized intents, recommendation decisions, and pricing calculations for debugging and improvement. Logs MUST be structured and queryable. The system MUST expose metrics for conversation quality, recommendation accuracy, and user satisfaction.

**Rationale**: Complex AI systems require rigorous testing and monitoring. Without observability, failures are invisible and improvements are impossible.

### VIII. Incremental Delivery and MVP Focus
Features MUST be delivered incrementally, with each increment providing independent value. The first MVP MUST support basic architecture recommendation for a single, well-defined use case. Multi-intent recognition and advanced features can follow, but the core recommendation capability MUST work independently first.

**Rationale**: Complex systems built all-at-once fail. Incremental delivery enables early validation, user feedback, and risk mitigation.

## Architecture Requirements

### User Interface Requirements
The system MUST provide a command-line interface (CLI) for user interaction. No complex frontend or web-based user interface is required. The CLI MUST support natural language input and output, maintaining conversational context across multiple interactions. The system MAY expose REST API endpoints for programmatic access, but the primary user interface MUST be CLI-based.

**Rationale**: A CLI interface is sufficient for the core use case of conversational AWS architecture recommendations. This simplifies development, reduces complexity, and focuses effort on the core recommendation engine rather than UI development.

### Technology Stack
- **Primary Language**: Python 3.11+ (for AI/ML libraries and AWS SDK integration)
- **User Interface**: Command-line interface (CLI) using Python CLI frameworks (e.g., Click, Typer, or argparse)
- **LLM Framework**: Must support function calling/tool use for structured outputs (e.g., OpenAI GPT-4, Anthropic Claude, or open-source alternatives)
- **AWS Integration**: boto3 SDK for AWS service queries and pricing API access
- **Diagram Generation**: Support for Mermaid, PlantUML, or AWS Architecture Icons rendering
- **Conversation State**: Persistent storage for conversation history (e.g., DynamoDB, PostgreSQL, or Redis)
- **API Framework**: FastAPI or similar for REST API endpoints (optional, for programmatic access)
- **Testing**: pytest for unit/integration tests, contract testing for API endpoints

### Data Requirements
- AWS service catalog with capabilities, limitations, and relationships
- AWS pricing data (via Pricing API or cached datasets)
- Architecture pattern templates and best practices
- Conversation history and user preferences (with privacy compliance)

### Performance Standards
- Intent recognition latency: < 2 seconds for single-turn, < 5 seconds for multi-intent
- Architecture diagram generation: < 10 seconds for standard diagrams
- Pricing calculation: < 3 seconds for typical configurations
- Conversation context retrieval: < 500ms
- System MUST handle concurrent conversations (target: 100+ simultaneous users)

### Security and Compliance
- User conversation data MUST be encrypted at rest and in transit
- AWS credentials MUST never be stored in code or logs
- The system MUST comply with data privacy regulations (GDPR, CCPA) for conversation logs
- All AWS API calls MUST use IAM roles with least-privilege permissions
- The system MUST validate and sanitize all user inputs to prevent injection attacks

## Development Workflow
### Code Review Requirements
* **State Machine Integrity**: All PRs modifying the **LangGraph** structure MUST include a visualization of the updated graph. Changes must be audited for state-transition leaks or potential infinite loops within the `AgentState`.
* **MCP Tooling Standards**: Any new **Model Context Protocol (MCP)** server or tool must provide a structured JSON schema for inputs/outputs and include mock responses for testing.
* **Architecture Alignment**: Proposed architecture patterns in the code must be cross-referenced with official **AWS Well-Architected** documentation. Links to relevant AWS whitepapers should be included in PR descriptions.
* **Prompt Engineering Audit**: Changes to system prompts or few-shot examples require a "diff" analysis of model outputs to ensure no regression in intent recognition or AWS service accuracy.

### Code Review Requirements
- All PRs MUST include tests for new conversation flows or intent recognition logic
- Architecture recommendations MUST be validated against AWS documentation
- Pricing calculations MUST be verified with test cases using known AWS pricing
- Diagram generation MUST be tested for correctness and visual quality

### Testing Gates
- Unit tests MUST cover intent recognition, recommendation logic, and pricing calculations
- Integration tests MUST validate end-to-end conversation flows for each user story
- Contract tests MUST verify API endpoint behavior and response schemas
- Performance tests MUST validate latency requirements under load

### Deployment Approval
- Architecture changes affecting recommendation accuracy require AWS solution architect review
- Pricing calculation changes require validation against AWS Pricing API
- New AWS service integrations require security review for IAM permissions

## Governance

This constitution supersedes all other development practices and coding standards. All code, architecture decisions, and feature implementations MUST comply with these principles.

**Amendment Procedure**: Constitution amendments require:
1. Documentation of the proposed change and rationale
2. Impact analysis on existing features and dependent templates
3. Approval from project maintainers
4. Update to version number following semantic versioning (MAJOR.MINOR.PATCH)
5. Propagation of changes to dependent templates and documentation

**Compliance Review**: All PRs MUST include a constitution compliance check. Violations MUST be justified in the Complexity Tracking section of the implementation plan, or the PR MUST be rejected.

**Versioning Policy**:
- MAJOR: Backward incompatible principle removals or redefinitions
- MINOR: New principle added or materially expanded guidance
- PATCH: Clarifications, wording improvements, typo fixes

**Complexity Justification**: Any deviation from these principles (e.g., adding a non-conversational interface, skipping pricing, or hardcoding AWS knowledge) MUST be explicitly justified in the implementation plan's Complexity Tracking section, explaining why the simpler alternative was insufficient.

**Version**: 1.1.0 | **Ratified**: 2025-01-27 | **Last Amended**: 2025-01-27
