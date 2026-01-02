# AWS Solution Architecture Recommendation Agent

智能云解决方案推荐智能体 - An intelligent conversational agent that recommends AWS cloud solution architectures through natural language dialogue.

## 项目简介 / Project Overview

本项目是一个智能对话式AWS云架构推荐系统，通过自然语言对话帮助用户获得专业的AWS云解决方案架构建议。系统支持中文（简体）交互，能够理解用户需求、推荐合适的AWS服务、生成架构图、提供配置详情和成本估算。

This project provides a command-line interface (CLI) for interacting with an AI agent that recommends AWS cloud architectures. The agent supports natural language interaction in Chinese (Simplified) and provides expert-level AWS architecture recommendations with visual diagrams, detailed configurations, and cost estimates.

### 核心功能 / Core Features

- 🎯 **基础架构推荐** (MVP): 通过自然语言对话获得AWS架构推荐和可视化图表
- 🔀 **多意图识别**: 在单条消息中识别和处理多个意图（架构请求、价格查询、澄清等）
- 💰 **价格详情**: 基于AWS Pricing API的准确成本估算，支持按服务分项明细
- 💬 **上下文保留**: 支持多轮对话，保持30天的会话上下文
- 📊 **架构图生成**: 自动生成Mermaid格式的架构图，支持SVG/PNG导出
- 🔍 **配置详情**: 提供详细的AWS服务配置规格（实例类型、存储选项等）
- 🔄 **场景对比**: 支持"假设"场景，对比不同配置的成本差异

### 技术特性 / Technical Features

- **多意图处理**: 单条消息可包含多个意图，按优先级处理（架构请求 > 价格查询 > 澄清）
- **上下文管理**: 使用LangGraph状态机管理对话流程，支持30天会话恢复
- **实时定价**: 集成AWS Pricing API，支持缓存和API回退机制
- **知识库验证**: AWS服务推荐基于Well-Architected Framework验证
- **可观测性**: 结构化日志、指标收集、健康检查
- **安全合规**: 数据加密、GDPR/CCPA合规、速率限制

## 系统要求 / Prerequisites

- **Python**: 3.11 或更高版本
- **AWS账户**: 用于AWS Pricing API访问（可选，可使用缓存数据）
- **LLM API密钥**: OpenAI API密钥 或 Anthropic API密钥（必需）
- **存储服务** (可选):
  - DynamoDB: 用于会话和消息存储
  - Redis: 用于价格缓存（可选）

## 安装步骤 / Installation

### 1. 克隆仓库

```bash
git clone <repository-url>
cd aws-solutions-recommender-agent
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入以下必需配置：
# OPENAI_API_KEY=your_openai_api_key_here
# 或
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# AWS配置（可选，用于Pricing API）
# AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=your_aws_access_key_id
# AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

## 启动运行方法 / Running the Application

### 方式一：CLI命令行界面（推荐）

CLI是主要的用户交互界面，提供交互式对话体验。

#### 启动新会话

```bash
# 使用命令行工具
aws-arch-agent chat

# 或直接使用Python模块
python -m src.cli.main chat
```

#### 恢复已有会话

```bash
# 使用会话ID恢复对话
aws-arch-agent chat --session-id <your-session-id>

# 或
python -m src.cli.main chat --session-id <your-session-id>
```

#### 指定LLM提供商

```bash
# 使用OpenAI (默认)
aws-arch-agent chat --llm openai

# 使用Anthropic
aws-arch-agent chat --llm anthropic
```

#### 使用示例

```bash
$ python -m src.cli.main chat

┌─────────────────────────────────────────┐
│ AWS Solution Architecture Recommendation │
│            Agent                         │
│    智能云解决方案推荐智能体                │
└─────────────────────────────────────────┘

New session created: 550e8400-e29b-41d4-a716-446655440000

Enter your requirements in Chinese. Type 'exit' or 'quit' to end.

You: 我需要一个能处理1000用户的Web应用架构

[Processing...]

Agent: 根据您的需求，我为您推荐以下AWS架构方案：

**推荐的服务：**
- **EC2**: Web服务器
- **RDS**: 数据库
- **S3**: 静态资源存储

**架构说明：**
推荐使用EC2作为Web服务器，RDS作为数据库...

**架构图：**
架构图已生成，可通过以下链接查看：/diagrams/880e8400-e29b-41d4-a716-446655440003.svg

You: 这个架构每月需要多少钱？

Agent: ## 价格信息
**预估月成本**: $245.50

