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

### 代理配置

系统支持HTTP和SOCKS5代理，在 `config/secrets.yaml` 中配置：

```yaml
# 代理配置
proxy:
  type: "http"  # 或 "socks5"
  url: "http://proxy:port"  # 或 "socks5://proxy:port"
```

**支持的代理类型**:
- **HTTP代理**: 适用于大多数网络环境，配置简单
- **SOCKS5代理**: 支持更多协议，需要安装PySocks依赖

### 队列处理配置

在 `config/config.yaml` 中配置队列处理参数：

```yaml
queue:
  retry_times: 3                           # 重试次数
  dead_letter_retry_daily: true            # 是否每日重试死信
  process_interval_seconds: 300            # 队列处理间隔（秒）
```

**队列处理间隔说明**:
- **默认值**: 300秒（5分钟）
- **最小值**: 60秒（1分钟）
- **建议值**: 300-600秒（5-10分钟），避免LLM API限流
- **调整建议**: 根据LLM服务商的限流策略调整，避免触发频率限制

### Feed过滤配置

在 `config/config.yaml` 中为每个feed源配置专门的过滤提示词和内容抓取策略：

```yaml
prompts:
  - site: ["rsshub://hackernews"]
    refetch_content: true  # 是否重新抓取网页内容
    prompt: |
      你是Hacker News内容过滤器...

  - site: ["https://www.v2ex.com/index.xml"]
    refetch_content: false  # 使用RSS原始内容，不重新抓取
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
2. 后台处理 → 获取Queue数据 → 匹配Prompt配置
         ↓
3. 内容处理策略:
   - refetch_content: true → 重新抓取网页内容（使用trafilatura）
   - refetch_content: false → 使用RSS原始内容
         ↓
4. 智能内容截断 → 保留前2500字符和后1000字符
         ↓
5. LLM判断 → 生成过滤结果
         ↓
6. 结果处理:
   - USEFUL: 发送到Readwise → Records表
   - USELESS: 被过滤 → Records表
   - SKIP: 无prompt → Records表
   - FAILED: 处理失败 → Records表（重试机制）
         ↓
7. 清理 → 删除Queue表数据
```

### 内容抓取配置

每个feed源可以独立配置是否重新抓取网页内容：

- **`refetch_content: true`**: 系统会访问原文链接，使用trafilatura库解析网页，提取纯文本内容
- **`refetch_content: false`**: 系统直接使用RSS feed中的原始内容

**优势对比**:
- **重新抓取**: 获得完整、干净的网页内容，避免RSS摘要截断问题
- **使用原始内容**: 处理速度更快，减少网络请求，适合内容质量较高的RSS源

### 内容智能截断

系统会自动对长文章进行智能截断处理，确保LLM能获得关键信息：

- **截断策略**: 保留文章前2500字符和最后1000字符
- **智能调整**: 根据文章长度自动调整截断参数
- **阈值设置**: 3500字符以下不截断，超过则智能截断
- **信息保留**: 优先保留文章开头和结尾，确保核心内容不丢失

**截断示例**:
```
原始文章: 8000字符
截断后: 前2500字符 + [截断提示] + 后1000字符 = 约3537字符
压缩率: 55.8%
```

### Readwise集成

系统会将有价值的文章保存到Readwise Reader：

- **只传递文章URL**，让Readwise自动抓取和解析内容
- 不传递标题、摘要、作者或HTML内容
- 自动分类到"feed"位置，便于后续阅读和管理
- 利用Readwise的智能内容解析能力，获得最佳阅读体验

**集成优势**:
- **内容质量**: Readwise专门优化的内容解析，去除广告和无关元素
- **阅读体验**: 自动生成目录、高亮重要内容、支持多种阅读模式
- **同步管理**: 与Readwise生态系统无缝集成，支持多设备同步

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
│   │   ├── queue_service.py         # 队列处理服务
│   │   ├── record_service.py        # 记录管理服务
│   │   ├── llm_service.py           # LLM调用服务
│   │   ├── readwise_service.py      # Readwise集成服务
│   │   └── content_fetcher_service.py # 网页内容抓取服务
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
