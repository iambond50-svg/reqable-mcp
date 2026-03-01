# Reqable Capture Reader MCP Server

读取 [Reqable](https://reqable.com) 抓包工具的本地数据，通过 MCP 协议供 AI 助手查询和分析。

## 安装

```bash
pip install -e .
```

## MCP 配置

在 Warp（或其他 MCP 客户端）中添加：

```json
{
  "mcpServers": {
    "reqable": {
      "command": "python",
      "args": ["-m", "reqable_mcp"],
      "cwd": "C:\\Users\\nicl\\Desktop\\reqable-mcp"
    }
  }
}
```

## 工具列表

| 工具 | 说明 |
|------|------|
| `list_captures` | 列出抓包记录，支持按 host/method/code/app/keyword 筛选，分页 |
| `get_capture_detail` | 获取单条抓包的完整详情（请求头、响应头、TLS、应用信息） |
| `get_capture_body` | 获取请求或响应体内容，支持大小限制 |
| `get_capture_stats` | 统计所有抓包记录（按域名、方法、状态码、应用分组） |
| `list_api_tests` | 列出 REST API 测试记录 |
| `get_api_test_detail` | 获取单条 API 测试的完整详情 |

## 项目结构

```
reqable-mcp/
├── pyproject.toml
├── README.md
└── src/reqable_mcp/
    ├── __init__.py
    ├── __main__.py      # 入口点
    ├── server.py        # MCP 工具定义
    ├── db.py            # LMDB 只读访问层
    └── models.py        # 数据解析与格式化
```