**成本明细：**
- EC2: $150.00
- RDS: $95.50
```

### 方式二：API服务器（可选，用于程序化访问）

API服务器提供RESTful接口，支持程序化集成。

#### 启动API服务器

```bash
# 使用uvicorn启动
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 或使用Python直接运行
python -m uvicorn src.api.main:app --reload
```

#### 访问API文档

启动后访问以下URL查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

#### API使用示例

```bash
# 1. 创建会话
curl -X POST http://localhost:8000/v1/conversations

# 响应:
# {
#   "session_id": "550e8400-e29b-41d4-a716-446655440000",
#   "created_at": "2025-01-27T10:00:00Z",
#   "expires_at": "2025-02-26T10:00:00Z"
# }

# 2. 发送消息
curl -X POST http://localhost:8000/v1/conversations/{session_id}/messages \
  -H "Content-Type: application/json" \
  -d '{"content": "我需要一个能处理1000用户的Web应用架构"}'

# 3. 获取会话历史
curl http://localhost:8000/v1/conversations/{session_id}/history
```

### 方式三：运行定价更新任务（可选）

如果需要更新AWS定价缓存：

```bash
python -m src.services.pricing.updater
```

## 代码架构介绍 / Architecture Overview

### 整体架构

系统采用分层架构设计，清晰分离关注点：

```
┌─────────────────────────────────────────────────────────┐
│                    CLI / API Layer                       │
│  (用户交互层: CLI命令行界面 / REST API)                   │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              Conversation Orchestration                 │
│  (对话编排层: LangGraph状态机管理对话流程)                │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼──────┐ ┌────▼──────┐
│  Intent      │ │Recommend  │ │  Pricing  │
│ Recognition  │ │  Engine    │ │ Calculator │
└──────────────┘ └────────────┘ └───────────┘
        │              │              │
