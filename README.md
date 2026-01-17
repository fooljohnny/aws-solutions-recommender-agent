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
- **LLM API密钥**: OpenAI API密钥、Anthropic API密钥 或 Groq API密钥（必需，至少一个）
- **存储服务**:
  - MySQL: 用于会话和消息存储（必需）
  - Redis: 用于价格缓存（可选）
  - Milvus: 用于向量数据库和RAG功能（可选，启用RAG时必需）

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
# 至少选择一个LLM提供商
# OPENAI_API_KEY=your_openai_api_key_here
# 或
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# 或
# GROQ_API_KEY=your_groq_api_key_here

# MySQL配置（必需，用于数据存储）
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_USER=root
# MYSQL_PASSWORD=your_mysql_password
# MYSQL_DATABASE=aws_arch_agent

# AWS配置（可选，用于Pricing API）
# AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=your_aws_access_key_id
# AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key

# Redis配置（可选，用于价格缓存）
# REDIS_HOST=localhost
# REDIS_PORT=6379
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

# 使用Groq (快速且经济)
aws-arch-agent chat --llm groq
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

## CLI 命令参考 / CLI Command Reference

本项目提供了完整的命令行界面（CLI），支持交互式对话和知识库管理。所有命令都可以通过 `python -m src.cli.main` 或安装后的 `aws-arch-agent` 命令访问。

### 主命令

#### `chat` - 交互式对话会话

启动与AI智能体的交互式对话，支持自然语言架构推荐。

**基本用法**:
```bash
# 启动新会话
python -m src.cli.main chat

# 恢复已有会话
python -m src.cli.main chat --session-id <session-id>

# 指定LLM提供商
python -m src.cli.main chat --llm <openai|anthropic|groq>
```

**选项**:
- `--session-id, -s`: 会话ID，用于恢复之前的对话（可选）
- `--llm`: LLM提供商，可选值：`openai`（默认）、`anthropic`、`groq`

**交互式命令**:
在对话过程中，支持以下斜杠命令：
- `/help` 或 `/?`: 显示帮助信息
- `/skills`: 列出所有可用的技能
- `/skill <name> [json_args]`: 执行指定技能，例如：`/skill ping {"message": "hello"}`

**示例**:
```bash
$ python -m src.cli.main chat --llm groq

┌─────────────────────────────────────────┐
│ AWS Solution Architecture Recommendation │
│            Agent                         │
│    智能云解决方案推荐智能体                │
└─────────────────────────────────────────┘

New session created: 550e8400-e29b-41d4-a716-446655440000

Enter your requirements in Chinese. Type 'exit' or 'quit' to end.

You: 我需要一个能处理1000用户的Web应用架构
[Processing...]
Agent: [架构推荐响应...]
```

#### `version` - 显示版本信息

显示项目版本信息。

**用法**:
```bash
python -m src.cli.main version
```

**输出**:
```
AWS Solution Architecture Recommendation Agent
Version: 0.1.0
```

### 知识库管理命令 (`kb`)

知识库管理命令用于管理解决方案模板知识库（Solution KB），支持导入CloudFormation模板、搜索、标注等功能。

#### `kb ingest` - 导入模板到知识库

将CloudFormation模板（JSON/YAML）导入到知识库中，支持Neo4j图数据库或本地文件存储。

**用法**:
```bash
python -m src.cli.main kb ingest <path> [选项]
```

**参数**:
- `path`（必需）: 模板文件路径或包含模板的目录路径

**选项**:
- `--source`: 模板来源标签，可选值：
  - `local`（默认）
  - `aws_quickstart`
  - `aws_solutions`
  - `aws_sar`
  - `aws_samples`
  - `terraform_aws_modules`
  - `aws_ia`
  - `community`
- `--repo`: 仓库标识符或URL（可选）
- `--kb-dir`: 知识库目录（默认：`.solution_kb`）
- `--max-files`: 目录扫描时的最大文件数（默认：2000）

**示例**:
```bash
# 导入单个模板文件
python -m src.cli.main kb ingest templates/web-app.yaml \
    --source aws_quickstart \
    --repo "github.com/aws-quickstart/quickstart-aws-vpc"

# 批量导入目录
python -m src.cli.main kb ingest templates/ \
    --source aws_solutions \
    --repo "github.com/aws-solutions" \
    --max-files 500
```

**输出**:
```
Ingest complete parsed=15 skipped=2 failed=0
```

#### `kb search` - 搜索模板

在知识库中搜索模板，支持关键词匹配。

**用法**:
```bash
python -m src.cli.main kb search <query> [选项]
```

