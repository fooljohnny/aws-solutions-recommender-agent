# Quick Start Guide: AWS Solution Architecture Recommendation Agent

**Date**: 2025-01-27  
**Feature**: AWS Solution Architecture Recommendation Agent

## Overview

This guide provides a quick start for using the AWS Solution Architecture Recommendation Agent API. The agent accepts natural language input in Chinese (Simplified) and provides AWS architecture recommendations with diagrams and pricing.

## Prerequisites

- API endpoint URL
- Session ID (obtained from creating a conversation)

## Basic Usage

### 1. Create a Conversation Session

```bash
POST /v1/conversations

Response:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-01-27T10:00:00Z",
  "expires_at": "2025-02-26T10:00:00Z"
}
```

### 2. Send a Message

```bash
POST /v1/conversations/{session_id}/messages
Content-Type: application/json

{
  "content": "我需要一个能处理1000用户的Web应用架构"
}

Response:
{
  "message_id": "660e8400-e29b-41d4-a716-446655440001",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "根据您的需求，我为您推荐以下AWS架构方案...",
  "timestamp": "2025-01-27T10:01:00Z",
  "intents": [
    {
      "intent_id": "770e8400-e29b-41d4-a716-446655440002",
      "intent_type": "architecture_request",
      "priority": 1,
      "confidence": 0.95,
      "status": "completed"
    }
  ],
  "recommendations": [
    {
      "recommendation_id": "880e8400-e29b-41d4-a716-446655440003",
      "created_at": "2025-01-27T10:01:00Z",
      "services": [
        {
          "service_id": "990e8400-e29b-41d4-a716-446655440004",
          "aws_service_name": "EC2",
          "service_type": "compute",
          "role": "Web服务器"
        },
        {
          "service_id": "aa0e8400-e29b-41d4-a716-446655440005",
          "aws_service_name": "RDS",
          "service_type": "database",
          "role": "数据库"
        }
      ],
      "diagram_data": "graph TB\n    A[EC2] --> B[RDS]\n    ...",
      "diagram_url": "https://api.example.com/v1/recommendations/880e8400-e29b-41d4-a716-446655440003/diagram?format=svg",
      "explanation": "推荐使用EC2作为Web服务器，RDS作为数据库..."
    }
  ],
  "diagrams": [
    {
      "diagram_id": "bb0e8400-e29b-41d4-a716-446655440006",
      "format": "svg",
      "url": "https://api.example.com/v1/recommendations/880e8400-e29b-41d4-a716-446655440003/diagram?format=svg"
    }
  ]
}
```

### 3. Ask for Pricing

```bash
POST /v1/conversations/{session_id}/messages

{
  "content": "这个架构每月需要多少钱？"
}

Response:
{
  "message_id": "cc0e8400-e29b-41d4-a716-446655440007",
  "content": "根据推荐的架构，预估每月成本如下...",
  "pricing": {
    "pricing_id": "dd0e8400-e29b-41d4-a716-446655440008",
    "calculated_at": "2025-01-27T10:02:00Z",
    "total_monthly_cost": 245.50,
    "cost_breakdown": [
      {
        "service_cost_id": "ee0e8400-e29b-41d4-a716-446655440009",
        "service_name": "EC2",
        "monthly_cost": 150.00,
        "cost_components": [
          {
            "component_type": "compute",
            "cost": 150.00,
            "unit": "per month"
          }
        ]
      },
      {
        "service_cost_id": "ff0e8400-e29b-41d4-a716-446655440010",
        "service_name": "RDS",
        "monthly_cost": 95.50,
        "cost_components": [
          {
            "component_type": "database",
            "cost": 95.50,
            "unit": "per month"
          }
        ]
      }
    ],
    "pricing_data_source": "cache",
    "pricing_data_freshness": "2025-01-27T00:00:00Z"
  }
}
```

### 4. Multi-Intent Example

```bash
POST /v1/conversations/{session_id}/messages

{
  "content": "给我一个更安全的版本，并且告诉我价格是多少？"
}

Response:
{
  "message_id": "110e8400-e29b-41d4-a716-446655440011",
  "content": "我为您推荐一个更安全的架构方案...",
  "intents": [
    {
      "intent_id": "220e8400-e29b-41d4-a716-446655440012",
      "intent_type": "modification",
      "priority": 1,
      "confidence": 0.92,
      "status": "completed"
    },
    {
      "intent_id": "330e8400-e29b-41d4-a716-446655440013",
      "intent_type": "pricing_query",
      "priority": 2,
      "confidence": 0.88,
      "status": "completed"
    }
  ],
  "recommendations": [
    {
      "recommendation_id": "440e8400-e29b-41d4-a716-446655440014",
      "services": [
        {
          "aws_service_name": "EC2",
          "role": "Web服务器"
        },
        {
          "aws_service_name": "RDS",
          "role": "数据库"
        },
        {
          "aws_service_name": "WAF",
          "service_type": "security",
          "role": "Web应用防火墙"
        }
      ],
      "explanation": "在原有架构基础上，增加了WAF以提升安全性..."
    }
  ],
  "pricing": {
    "total_monthly_cost": 295.50,
    "cost_breakdown": [...]
  }
}
```

## Common Use Cases

### Use Case 1: Basic Architecture Recommendation

**User**: "我需要一个Web应用架构"  
**Agent**: Provides architecture recommendation with diagram

### Use Case 2: Architecture with Pricing

**User**: "给我推荐一个能处理10000用户的架构，并告诉我成本"  
**Agent**: Provides architecture recommendation and pricing calculation

### Use Case 3: Architecture Refinement

**User**: "我需要一个Web应用架构"  
**Agent**: Provides initial recommendation  
**User**: "让它更安全一些"  
**Agent**: Provides updated recommendation with security enhancements

### Use Case 4: What-If Scenario

**User**: "如果使用更小的实例，成本会是多少？"  
**Agent**: Provides alternative configuration and updated pricing

## Error Handling

### Session Not Found (404)

```json
{
  "error": "SESSION_NOT_FOUND",
  "message": "Session with ID {session_id} not found or expired",
  "details": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### Rate Limit Exceeded (429)

```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests. Please try again later.",
  "details": {
    "retry_after": 60
  }
}
```

### Invalid Request (400)

```json
{
  "error": "INVALID_REQUEST",
  "message": "Message content is required and must be non-empty",
  "details": {
    "field": "content"
  }
}
```

## Best Practices

1. **Session Management**: Store session_id securely. Sessions expire after 30 days.

2. **Context Preservation**: The agent maintains context across messages. Reference previous recommendations naturally (e.g., "这个架构" refers to the last recommendation).

3. **Multi-Intent**: You can combine multiple requests in one message. The agent processes them in priority order.

4. **Diagram Access**: Diagrams are embedded in responses and available via download links. Use the `diagram_url` for direct access.

5. **Pricing Accuracy**: Pricing data is updated daily. Check `pricing_data_freshness` to see when data was last updated.

6. **Error Recovery**: If a request fails, retry with exponential backoff. For session expiration, create a new session.

## Rate Limits

- **Per Session**: 60 requests per minute
- **Per IP**: 1000 requests per hour

## Support

For API documentation, see `contracts/api.yaml`.  
For data model details, see `data-model.md`.

