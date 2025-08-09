> 注意：本项目 95% 的代码都由 AI 编写，没有完整审计过代码，只测试了基本功能，因此完全不可信。

# FeedSieve

智能RSS内容过滤系统 - 使用LLM智能筛选RSS订阅内容，并将有价值的文章自动保存到Readwise Reader。

## ✨ 功能特性

- 🤖 **智能内容过滤**: 基于自定义提示词，使用LLM智能判断内容价值
- 📡 **Webhook接收**: 接收RSS服务的webhook推送，实时处理新内容
- 🔄 **异步队列处理**: 基于SQLite的队列系统，一个一个处理内容，确保稳定性
- 📚 **Readwise集成**: 自动将有价值的内容发送到Readwise Reader保存
- 📊 **完整记录**: 记录所有处理结果（有用/无用/失败/跳过）
- 🔁 **重试机制**: 处理失败时自动重试，最多3次
- 📝 **分类日志**: 按功能模块分类记录日志，便于调试和监控

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Poetry（依赖管理）
- OpenRouter API密钥（LLM服务）
- Readwise Token（用于保存文章）

### 安装步骤

1. **克隆项目**:
   ```bash
   git clone <repository-url>
   cd feedsieve
   ```

2. **安装依赖**:
   ```bash
   poetry install
   ```

3. **配置敏感信息**:
   ```bash
   # 编辑配置文件，填入实际的API密钥
   nano config/secrets.yaml
   ```

4. **启动服务**:
   ```bash
   poetry run python main.py
   ```

5. **验证服务**:
   ```bash
   # 服务启动后，应该看到以下输出：
   # INFO - 正在启动 FeedSieve...
   # INFO - 数据库表创建成功
   # INFO - FeedSieve 启动完成
   # INFO - Application startup complete.
   ```

## ⚙️ 配置

### 配置文件结构

项目使用双文件配置：

- **`config/config.yaml`** - 非敏感配置（提示词、数据库等）
- **`config/secrets.yaml`** - 敏感配置（API密钥、密码等）

### 敏感信息配置

编辑 `config/secrets.yaml`:

```yaml
# 认证配置（目前已移除认证功能）
auth:
  username: "${FEEDSIEVE_USERNAME:-admin}"
  password: "${FEEDSIEVE_PASSWORD:-change_me}"

# API密钥配置
api:
  openrouter_key: "${OPENROUTER_API_KEY:-your_openrouter_key_here}"
  readwise_token: "${READWISE_TOKEN:-your_readwise_token_here}"
```

### 环境变量（推荐生产环境）

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
export READWISE_TOKEN="your_readwise_token"
export FEEDSIEVE_USERNAME="admin"
export FEEDSIEVE_PASSWORD="secure_password"
```

### Feed过滤配置

在 `config/config.yaml` 中为每个feed源配置专门的过滤提示词：

```yaml
prompts:
  - site: ["rsshub://hackernews"]
    prompt: |
      你是Hacker News内容过滤器...

  - site: ["https://www.v2ex.com/index.xml"]
    prompt: |
      你是V2EX内容过滤器...
```

## 🔧 API使用

### Webhook接口

**接收内容webhook**:
```http
POST /api/webhook/053e46c8c41a4de199c4
Content-Type: application/json

{
  "entry": {
    "title": "文章标题",
    "content": "文章内容",
    "url": "https://example.com/article"
  },
  "feed": {
    "title": "Feed名称",
    "url": "rsshub://hackernews",
    "siteUrl": "https://news.ycombinator.com"
  },
  "view": 1
}
```

**响应格式**:
```json
{
  "success": true,
  "message": "Webhook 处理成功",
  "data": {
    "queue_id": 123,
    "feed_url": "rsshub://hackernews"
  }
}
```

## 📊 处理流程

```
1. Webhook接收 → 验证数据 → 存入Queue表
         ↓
2. 后台处理 → 获取Queue数据 → 匹配Prompt
         ↓
3. LLM判断 → 生成过滤结果
         ↓
