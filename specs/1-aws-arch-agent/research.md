# Research: AWS Solution Architecture Recommendation Agent

**Date**: 2025-01-27  
**Feature**: AWS Solution Architecture Recommendation Agent  
**Phase**: 0 - Research & Technology Selection

## Technology Decisions

### LLM Framework Selection

**Decision**: Use LangGraph for conversation orchestration with OpenAI GPT-4 or Anthropic Claude for Chinese language support

**Rationale**: 
- LangGraph provides state machine-based conversation management, required by constitution for state transition auditing
- Supports complex multi-turn dialogue with state persistence
- Enables function calling/tool use for structured AWS service queries
- Both GPT-4 and Claude have strong Chinese language capabilities
- Function calling support enables MCP tool integration

**Alternatives Considered**:
- LangChain: More complex, less state machine focused
- Custom state management: Too much reinvention, violates DRY principle
- Amazon Lex: Limited to AWS ecosystem, less flexible for custom logic

### Conversation State Management

**Decision**: Use LangGraph StateGraph with persistent storage in DynamoDB

**Rationale**:
- LangGraph StateGraph provides explicit state transitions (required for constitution compliance)
- DynamoDB supports 30-day TTL for automatic conversation history cleanup
- Fast retrieval (< 500ms requirement) with DynamoDB query patterns
- Scales to 100+ concurrent conversations
- No authentication required (session ID only)

**Alternatives Considered**:
- PostgreSQL: More complex setup, overkill for session storage
- Redis: Faster but no built-in TTL management, requires manual cleanup
- In-memory: Doesn't support conversation resumption across restarts

### Multi-Intent Recognition

**Decision**: Use LLM function calling with structured intent classification schema

**Rationale**:
- LLM function calling provides structured output for intent classification
- Supports priority ordering (architecture > pricing > clarification) as specified
- Can handle multiple intents in single classification call
- Natural language understanding for Chinese input

**Alternatives Considered**:
- Separate classification model: Adds complexity, requires training data
- Rule-based parsing: Too brittle for natural language
- Sequential processing: Doesn't meet multi-intent requirement

### AWS Pricing Integration

**Decision**: Daily scheduled job updates pricing cache, real-time queries use cache with API fallback

**Rationale**:
- Daily updates balance accuracy with API rate limits
- Cached data ensures < 3s pricing calculation requirement
- Fallback to API when cache stale or unavailable
- Reduces AWS Pricing API costs and latency

**Alternatives Considered**:
- Real-time API queries only: Too slow, violates < 3s requirement
- Weekly updates: May be too stale for accurate pricing
- Static pricing data: Doesn't meet accuracy requirements

### Architecture Diagram Generation

**Decision**: Use Mermaid for diagram generation with AWS Architecture Icons library

**Rationale**:
- Mermaid is machine-readable (text-based) and human-viewable (rendered SVG/PNG)
- Supports programmatic generation from architecture data
- AWS Architecture Icons available as SVG library for integration
- Can be embedded in API responses and provided as download links
- Meets < 10s generation requirement

**Alternatives Considered**:
- PlantUML: Less flexible for AWS-specific icons
- AWS native diagram tools: Not programmatically accessible
- Manual diagram creation: Doesn't scale, violates automation requirement

### AWS Service Knowledge Base

**Decision**: Structured JSON knowledge base with vector embeddings for semantic search

**Rationale**:
- Structured data enables validation against AWS documentation (FR-010)
- Vector embeddings support semantic matching for ambiguous service names
- Can be updated independently from code
- Supports Well-Architected Framework alignment checks

**Alternatives Considered**:
- Hardcoded service lists: Not maintainable, violates accuracy principle
- Real-time AWS API queries: Too slow, may not have all metadata
- External knowledge graph: Adds dependency, complexity

### API Framework

**Decision**: FastAPI with async support

**Rationale**:
- FastAPI provides async support for concurrent conversations (100+ requirement)
- Automatic OpenAPI schema generation for contract testing
- Strong typing with Pydantic for request/response validation
- High performance, meets latency requirements

**Alternatives Considered**:
- Flask: Synchronous, doesn't scale to 100+ concurrent users
- Django: Too heavyweight for API-only service
- Express.js: Wrong language (Python required by constitution)

