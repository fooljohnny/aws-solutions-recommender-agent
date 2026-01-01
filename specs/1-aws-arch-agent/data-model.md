# Data Model: AWS Solution Architecture Recommendation Agent

**Date**: 2025-01-27  
**Feature**: AWS Solution Architecture Recommendation Agent

## Entities

### Conversation

Represents a user session with the agent, identified by a session ID (no authentication required).

**Fields**:
- `session_id` (string, primary key): Unique session identifier (UUID)
- `created_at` (datetime): Session creation timestamp
- `last_accessed_at` (datetime): Last message timestamp
- `expires_at` (datetime): TTL timestamp (30 days from creation)
- `conversation_history` (array of Message): Ordered list of messages
- `current_context` (Context): Current conversation context state
- `user_preferences` (object, optional): User preferences (region, language, etc.)

**Relationships**:
- One-to-many with Message
- One-to-one with Context

**Validation Rules**:
- session_id must be UUID format
- expires_at must be exactly 30 days from created_at
- conversation_history limited to last 50 messages (to manage token limits)

**State Transitions**:
- Created → Active (on first message)
- Active → Expired (after 30 days or manual expiration)

### Message

Represents a single message in a conversation.

**Fields**:
- `message_id` (string, primary key): Unique message identifier (UUID)
- `session_id` (string, foreign key): Reference to Conversation
- `timestamp` (datetime): Message timestamp
- `role` (enum: "user" | "assistant"): Message sender role
- `content` (string): Message text content
- `intents` (array of Intent): Recognized intents from this message
- `metadata` (object, optional): Additional metadata (diagram URLs, pricing data, etc.)

**Relationships**:
- Many-to-one with Conversation
- One-to-many with Intent

**Validation Rules**:
- content must be non-empty string
- role must be "user" or "assistant"
- intents array may be empty for user messages (before processing)

### Intent

Represents a recognized user intent from a message.

**Fields**:
- `intent_id` (string, primary key): Unique intent identifier (UUID)
- `message_id` (string, foreign key): Reference to Message
- `intent_type` (enum: "architecture_request" | "pricing_query" | "clarification" | "modification"): Intent category
- `priority` (integer): Processing priority (1=architecture, 2=pricing, 3=clarification)
- `confidence` (float, 0-1): Recognition confidence score
- `extracted_entities` (object): Extracted entities from intent (services, requirements, etc.)
- `status` (enum: "pending" | "processing" | "completed" | "failed"): Processing status

**Relationships**:
- Many-to-one with Message

**Validation Rules**:
- priority must match intent_type (1 for architecture_request, 2 for pricing_query, 3 for clarification)
- confidence must be between 0 and 1
- status transitions: pending → processing → completed/failed

### ArchitectureRecommendation

Represents a recommended AWS solution architecture.

**Fields**:
- `recommendation_id` (string, primary key): Unique recommendation identifier (UUID)
- `session_id` (string, foreign key): Reference to Conversation
- `created_at` (datetime): Recommendation creation timestamp
- `services` (array of Service): Recommended AWS services
- `configurations` (array of Configuration): Service configurations
- `diagram_data` (string): Mermaid diagram source code
- `diagram_url` (string, optional): Rendered diagram URL
- `pricing` (PricingCalculation, optional): Associated pricing calculation
- `well_architected_alignment` (object): Alignment with Well-Architected Framework pillars
- `explanation` (string): Explanation of why services were recommended

**Relationships**:
- Many-to-one with Conversation
- One-to-many with Service
- One-to-many with Configuration
- One-to-one with PricingCalculation (optional)

**Validation Rules**:
- services array must not be empty
- diagram_data must be valid Mermaid syntax
- well_architected_alignment must include all 6 pillars

### Service

Represents an AWS service in a recommendation.

**Fields**:
- `service_id` (string, primary key): Unique service identifier (UUID)
- `recommendation_id` (string, foreign key): Reference to ArchitectureRecommendation
- `aws_service_name` (string): AWS service name (e.g., "EC2", "RDS", "S3")
- `service_type` (enum: "compute" | "storage" | "database" | "networking" | "security" | "monitoring" | "other"): Service category
- `role` (string): Role in architecture (e.g., "web server", "database", "load balancer")
- `region` (string, optional): AWS region
- `dependencies` (array of string): Service IDs this service depends on

**Relationships**:
- Many-to-one with ArchitectureRecommendation
- Many-to-many with Service (via dependencies)

**Validation Rules**:
- aws_service_name must be valid AWS service name
- dependencies must reference valid service_ids in same recommendation

### Configuration

Represents configuration for an AWS service.

**Fields**:
- `configuration_id` (string, primary key): Unique configuration identifier (UUID)
- `service_id` (string, foreign key): Reference to Service
- `config_type` (string): Configuration type (e.g., "instance_type", "storage_size", "encryption")
- `config_value` (string): Configuration value (e.g., "t3.medium", "100GB", "AES256")
- `config_details` (object, optional): Additional configuration details

**Relationships**:
- Many-to-one with Service

**Validation Rules**:
- config_type and config_value must be non-empty
- config_value must be valid for the config_type

### PricingCalculation

Represents a cost estimate for an architecture.