**参数**:
- `query`（必需）: 搜索关键词

**选项**:
- `--kb-dir`: 知识库目录（默认：`.solution_kb`）
- `--limit`: 最大返回结果数（默认：5）

**示例**:
```bash
# 搜索Web应用相关模板
python -m src.cli.main kb search "web application" --limit 10

# 搜索高可用架构
python -m src.cli.main kb search "high availability"
```

**输出**:
```
┌─────────────────────────────────────────────────────────────┐
│                    KB Search Results                        │
├──────────────┬──────────────┬──────────┬──────────┬────────┤
│ template_id │ name          │ source   │ resource_types │ parameters │
├──────────────┼──────────────┼──────────┼──────────┼────────┤
│ abc-123...   │ Web应用架构  │ aws_quickstart │ EC2, RDS │ InstanceType, DBClass │
└──────────────┴──────────────┴──────────┴──────────┴────────┘
```

#### `kb init-neo4j` - 初始化Neo4j数据库

初始化Neo4j图数据库的约束和索引（仅需执行一次）。

**用法**:
```bash
python -m src.cli.main kb init-neo4j
```

**环境变量要求**:
- `NEO4J_URI`（必需）: Neo4j连接URI，例如：`bolt://localhost:7687`
- `NEO4J_USER`（可选）: 用户名，默认：`neo4j`
- `NEO4J_PASSWORD`（必需）: 密码
- `NEO4J_DATABASE`（可选）: 数据库名称

**示例**:
```bash
# 设置环境变量
export NEO4J_URI=bolt://localhost:7687
export NEO4J_PASSWORD=your_password

# 初始化数据库
python -m src.cli.main kb init-neo4j
```

**输出**:
```
Neo4j KB schema initialized.
```

#### `kb validate-meta` - 验证元数据文件

验证 `kb.meta.yaml` 元数据文件的格式是否正确。

**用法**:
```bash
python -m src.cli.main kb validate-meta <meta_path>
```

**参数**:
- `meta_path`（必需）: 元数据文件路径（支持 `.yaml`、`.yml`、`.json`）

**示例**:
```bash
# 验证元数据文件
python -m src.cli.main kb validate-meta templates/kb.meta.yaml
```

**输出**:
```
Meta file is valid.
Mode: single-template/default
```

#### `kb annotate` - 更新模板元数据

为已导入知识库的模板更新元数据（名称、描述、标签、行业分类等）。

**用法**:
```bash
python -m src.cli.main kb annotate [选项]
```

**选项**:
- `--template-id`（必需）: 模板UUID
- `--name`: 覆盖模板名称
- `--description`: 覆盖模板描述
- `--tags`: 逗号分隔的标签列表
- `--industries`: 逗号分隔的行业列表
- `--business-types`: 逗号分隔的业务类型列表
- `--kb-dir`: 知识库目录（本地后端）

**示例**:
```bash
# 更新模板标签和行业
python -m src.cli.main kb annotate \
    --template-id "550e8400-e29b-41d4-a716-446655440000" \
    --tags "web,high-availability,prod-ready" \
    --industries "retail,ecommerce"
```

**输出**:
```
Template metadata updated.
```

#### `kb suggest-links` - 查询资源关联关系

基于知识图谱统计，查询哪些资源类型经常与指定资源类型一起使用。

**用法**:
```bash
python -m src.cli.main kb suggest-links [选项]
```

**选项**:
- `--resource-type`（必需）: 资源类型，例如：`AWS::Lambda::Function`
- `--relation`: 关系类型，可选值：`depends_on`、`references`、`both`（默认：`both`）
- `--direction`: 方向，可选值：`out`（A->B）、`in`（X->A）、`both`（默认：`out`）
- `--industries`: 逗号分隔的行业过滤器
- `--business-types`: 逗号分隔的业务类型过滤器
- `--limit`: 最大建议数（默认：10）
- `--kb-dir`: 知识库目录（本地后端）

**示例**:
```bash
# 查询Lambda函数经常与哪些资源一起使用
python -m src.cli.main kb suggest-links \
    --resource-type "AWS::Lambda::Function" \
    --relation both \
    --limit 10

# 查询金融行业的资源关联
python -m src.cli.main kb suggest-links \
    --resource-type "AWS::RDS::DBInstance" \
    --industries "finance" \
    --business-types "payments"
```

