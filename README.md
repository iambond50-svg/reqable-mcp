# Reqable Capture Reader MCP Server

一个 [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) 服务端，用于读取 [Reqable](https://reqable.com) 抓包工具的本地数据，让 AI 助手能够直接查询、筛选和分析你的 HTTP 抓包记录。

## 它能做什么？

通过自然语言与 AI 助手对话，即可完成以下操作：

- **“列出所有访问 api.example.com 的请求”** → 按域名筛选抓包记录
- **“最近那条 POST 请求返回了什么？”** → 查看响应体内容
- **“统计一下各个域名的请求量”** → 获取聚合统计
- **“看看状态码 500 的请求都有哪些”** → 按状态码筛选定位问题
- **“那条请求的请求头是什么？”** → 查看完整请求/响应头、TLS 信息

无需手动翻找 Reqable 界面，AI 帮你直接从数据库中检索。

## 工作原理

Reqable 使用 ObjectBox（基于 LMDB）存储抓包数据，本项目以只读模式直接读取该数据库，**不会修改任何数据**，且 Reqable 运行时也可安全读取。

```
Reqable 抓包 → LMDB 数据库 → reqable-mcp (只读) → MCP 协议 → AI 助手
```

## 前置要求

- Python 3.10+
- [Reqable](https://reqable.com) 已安装并有抓包记录
- 支持 MCP 的客户端（如 [Warp](https://www.warp.dev/)、Claude Desktop 等）

## 安装

```bash
git clone https://github.com/iambond50-svg/reqable-mcp.git
cd reqable-mcp
pip install -e .
```

## 配置

### Warp

在 Warp 的 MCP 设置中添加：

```json
{
  "mcpServers": {
    "reqable": {
      "command": "python",
      "args": ["-m", "reqable_mcp"],
      "cwd": "/path/to/reqable-mcp"
    }
  }
}
```

### Claude Desktop

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "reqable": {
      "command": "python",
      "args": ["-m", "reqable_mcp"],
      "cwd": "/path/to/reqable-mcp"
    }
  }
}
```

> 将 `/path/to/reqable-mcp` 替换为实际项目路径。

## 提供的 MCP 工具

### 抓包记录（Proxy Capture）

| 工具 | 说明 |
|------|------|
| `list_captures` | 列出抓包记录，支持按 host / method / status code / app / keyword 筛选，分页返回 |
| `get_capture_detail` | 获取单条抓包的完整详情：请求头、响应头、TLS 握手信息、应用信息、时间戳 |
| `get_capture_body` | 读取请求体或响应体内容，支持大小限制（默认 4KB，最大 64KB） |
| `get_capture_stats` | 聚合统计：按域名、HTTP 方法、状态码、应用名称分组计数 |

### API 测试记录（REST Client）

| 工具 | 说明 |
|------|------|
| `list_api_tests` | 列出 Reqable REST 客户端的 API 测试记录，支持关键词搜索 |
| `get_api_test_detail` | 获取单条 API 测试的完整请求与响应详情 |

## 安全性

- **只读访问**：以 `readonly=True, lock=False` 模式打开 LMDB，不会写入或修改任何数据
- **Body 大小限制**：默认最大返回 4KB 响应体，防止大文件撑爆上下文，可调至最大 64KB
- **分页保护**：列表默认返回 20 条，最大 100 条，避免一次性加载过多数据

## 数据位置

Reqable 默认数据目录：

- **Windows**: `%APPDATA%\\Reqable\\`
- **macOS**: `~/Library/Application Support/Reqable/`

本项目会自动检测默认路径，无需手动配置。

## 项目结构

```
reqable-mcp/
├── pyproject.toml           # 项目配置与依赖
├── README.md
├── .gitignore
└── src/reqable_mcp/
    ├── __init__.py
    ├── __main__.py           # 入口点 (python -m reqable_mcp)
    ├── server.py             # MCP 工具定义（6 个工具）
    ├── db.py                 # LMDB 只读访问层
    └── models.py             # 数据解析与格式化
```

## License

MIT