**Fields**:
- `pricing_id` (string, primary key): Unique pricing identifier (UUID)
- `recommendation_id` (string, foreign key): Reference to ArchitectureRecommendation
- `calculated_at` (datetime): Calculation timestamp
- `total_monthly_cost` (decimal): Total estimated monthly cost (USD)
- `cost_breakdown` (array of ServiceCost): Itemized costs by service
- `usage_assumptions` (object): Usage assumptions used in calculation
- `pricing_data_source` (enum: "api" | "cache"): Source of pricing data
- `pricing_data_freshness` (datetime): Timestamp of pricing data used

**Relationships**:
- One-to-one with ArchitectureRecommendation
- One-to-many with ServiceCost

**Validation Rules**:
- total_monthly_cost must be >= 0
- cost_breakdown must sum to total_monthly_cost (within rounding tolerance)
- pricing_data_freshness must be within 24 hours if source is "cache"

### ServiceCost

Represents cost for a single service in pricing calculation.

**Fields**:
- `service_cost_id` (string, primary key): Unique service cost identifier (UUID)
- `pricing_id` (string, foreign key): Reference to PricingCalculation
- `service_name` (string): AWS service name
- `monthly_cost` (decimal): Estimated monthly cost (USD)
- `cost_components` (array of CostComponent): Breakdown of cost components
- `usage_estimate` (object): Usage estimate used for calculation

**Relationships**:
- Many-to-one with PricingCalculation
- One-to-many with CostComponent

**Validation Rules**:
- monthly_cost must be >= 0
- service_name must match a service in the recommendation

### CostComponent

Represents a component of service cost (e.g., compute, storage, data transfer).

**Fields**:
- `component_id` (string, primary key): Unique component identifier (UUID)
- `service_cost_id` (string, foreign key): Reference to ServiceCost
- `component_type` (string): Component type (e.g., "compute", "storage", "data_transfer")
- `cost` (decimal): Component cost (USD)
- `unit` (string): Cost unit (e.g., "per hour", "per GB")

**Relationships**:
- Many-to-one with ServiceCost

**Validation Rules**:
- cost must be >= 0
- component_type must be valid AWS cost component

### UserRequirement

Represents extracted user requirements from conversation.

**Fields**:
- `requirement_id` (string, primary key): Unique requirement identifier (UUID)
- `session_id` (string, foreign key): Reference to Conversation
- `extracted_at` (datetime): Extraction timestamp
- `requirement_type` (enum: "application_type" | "scale" | "constraint" | "preference"): Requirement category
- `requirement_value` (string): Requirement value (e.g., "web application", "1000 users", "high availability")
- `confidence` (float, 0-1): Extraction confidence score
- `source_message_id` (string, foreign key, optional): Message where requirement was extracted

**Relationships**:
- Many-to-one with Conversation
- Many-to-one with Message (optional)

**Validation Rules**:
- requirement_type and requirement_value must be non-empty
- confidence must be between 0 and 1

### Context

Represents current conversation context state.

**Fields**:
- `context_id` (string, primary key): Unique context identifier (UUID)
- `session_id` (string, foreign key, unique): Reference to Conversation
- `current_recommendation_id` (string, foreign key, optional): Current active recommendation
- `extracted_requirements` (array of UserRequirement): Active requirements
- `conversation_summary` (string, optional): Summarized conversation history
- `last_intents` (array of Intent, optional): Last processed intents
- `updated_at` (datetime): Last context update timestamp

**Relationships**:
- One-to-one with Conversation
- One-to-many with UserRequirement
- One-to-one with ArchitectureRecommendation (optional)

**Validation Rules**:
- context_id must match session_id (1:1 relationship)
- conversation_summary limited to 500 characters

## Data Storage

### Primary Storage: DynamoDB

**Tables**:
- `conversations`: Conversation entity (partition key: session_id)
- `messages`: Message entity (partition key: session_id, sort key: timestamp)
- `recommendations`: ArchitectureRecommendation entity (partition key: session_id, sort key: created_at)
- `pricing_calculations`: PricingCalculation entity (partition key: recommendation_id)

**TTL Configuration**:
- conversations.expires_at: Automatic deletion after 30 days
- messages: Deleted when parent conversation expires

### Secondary Storage: Redis (Optional)

**Use Cases**:
- Pricing cache (L1 cache)
- Session state cache (hot sessions)
- Rate limiting counters

**TTL Configuration**:
- Pricing cache: 24 hours
- Session cache: 1 hour
- Rate limit: Per request window

## Data Access Patterns

### Conversation Retrieval
- Query by session_id
- Retrieve last N messages for context
- Filter by timestamp range

### Recommendation Lookup
- Query by session_id and recommendation_id
- List all recommendations for a session
- Query by creation date

### Pricing Lookup
- Query by recommendation_id
- Query by service name and region (for cache)

## Data Privacy & Compliance

### Encryption
- All data encrypted at rest (DynamoDB encryption)
- All data encrypted in transit (TLS)

### Retention
- Automatic deletion after 30 days (TTL)
- Manual deletion support (future enhancement)

### Access Control
- Session-based access (no authentication required)
- Session ID validation prevents unauthorized access
- Rate limiting per session