**输出**:
```
┌─────────────────────────────────────────────────────┐
│    Most-likely connected resource types             │
├──────────────┬──────────────┬───────────┤
│ source_type │ target_type     │ count    │
├──────────────┼──────────────┼───────────┤
│ AWS::Lambda::Function │ AWS::DynamoDB::Table │ 45 │
│ AWS::Lambda::Function │ AWS::S3::Bucket │ 32 │
└──────────────┴──────────────┴───────────┘
```

#### `kb show-weights` - 显示排序权重

显示当前混合排序器的权重配置（用于模板检索排序）。

**用法**:
```bash
python -m src.cli.main kb show-weights [选项]
```

**选项**:
- `--kb-dir`: 知识库目录（用于本地权重文件）

**示例**:
```bash
python -m src.cli.main kb show-weights
```

**输出**:
```json
{
  "keyword_match": 0.3,
  "semantic_similarity": 0.4,
  "source_priority": 0.2,
  "usage_count": 0.1
}
```

#### `kb reset-weights` - 重置排序权重

将排序权重重置为默认值。

**用法**:
```bash
python -m src.cli.main kb reset-weights [选项]
```

**选项**:
- `--kb-dir`: 知识库目录（用于本地权重文件）

**示例**:
```bash
python -m src.cli.main kb reset-weights
```

**输出**:
```
Weights reset.
```

#### `kb feedback` - 提供反馈以学习权重

提供成对反馈（选择的模板 vs 拒绝的模板），用于在线学习排序权重。

**用法**:
```bash
python -m src.cli.main kb feedback [选项]
```

**选项**:
- `--chosen`（必需）: 被选择的模板UUID
- `--rejected`（必需）: 被拒绝的模板UUID
- `--query`（必需）: 原始用户描述
- `--kb-dir`: 知识库目录（用于本地权重文件）

**示例**:
```bash
python -m src.cli.main kb feedback \
    --chosen "550e8400-e29b-41d4-a716-446655440000" \
    --rejected "660e8400-e29b-41d4-a716-446655440001" \
    --query "我需要一个高可用的Web应用架构"
```

**输出**:
```
Weights updated.
{
  "keyword_match": 0.32,
  "semantic_similarity": 0.38,
  ...
}
```

### 命令速查表

| 命令 | 功能 | 必需参数 |
|------|------|----------|
| `chat` | 启动交互式对话 | 无 |
| `version` | 显示版本信息 | 无 |
| `kb ingest` | 导入模板到知识库 | `path` |
| `kb search` | 搜索模板 | `query` |
| `kb init-neo4j` | 初始化Neo4j数据库 | 无（需环境变量） |
| `kb validate-meta` | 验证元数据文件 | `meta_path` |
| `kb annotate` | 更新模板元数据 | `--template-id` |
| `kb suggest-links` | 查询资源关联关系 | `--resource-type` |
| `kb show-weights` | 显示排序权重 | 无 |
| `kb reset-weights` | 重置排序权重 | 无 |
| `kb feedback` | 提供反馈学习权重 | `--chosen`, `--rejected`, `--query` |

### 环境变量配置

不同命令可能需要不同的环境变量配置：

