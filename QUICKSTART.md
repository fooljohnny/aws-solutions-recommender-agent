# 快速启动指南 / Quick Start Guide

## 运行程序前的准备

### 1. 配置环境变量

创建 `.env` 文件（如果还没有）：

```bash
# Windows PowerShell
New-Item -ItemType File -Path .env

# Linux/Mac
touch .env
```

在 `.env` 文件中添加以下配置（至少需要LLM API密钥之一）：

```bash
# LLM配置（必需，至少选择一个）
OPENAI_API_KEY=your_openai_api_key_here
# 或
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# 或
GROQ_API_KEY=your_groq_api_key_here

# AWS配置（可选，用于Pricing API）
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key

# MySQL配置（必需，用于数据存储）
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=aws_arch_agent

# Redis配置（可选，用于价格缓存）
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 2. 运行CLI程序

#### 方式一：启动新会话

```bash
python -m src.cli.main chat
```

#### 方式二：指定LLM提供商

```bash
# 使用OpenAI
python -m src.cli.main chat --llm openai

# 使用Anthropic
python -m src.cli.main chat --llm anthropic

# 使用Groq
python -m src.cli.main chat --llm groq
```

#### 方式三：恢复已有会话

```bash
python -m src.cli.main chat --session-id <your-session-id>
```

### 3. 运行API服务器（可选）

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

然后访问：
- Swagger UI: http://localhost:8000/docs
- API文档: http://localhost:8000/redoc

## 使用示例

启动CLI后，您可以输入中文需求：

```
You: 我需要一个能处理1000用户的Web应用架构

[Processing...]

Agent: 根据您的需求，我为您推荐以下AWS架构方案...
```

## 注意事项

1. **首次运行**：程序会自动创建MySQL数据库和表（如果不存在），确保MySQL服务正在运行
2. **API密钥**：必须配置OPENAI_API_KEY、ANTHROPIC_API_KEY或GROQ_API_KEY之一才能使用
3. **存储服务**：
   - MySQL是必需的，用于存储会话、消息、意图等数据
   - Redis是可选的，用于价格缓存（未配置时价格查询功能仍可用）
4. **错误处理**：如果遇到错误，程序会显示详细的错误信息

## 故障排除

### 问题：ModuleNotFoundError
**解决**：运行 `pip install -r requirements.txt`

### 问题：API密钥错误
**解决**：检查 `.env` 文件中的API密钥是否正确设置

### 问题：MySQL连接失败
**解决**：
- 确保MySQL服务正在运行
- 检查`.env`文件中的MySQL配置是否正确
- 确认数据库用户有创建数据库和表的权限
- 检查防火墙设置，确保端口3306可访问

### 问题：数据库表不存在
**解决**：程序会在首次运行时自动创建数据库和表。如果表不存在，检查：
- MySQL用户是否有CREATE DATABASE和CREATE TABLE权限
- 数据库连接是否正常
- 查看程序日志中的错误信息

### 问题：Redis连接失败
**解决**：Redis是可选的，程序会继续运行但价格缓存功能受限。如果不需要价格缓存，可以忽略此错误

### 问题：Milvus连接失败
**解决**：
- Milvus是可选的，用于RAG向量搜索功能
- 如果未配置Milvus，系统会自动使用关键词搜索
- 要启用RAG功能，需要：
  1. 安装并运行Milvus服务
  2. 在`.env`中配置`MILVUS_HOST`和`MILVUS_PORT`
  3. 配置`OPENAI_API_KEY`用于生成embeddings
  4. 在代码中初始化`AWSServiceCatalog`时设置`use_rag=True`