### Testing Strategy

**Decision**: pytest with contract testing, integration tests for conversation flows

**Rationale**:
- pytest is standard for Python projects
- Contract testing validates API schemas (constitution requirement)
- Integration tests validate end-to-end conversation flows per user story
- Supports testability principle (Constitution VII)

**Alternatives Considered**:
- unittest: Less feature-rich than pytest
- Manual testing only: Doesn't meet testability requirement

## Architecture Patterns

### LangGraph State Machine Pattern

**Pattern**: Use LangGraph StateGraph with explicit nodes for:
- Intent recognition
- Architecture recommendation
- Pricing calculation
- Diagram generation
- Response formatting

**Rationale**: 
- Enables state transition visualization (constitution requirement)
- Prevents infinite loops through explicit graph structure
- Supports multi-intent processing with conditional edges
- Maintains conversation context in AgentState

### MCP Tool Pattern

**Pattern**: Implement MCP servers for:
- AWS Pricing API tool
- AWS Service Knowledge tool
- Diagram Generation tool

**Rationale**:
- MCP provides structured JSON schemas (constitution requirement)
- Enables mock responses for testing
- Standardizes tool interface for LLM function calling
- Supports tool composition and reuse

### Caching Pattern

**Pattern**: Two-tier caching:
- L1: In-memory cache for frequently accessed pricing data
- L2: DynamoDB cache with daily refresh job

**Rationale**:
- Meets < 3s pricing calculation requirement
- Reduces AWS Pricing API calls and costs
- Provides fallback when API unavailable
- Automatic cache invalidation with TTL

## Integration Points

### AWS Pricing API Integration

**Endpoint**: AWS Pricing API (GetProducts, GetPrice)
**Authentication**: IAM role with least-privilege permissions
**Rate Limits**: Handle throttling with exponential backoff
**Error Handling**: Fallback to cached data with freshness disclaimers

### AWS Service Documentation Integration

**Source**: AWS Well-Architected Framework, AWS Service documentation
**Update Frequency**: Manual updates when new services released
**Format**: Structured JSON with service metadata, capabilities, limitations

### LLM API Integration

**Provider**: OpenAI GPT-4 or Anthropic Claude
**Features Required**: Function calling, Chinese language support, streaming (optional)
**Error Handling**: Retry with exponential backoff, fallback to cached responses if available

## Performance Considerations

### Intent Recognition Optimization

- Cache common intent patterns
- Batch processing for multiple intents
- Parallel tool calls where possible

### Diagram Generation Optimization

- Pre-render common architecture patterns
- Cache generated diagrams for similar architectures
- Async generation to avoid blocking conversation flow

### Context Retrieval Optimization

- Index conversation history by session ID and timestamp
- Limit context window to last 10 turns (per SC-007)
- Compress old context when approaching token limits

## Security Considerations

### Data Encryption

- Encrypt conversation data at rest (DynamoDB encryption)
- TLS for all API communications
- Encrypt pricing cache data

### Input Validation

- Sanitize all user inputs to prevent injection attacks
- Validate session IDs to prevent unauthorized access
- Rate limit per session to prevent abuse

### AWS Credentials

- Use IAM roles, never store credentials in code
- Least-privilege permissions for Pricing API access
- Rotate credentials regularly

## Compliance Considerations

### GDPR/CCPA Compliance

- 30-day retention with automatic deletion (TTL)
- User data encryption
- Clear data handling policies
- Support for data deletion requests (future enhancement)

## Open Questions Resolved

1. **Q**: How to handle Chinese language input/output?  
   **A**: Use GPT-4 or Claude with Chinese-optimized prompts and function schemas

2. **Q**: How to ensure AWS service knowledge accuracy?  
   **A**: Structured knowledge base with validation against AWS documentation, regular updates

3. **Q**: How to meet pricing accuracy requirements?  
   **A**: Daily cache updates with real-time API fallback, validation against AWS Pricing Calculator

4. **Q**: How to support 100+ concurrent conversations?  
   **A**: FastAPI async, DynamoDB for state storage, efficient context retrieval

5. **Q**: How to generate architecture diagrams programmatically?  
   **A**: Mermaid with AWS Architecture Icons, programmatic generation from service data