**通用配置**:
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GROQ_API_KEY`: LLM API密钥（`chat`命令需要）

**知识库配置**:
- `NEO4J_URI`: Neo4j连接URI（使用Neo4j后端时）
- `NEO4J_USER`: Neo4j用户名（可选，默认：`neo4j`）
- `NEO4J_PASSWORD`: Neo4j密码（使用Neo4j后端时）
- `NEO4J_DATABASE`: Neo4j数据库名称（可选）
- `SOLUTION_KB_DIR`: 本地知识库目录（默认：`.solution_kb`）

**存储配置**:
- `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`: MySQL配置（`chat`命令需要）
- `REDIS_HOST`, `REDIS_PORT`: Redis配置（可选，用于价格缓存）

### 使用技巧

1. **批量导入模板**: 使用 `kb ingest` 命令可以批量导入整个目录的模板，系统会自动扫描 `.yaml`、`.yml`、`.json` 文件。

2. **元数据标注**: 在模板文件同目录下创建 `kb.meta.yaml` 文件，导入时会自动合并元数据。

3. **会话恢复**: 使用 `chat --session-id` 可以恢复之前的对话，系统会保留30天的会话历史。

4. **多LLM支持**: 可以通过 `--llm` 选项切换不同的LLM提供商，适合测试和成本优化。

5. **知识图谱查询**: 使用 `kb suggest-links` 可以探索资源之间的关联关系，帮助理解常见架构模式。

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
│    - JSON知识库 + 关键词搜索                  │
│    - Milvus向量数据库 (RAG, 可选)            │
└─────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────┐
│     Solution Template KB / Knowledge Graph   │
│  (成熟模板知识库/Neo4j知识图谱 + 检索排序)     │
└─────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────┐
│         Storage Layer                        │
│  (存储层: MySQL + Redis)                      │
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
│   │   ├── solution_kb/                    # 成熟模板知识库/知识图谱（Neo4j）
│   │   │   ├── cfn_parser.py              # CloudFormation解析与抽取
│   │   │   ├── meta.py                    # 运营标注(kb.meta.yaml)解析与合并
│   │   │   ├── neo4j_store.py             # Neo4j图谱存储/检索
│   │   │   ├── store.py                   # 本地回退存储(JSONL)
│   │   │   ├── retriever.py               # 候选模板检索入口
│   │   │   ├── ranking.py                 # 混合排序(关键词+语义+同义词+来源优先级+权重学习)
│   │   │   ├── clarifier.py               # 候选差异驱动澄清提问
│   │   │   ├── embeddings.py              # 向量/语义相似度(可选OpenAI,兜底Hash)
│   │   │   └── synonyms.py                # 行业/业务同义词归一
│   │   │
│   │   └── aws_knowledge/                 # AWS知识库服务
│   │       ├── base.py                   # 知识库基础结构
│   │       ├── catalog.py                # 服务目录加载器（JSON + RAG支持）
│   │       ├── embedding.py              # 嵌入服务（RAG，生成向量）
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
│       │   ├── mysql.py                 # MySQL客户端包装
│       │   ├── redis.py                 # Redis客户端包装
│       │   └── milvus.py                # Milvus向量数据库客户端（RAG）
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
（可选）成熟模板候选差异澄清 (clarify_requirements) - KB驱动最少问题
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
2. **服务选择**: 
   - **RAG模式**（可选）: 使用Milvus向量数据库进行语义搜索，找到最相关的AWS服务
   - **传统模式**: 从AWS知识库使用关键词匹配服务
3. **配置生成**: 根据规模生成详细配置
4. **验证**: 使用Well-Architected Framework验证
5. **解释生成**: LLM生成推荐理由

#### 3.5 成熟模板知识库 / 知识图谱 (Solution Template KB / Knowledge Graph)

目标：把成熟的 CloudFormation /（未来 Terraform）模板抽取成图谱，优先复用成熟方案、参数与拓扑，再由LLM补齐解释与细节。

**核心入口**：
- `src/services/solution_kb/ingest.py`: 采集模板并入库（解析 + 运营标注合并 + 生成embedding）
- `src/services/solution_kb/neo4j_store.py`: Neo4j图谱存储与检索
- `src/services/solution_kb/retriever.py`: 候选模板检索（混合排序）
- `src/services/solution_kb/clarifier.py`: 候选差异驱动澄清提问（用户描述不完整时）

**Neo4j 环境变量**：
- `NEO4J_URI`
- `NEO4J_USER`（可选，默认 `neo4j`）
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`（可选）
- `SOLUTION_KB_BACKEND=neo4j`（可选；也可仅设置 `NEO4J_URI` 自动启用）

**运营标注（kb.meta.yaml）**：
在模板同目录放置 `kb.meta.yaml`（也支持 `.yml/.json`），入库时会自动合并标注到图谱中。

单模板模式示例：

```yaml
name: "电商高可用Web参考架构"
description: "ALB + EC2 + RDS，多可用区"
source: aws_quickstart
repository: "github.com/aws-quickstart/..."
tags: ["high-availability", "web", "prod-ready"]
industries: ["零售", "电商"]        # 会自动归一为 canonical token（如 retail）
business_types: ["ecommerce"]
```

多模板模式示例：

```yaml
default:
  source: aws_solutions
  tags: ["prod-ready"]
templates:
  - path: "a/template.yaml"
    name: "方案A"
    tags: ["web"]
  - path: "b/template.yaml"
    name: "方案B"
    industries: ["金融"]
```

**入库/校验/检索 CLI**：
- `aws-arch-agent kb validate-meta path/to/kb.meta.yaml`：校验运营标注文件
- `aws-arch-agent kb init-neo4j`：初始化 Neo4j 约束/索引（只需一次）
- `aws-arch-agent kb ingest <模板文件或目录> --source aws_quickstart --repo <repo标识> --include-body`：解析模板并刷入知识图谱（可选存储模板原文）
- `aws-arch-agent kb search "<关键词>" --limit 5`：检索模板
- `aws-arch-agent kb annotate --template-id <uuid> --tags "a,b" --industries "finance" --business-types "payments"`：事后补标/改标
- `aws-arch-agent kb export --template-id <uuid> --out ./out.yaml`：导出模板原文（若已存储或路径可访问）
- `aws-arch-agent kb recommend "<自然语言描述>" --no-clarify --export ./out`：基于自然语言查询推荐成熟模板并导出