┌───────▼──────────────────────────────▼──────┐
│         AWS Knowledge Base                   │
│    (AWS服务知识库和验证)                      │
└─────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────┐
│         Storage Layer                        │
│  (存储层: DynamoDB + Redis)                   │
└─────────────────────────────────────────────┘
```

### 目录结构详解

```
aws-solutions-recommender-agent/
├── src/                                    # 源代码目录
│   ├── models/                            # 数据模型层
│   │   ├── conversation.py               # 会话模型（会话ID、过期时间、历史记录）
│   │   ├── message.py                    # 消息模型（用户/助手消息）
│   │   ├── intent.py                     # 意图模型（架构请求、价格查询等）
│   │   ├── user_requirement.py           # 用户需求模型（提取的需求信息）
│   │   ├── architecture_recommendation.py # 架构推荐模型
│   │   ├── service.py                    # AWS服务模型
│   │   ├── configuration.py              # 配置模型
│   │   ├── pricing_calculation.py        # 价格计算模型
│   │   ├── context.py                    # 上下文模型（会话状态）
│   │   └── ...
│   │
│   ├── services/                          # 业务逻辑服务层
│   │   ├── conversation/                  # 对话管理服务
│   │   │   ├── orchestrator.py           # 对话编排器（LangGraph集成）
│   │   │   ├── context_retriever.py     # 上下文检索服务
│   │   │   ├── context_updater.py        # 上下文更新服务
│   │   │   ├── summarizer.py             # 对话摘要服务（LLM）
│   │   │   ├── history_manager.py        # 历史记录管理（50条消息限制）
│   │   │   ├── session_manager.py        # 会话管理（30天TTL）
│   │   │   └── formatter.py              # 多意图响应格式化
│   │   │
│   │   ├── intent/                       # 意图识别服务
│   │   │   ├── classifier.py             # 多意图分类器（LLM函数调用）
│   │   │   ├── processor.py              # 意图优先级处理器
│   │   │   ├── extractor.py             # 意图实体提取器
│   │   │   ├── orchestrator.py           # 意图处理编排器
│   │   │   └── aggregator.py             # 意图结果聚合器
│   │   │
│   │   ├── recommendation/                # 架构推荐服务
│   │   │   ├── requirement_extractor.py  # 需求提取服务（LLM）
│   │   │   ├── recommender.py            # 架构推荐引擎（LLM）
│   │   │   ├── well_architected.py       # Well-Architected框架验证
│   │   │   ├── config_spec.py            # 配置规格生成服务
│   │   │   └── modifier.py               # 推荐修改服务（基于上下文）
│   │   │
│   │   ├── pricing/                       # 价格计算服务
│   │   │   ├── calculator.py             # 价格计算器（AWS Pricing API）
│   │   │   ├── cache.py                  # 价格缓存服务（Redis）
│   │   │   ├── updater.py                # 每日价格更新任务
│   │   │   ├── whatif.py                 # 假设场景服务
│   │   │   └── comparison.py             # 成本对比服务
│   │   │
│   │   ├── diagram/                       # 图表生成服务
│   │   │   ├── generator.py              # Mermaid图表生成器
│   │   │   ├── icons.py                  # AWS架构图标映射
│   │   │   ├── renderer.py               # 图表渲染器（SVG/PNG）
│   │   │   └── storage.py                # 图表存储和URL生成
│   │   │
│   │   └── aws_knowledge/                 # AWS知识库服务
│   │       ├── base.py                   # 知识库基础结构
│   │       ├── catalog.py                # 服务目录加载器（JSON）
│   │       └── validator.py              # 服务验证器（Well-Architected）
│   │
│   ├── agents/                            # LangGraph智能体层
│   │   ├── state/                        # 状态定义
│   │   │   └── agent_state.py            # AgentState（会话状态、推荐、意图等）
│   │   ├── prompts/                      # 提示词模板
│   │   │   └── chinese.py                # 中文提示词（需求提取、推荐等）
│   │   └── conversation_graph.py         # 对话图定义（节点和边）
│   │
│   ├── api/                               # API接口层（可选）
│   │   ├── main.py                       # FastAPI应用主入口
│   │   ├── routes/                       # 路由处理器
│   │   │   ├── conversations.py          # 会话路由（创建、获取、历史）
│   │   │   ├── messages.py              # 消息路由（发送消息）
│   │   │   └── health.py                # 健康检查路由
│   │   ├── schemas/                      # Pydantic请求/响应模式
│   │   │   ├── requests.py              # 请求模式
│   │   │   └── responses.py             # 响应模式
│   │   └── middleware/                   # 中间件
│   │       ├── error_handler.py         # 错误处理中间件
│   │       ├── validator.py             # 输入验证中间件
│   │       └── rate_limiter.py          # 速率限制中间件
│   │
│   ├── cli/                               # CLI命令行界面
│   │   ├── main.py                       # CLI主入口（Typer）
│   │   └── chat.py                       # 交互式聊天会话
│   │
│   ├── repositories/                      # 数据访问层
│   │   ├── conversation_repository.py    # 会话数据访问
│   │   ├── message_repository.py         # 消息数据访问
│   │   ├── intent_repository.py          # 意图数据访问
│   │   └── user_requirement_repository.py # 需求数据访问
│   │
│   ├── tools/                             # MCP工具层
│   │   └── aws_pricing/                  # AWS定价工具
│   │       ├── client.py                 # AWS Pricing API客户端
│   │       ├── mcp_tool.py               # MCP工具接口
│   │       └── handler.py                # 工具处理器
│   │
│   └── utils/                             # 工具类
│       ├── storage/                      # 存储工具
│       │   ├── dynamodb.py              # DynamoDB客户端包装
│       │   └── redis.py                 # Redis客户端包装
│       ├── logging/                      # 日志工具
│       │   └── logger.py                # 结构化日志记录器
│       ├── metrics/                      # 指标工具
│       │   └── collector.py             # 指标收集器
│       ├── security/                     # 安全工具
│       │   └── encryption.py            # 加密配置
│       └── compliance/                   # 合规工具
│           └── data_privacy.py           # GDPR/CCPA合规
│
├── tests/                                 # 测试目录
│   ├── contract/                         # 合约测试
│   │   └── test_api_schema.py          # API模式验证测试
│   ├── integration/                      # 集成测试
│   │   └── helpers.py                   # 测试辅助函数
│   └── unit/                             # 单元测试
│       └── fixtures.py                  # 测试夹具（Mock服务）
│
├── specs/                                 # 项目规范文档
│   └── 1-aws-arch-agent/                 # 功能规范
│       ├── spec.md                       # 功能规格说明
│       ├── plan.md                       # 实施计划
│       ├── data-model.md                 # 数据模型
│       ├── tasks.md                      # 任务清单
│       └── contracts/                    # API合约
│           └── api.yaml                  # OpenAPI规范
│
├── requirements.txt                       # Python依赖
├── pyproject.toml                        # 项目配置
├── .env.example                          # 环境变量示例
└── README.md                             # 本文件
```

### 核心组件说明

#### 1. 对话编排层 (Conversation Orchestration)

**文件**: `src/services/conversation/orchestrator.py`

使用LangGraph构建状态机，管理完整的对话流程：

```
用户消息
  ↓