4. 结果处理:
   - USEFUL: 发送到Readwise → Records表
   - USELESS: 被过滤 → Records表
   - SKIP: 无prompt → Records表
   - FAILED: 处理失败 → Records表（重试机制）
         ↓
5. 清理 → 删除Queue表数据
```

## 📁 项目结构

```
feedsieve/
├── app/
│   ├── core/              # 核心组件
│   │   ├── config.py      # 配置管理
│   │   ├── constants.py   # 常量定义
│   │   ├── database.py    # 数据库管理
│   │   ├── logging.py     # 日志配置
│   │   └── settings.py    # 设置模型
│   ├── models/            # 数据模型
│   │   ├── database.py    # SQLAlchemy模型
│   │   └── schemas.py     # Pydantic模型
│   ├── services/          # 业务服务
│   │   ├── queue_service.py    # 队列处理服务
│   │   ├── record_service.py   # 记录管理服务
│   │   ├── llm_service.py      # LLM调用服务
│   │   └── readwise_service.py # Readwise集成服务
│   ├── repositories/      # 数据访问层
│   │   ├── queue_repository.py   # 队列数据访问
│   │   └── record_repository.py  # 记录数据访问
│   ├── controllers/       # 控制器
│   │   └── webhook_controller.py # Webhook处理
│   └── middleware/        # 中间件
├── config/               # 配置文件
│   ├── config.yaml      # 主配置
│   ├── secrets.yaml     # 敏感配置
├── data/                # 数据目录
│   ├── feedsieve.db     # SQLite数据库
│   └── *.log           # 各种日志文件
├── main.py             # 应用入口
└── pyproject.toml      # Poetry配置
```

## 📝 日志系统

系统按功能模块生成分类日志：

```bash
data/
├── feedsieve.log      # 主应用日志
├── error.log          # 错误日志
├── webhook.log        # Webhook接收日志
├── queue.log          # 队列处理日志
├── llm.log            # LLM调用日志
└── readwise.log       # Readwise保存日志
```

### 实时监控日志
```bash
# 监控特定功能日志
tail -f data/webhook.log    # Webhook接收
tail -f data/queue.log      # 队列处理
tail -f data/llm.log        # LLM过滤
tail -f data/readwise.log   # Readwise保存
```

## 💾 数据库

### 表结构

**Queue表** (临时数据):
- 存储接收到的webhook数据
- 处理完成后自动删除
- 支持重试机制

**Records表** (永久记录):
- 记录所有处理结果
- 状态：useful/useless/failed/skip
- 包含错误信息和LLM判断结果

### 数据库查询
```bash
# 查看队列状态
sqlite3 data/feedsieve.db "SELECT * FROM queue;"

# 查看处理记录
sqlite3 data/feedsieve.db "
SELECT id, status, title, feed_url, created_at
FROM records
ORDER BY created_at DESC
LIMIT 10;
"

# 查看统计信息
sqlite3 data/feedsieve.db "
SELECT status, COUNT(*) as count
FROM records
GROUP BY status;
"
```

## 🔍 故障排除

### 常见问题

1. **连接失败**:
   ```bash
   # 检查服务状态
   curl -I http://localhost:8000/api/webhook/053e46c8c41a4de199c4
   # 检查端口占用
   lsof -i :8000
   ```

2. **API密钥错误**:
   - 检查 `config/secrets.yaml` 配置
   - 查看 `data/llm.log` 获取详细错误

3. **配置文件问题**:
   ```bash
   # 验证配置语法
   poetry run python -c "
   from app.core.config import config
   print('配置加载成功:', len(config.get_prompts()), '个feed源')
   "
   ```

4. **数据库问题**:
   ```bash
   # 重建数据库
   rm data/feedsieve.db
   poetry run python main.py  # 会自动重建表
   ```

### 调试

修改 `config/config.yaml` 中的日志级别：
```yaml
logging:
  level: "DEBUG"  # 改为DEBUG查看详细日志
```