**资源类型“最可能连接”统计**：
- `aws-arch-agent kb suggest-links --resource-type "AWS::Lambda::Function" --direction out|in|both --relation depends_on|references|both --industries "finance" --business-types "payments"`
- `aws-arch-agent kb suggest-next --resource-types "AWS::Lambda::Function,AWS::S3::Bucket" --direction both --relation both`：多资源类型的“下一图元”建议

**候选模板混合排序（关键词+语义+同义词+来源优先级）**：
- 关键词命中、资源类型命中
- 向量语义相似度（有 `OPENAI_API_KEY` 时使用 OpenAI embeddings；否则使用 HashEmbedding 兜底）
- 行业/业务同义词归一（如 “金融/银行/finance”→`finance`）
- 模板来源可信度优先级（QuickStart > Solutions > SAR > …）

**权重学习（可选）**：
- `aws-arch-agent kb show-weights`
- `aws-arch-agent kb reset-weights`
- `aws-arch-agent kb feedback --chosen <uuid> --rejected <uuid> --query "<用户描述>"`：成对反馈更新排序权重

**知识图谱三元组（当前已实现）**：
- 模板结构：
  - `(Template)-[:CONTAINS]->(Resource|Parameter|Output)`
- 资源拓扑：
  - `(Resource)-[:DEPENDS_ON]->(Resource)`
  - `(Resource)-[:REFERENCES]->(Resource|Parameter)`
- 运营标注：
  - `(Template)-[:HAS_TAG]->(Tag)`
  - `(Template)-[:HAS_INDUSTRY]->(Industry)`
  - `(Template)-[:HAS_BUSINESS_TYPE]->(BusinessType)`
**RAG功能**:
- 启用RAG后，系统使用向量嵌入进行语义搜索
- 支持自然语言查询，如"我需要一个数据库服务"会自动匹配RDS、DynamoDB等
- 提高服务推荐的准确性和相关性

#### 4. 价格计算服务 (Pricing Service)

**文件**: `src/services/pricing/calculator.py`

**数据流**:
```
服务配置
  ↓
检查Redis缓存 (L1)
  ↓ (未命中)
检查MySQL缓存 (L2)
  ↓ (未命中或过期)
调用AWS Pricing API
  ↓
更新缓存
  ↓
计算月成本
```

**特性**:
- 两级缓存（Redis + MySQL）
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

**MySQL表结构**:
- `conversations`: 会话表（主键: session_id）
- `messages`: 消息表（主键: message_id，索引: session_id + timestamp）
- `intents`: 意图表（主键: intent_id，索引: message_id）
- `user_requirements`: 用户需求表（主键: requirement_id，索引: session_id）
- `recommendations`: 推荐表（主键: recommendation_id，索引: session_id）

**MySQL存储**:
- 自动初始化：首次运行自动创建数据库和表
- JSON支持：使用MySQL JSON类型存储复杂数据
- 索引优化：为常用查询字段创建索引
- 30天TTL：会话自动过期清理

**Redis缓存**（可选）:
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
# 至少选择一个LLM提供商
OPENAI_API_KEY=sk-...
# 或
ANTHROPIC_API_KEY=sk-ant-...
# 或
GROQ_API_KEY=gsk-...
```

#### AWS配置（可选，用于Pricing API）

```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

#### 存储配置

```bash
# MySQL配置（必需，用于数据存储）
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=aws_arch_agent

# Redis配置（可选，用于价格缓存）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Milvus配置（可选，用于RAG向量搜索）
MILVUS_HOST=localhost
MILVUS_PORT=19530
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
- **repositories/**: 数据访问抽象层，封装MySQL操作
- **tools/**: MCP工具，用于LLM函数调用
- **utils/**: 工具类（存储、日志、指标、安全、合规）

### 关键设计决策

1. **LangGraph状态机**: 符合Constitution要求，支持状态转换审计
2. **多意图处理**: 单消息多意图，按优先级顺序处理
3. **两级缓存**: Redis (L1) + MySQL (L2) 确保价格查询性能
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

2. **MySQL连接失败**
   - 检查MySQL服务是否运行
   - 确认数据库用户权限
   - 检查连接配置（主机、端口、用户名、密码）
   - 程序会在首次运行时自动创建数据库和表

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