意图分类 (classify_intents)
  ↓
需求提取 (extract_requirements) - 支持上下文合并
  ↓
架构推荐 (generate_recommendation) - 基于需求和上下文
  ↓
图表生成 (generate_diagram) - Mermaid格式
  ↓
响应格式化 (format_response) - 多意图响应聚合
  ↓
返回结果
```

**关键特性**:
- 状态持久化：AgentState保存对话状态、推荐、意图等
- 上下文感知：自动加载和更新会话上下文
- 错误处理：每个节点都有错误处理机制

#### 2. 意图识别层 (Intent Recognition)

**文件**: `src/services/intent/classifier.py`

使用LLM函数调用识别多个意图：

- **架构请求** (priority 1): 请求推荐或修改架构
- **价格查询** (priority 2): 询问成本信息
- **澄清请求** (priority 3): 需要更多信息

**处理流程**:
1. LLM分类所有意图
2. 按优先级排序
3. 提取每个意图的实体
4. 顺序处理每个意图
5. 聚合结果生成响应

#### 3. 架构推荐引擎 (Recommendation Engine)

**文件**: `src/services/recommendation/recommender.py`

基于用户需求和AWS知识库生成推荐：

1. **需求分析**: 提取应用类型、规模、约束条件
2. **服务选择**: 从AWS知识库匹配合适服务
3. **配置生成**: 根据规模生成详细配置
4. **验证**: 使用Well-Architected Framework验证
5. **解释生成**: LLM生成推荐理由

#### 4. 价格计算服务 (Pricing Service)

**文件**: `src/services/pricing/calculator.py`

**数据流**:
```
服务配置
  ↓
检查Redis缓存 (L1)
  ↓ (未命中)
检查DynamoDB缓存 (L2)
  ↓ (未命中或过期)
调用AWS Pricing API
  ↓
更新缓存
  ↓
计算月成本
```

**特性**:
- 两级缓存（Redis + DynamoDB）
- API失败时使用缓存回退
- 每日自动更新任务
- 支持假设场景对比

#### 5. 上下文管理 (Context Management)

**文件**: `src/services/conversation/context_retriever.py`, `context_updater.py`

**上下文包含**:
- 提取的需求列表
- 当前推荐架构
- 对话摘要（长对话时）
- 最后处理的意图

**更新策略**:
- 增量更新：每次消息后更新
- 摘要压缩：超过50条消息时生成摘要
- 30天TTL：自动过期清理

#### 6. 存储层 (Storage Layer)

**DynamoDB表结构**:
- `conversations`: 会话表（主键: session_id）
- `messages`: 消息表（主键: session_id + timestamp）
- `recommendations`: 推荐表（主键: session_id + created_at）

**Redis缓存**:
- 价格数据：24小时TTL
- 会话状态：1小时TTL（热会话）
- 速率限制：按窗口计数

### 数据流示例

#### 完整对话流程

```
1. 用户输入: "我需要一个Web应用架构，能处理1000用户，还要知道价格"
   ↓
2. 意图分类: 
     - architecture_request (priority 1)
     - pricing_query (priority 2)
   ↓
3. 需求提取:
     - application_type: "Web应用"
     - scale: "1000用户"
   ↓
4. 架构推荐:
     - 服务: EC2, RDS, S3
     - 配置: t3.medium, db.t3.medium
     - 图表: Mermaid生成
   ↓
5. 价格计算:
     - EC2: $150/月
     - RDS: $95.50/月
     - 总计: $245.50/月
   ↓
6. 响应格式化:
     - 架构推荐部分
     - 价格信息部分
   ↓
7. 上下文更新:
     - 保存推荐
     - 更新需求列表
     - 更新对话摘要
```

## 配置说明 / Configuration

### 环境变量

完整的环境变量配置请参考 `.env.example`。主要配置项：

#### LLM配置（必需）

```bash
# 选择其中一个
OPENAI_API_KEY=sk-...
# 或
ANTHROPIC_API_KEY=sk-ant-...
```

#### AWS配置（可选，用于Pricing API）

```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

#### 存储配置

```bash
# DynamoDB表名
DYNAMODB_TABLE_CONVERSATIONS=conversations
DYNAMODB_TABLE_MESSAGES=messages
DYNAMODB_TABLE_RECOMMENDATIONS=recommendations

# Redis配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

#### 应用配置

```bash
LOG_LEVEL=INFO
CONVERSATION_TTL_DAYS=30
PRICING_CACHE_TTL_HOURS=24
```

#### API配置（仅API模式）

```bash
API_HOST=0.0.0.0
API_PORT=8000
```

## 开发指南 / Development

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/unit/
pytest tests/integration/
pytest tests/contract/

# 带覆盖率
pytest --cov=src tests/
```

### 代码质量检查

```bash
# 代码格式化
black src/ tests/

# 代码检查
ruff check src/ tests/

# 类型检查
mypy src/
```

### 项目结构说明

- **models/**: 数据模型，使用Pydantic定义，支持验证和序列化
- **services/**: 业务逻辑，按功能模块组织（对话、意图、推荐、价格、图表）
- **agents/**: LangGraph智能体定义，管理对话状态机
- **api/**: FastAPI REST接口（可选，用于程序化访问）
- **cli/**: 命令行界面，使用Typer和Rich构建
- **repositories/**: 数据访问抽象层，封装DynamoDB操作
- **tools/**: MCP工具，用于LLM函数调用
- **utils/**: 工具类（存储、日志、指标、安全、合规）

### 关键设计决策

1. **LangGraph状态机**: 符合Constitution要求，支持状态转换审计
2. **多意图处理**: 单消息多意图，按优先级顺序处理
3. **两级缓存**: Redis (L1) + DynamoDB (L2) 确保价格查询性能
4. **上下文管理**: 30天TTL，支持会话恢复和上下文压缩
5. **CLI优先**: 主要接口为CLI，API为可选功能

## 使用示例 / Usage Examples

### 示例1: 基础架构推荐

```bash
$ python -m src.cli.main chat

You: 我需要一个能处理1000用户的Web应用架构

Agent: 根据您的需求，我为您推荐以下AWS架构方案：

**推荐的服务：**
- **EC2**: Web服务器
- **RDS**: 数据库
- **S3**: 静态资源存储
- **CloudFront**: CDN加速

**架构说明：**
推荐使用EC2作为Web服务器，RDS作为数据库...

**架构图：**
/diagrams/xxx.svg
```

### 示例2: 多意图消息

```bash
You: 给我一个更安全的版本，并且告诉我价格是多少？

Agent: ## 架构推荐
[安全增强的架构方案，包含WAF、KMS等]

## 价格信息
**预估月成本**: $295.50
[详细成本明细]
```

### 示例3: 多轮对话

```bash
You: 我需要一个Web应用架构
Agent: [推荐基础架构]

You: 让它更安全一些
Agent: [基于之前的推荐，添加安全服务]

You: 这个架构的价格是多少？
Agent: [计算并显示价格，理解"这个架构"指之前的推荐]
```

## 性能指标 / Performance

- **意图识别延迟**: < 2秒（单意图），< 5秒（多意图）
- **架构图生成**: < 10秒
- **价格计算**: < 3秒（使用缓存）
- **上下文检索**: < 500ms
- **并发支持**: 100+ 同时会话

## 故障排除 / Troubleshooting

### 常见问题

1. **LLM API错误**
   - 检查API密钥是否正确设置
   - 确认API配额未超限
   - 检查网络连接

2. **DynamoDB连接失败**
   - 检查AWS凭证配置
   - 确认表已创建（首次运行需初始化）
   - 检查区域设置

3. **Redis连接失败**
   - Redis为可选组件，价格缓存会回退到API
   - 检查Redis服务是否运行
   - 确认端口和密码配置

4. **价格数据不可用**
   - 系统会自动使用缓存数据
   - 运行价格更新任务：`python -m src.services.pricing.updater`
   - 检查AWS Pricing API访问权限

## 许可证 / License

MIT License

## 贡献指南 / Contributing

详细的项目规范和实施计划请参考 `specs/1-aws-arch-agent/` 目录：

- `spec.md`: 功能规格说明
- `plan.md`: 技术实施计划
- `data-model.md`: 数据模型定义
- `tasks.md`: 实施任务清单
- `contracts/api.yaml`: API接口规范

## 相关文档 / Related Documentation

- [功能规格说明](specs/1-aws-arch-agent/spec.md)
- [实施计划](specs/1-aws-arch-agent/plan.md)
- [数据模型](specs/1-aws-arch-agent/data-model.md)
- [API文档](specs/1-aws-arch-agent/contracts/api.yaml)
- [快速开始指南](specs/1-aws-arch-agent/quickstart.md)
