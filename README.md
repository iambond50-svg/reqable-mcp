# Reqable MCP Server

一个 [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) 服务端，通过 [Reqable](https://reqable.com) 的本地 HTTP API 暴露 **143 个工具**，让 AI 助手能够控制抓包、配置规则、管理环境变量、操作 API 集合等。

Python 移植版，对标官方 [reqable-mcp-server](https://github.com/reqable/reqable-mcp-server)（Dart）。

## 它能做什么？

通过自然语言与 AI 助手对话，即可完成以下操作：

- **"开始抓包"** / **"停止抓包"** → 控制实时抓包引擎
- **"筛选出所有 500 的请求"** → 按状态码过滤实时记录
- **"创建一个断点，匹配 api.example.com"** → 创建断点规则
- **"把网关功能打开"** → 启用/禁用各类抓包功能
- **"当前激活的环境变量是哪个？"** → 查询和切换环境
- **"生成这条请求的 cURL 命令"** → 从抓包记录生成 cURL
- **"创建一个镜像规则把 api.test.com 转发到 api.prod.com"** → 配置镜像/重写/网关/脚本等规则

共 143 个工具，覆盖 Reqable 几乎全部功能。

## 工作原理

本项目通过 HTTP API 与正在运行的 Reqable 应用程序通信，**不直接访问数据库**。

```
AI 助手 → MCP 协议 (stdio) → reqable-mcp → HTTP API → Reqable 应用
```

Reqable 需处于运行状态，并开启本地 API 服务（默认 `127.0.0.1:9000`）。

## 前置要求

- Python 3.10+
- [Reqable](https://reqable.com) 已安装并运行
- 支持 MCP 的客户端（如 [Claude Desktop](https://claude.ai/download)、[Warp](https://www.warp.dev/) 等）

## 安装

```bash
git clone <repo-url>
cd reqable-mcp
pip install -e .
```

## 配置

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

### 自定义 Host / Port

如果 Reqable 的 API 端口非默认值，可通过参数指定：

```json
{
  "mcpServers": {
    "reqable": {
      "command": "python",
      "args": ["-m", "reqable_mcp", "--host", "127.0.0.1", "--port", "9000"],
      "cwd": "/path/to/reqable-mcp"
    }
  }
}
```

未指定端口时，会自动从 Reqable 配置文件读取 `proxyPort`。

## 提供的 MCP 工具（143 个）

### 实时抓包 Capture Live（8 个）

| 工具 | 说明 |
|------|------|
| `capture_live_status` | 查询抓包引擎状态 |
| `capture_live_set_enabled` | 启动/停止抓包 |
| `capture_live_filter` | 按条件筛选实时记录 |
| `capture_live_get_by_id` | 获取单条记录详情 |
| `capture_live_clear` | 清空所有实时记录 |
| `capture_live_generate_curl` | 生成 cURL 命令 |
| `capture_live_compose` | 将记录组合到新标签页 |
| `capture_live_collection_add` | 将记录添加到集合 |

### 文件夹式 CRUD 工具组（6 组 × 11 = 66 个）

每组包含：`get_config` / `set_enabled` / `list` / `set_item_enabled` / `get_by_id` / `create` / `create_folder` / `delete` / `delete_folder` / `update` / `update_folder_name`

| 功能组 | 工具前缀 | 说明 |
|--------|----------|------|
| 断点 | `capture_breakpoint_*` | 暂停匹配的请求/响应以便检查修改 |
| 网关 | `capture_gateway_*` | 流量控制：阻止/绕过/挂起 |
| 镜像 | `capture_mirror_*` | 将流量重定向到不同域名 |
| 重写 | `capture_rewrite_*` | 修改请求/响应内容 |
| 脚本 | `capture_script_*` | 自定义脚本处理流量 |
| 反向代理 | `capture_reverse_proxy_*` | 本地端口转发到远程主机 |

### 配置式 Profile 工具组（4 组 × 8 = 32 个）

每组包含：`get_config` / `set_enabled` / `get_active` / `lookup` / `select` / `create` / `delete` / `update`

| 功能组 | 工具前缀 | 说明 |
|--------|----------|------|
| SSL 代理 | `capture_ssl_proxying_*` | SSL/TLS 解密配置 |
| 网络限速 | `capture_network_throttling_*` | 模拟 2G/3G/4G/5G/WiFi 等网络 |
| 二级代理 | `capture_secondary_proxy_*` | 上游代理配置 |
| 访问控制 | `capture_access_control_*` | IP/域名访问黑白名单 |

### 环境变量 Environment（8 个）

| 工具 | 说明 |
|------|------|
| `environment_list` | 列出所有环境 |
| `environment_get_by_id` | 按 ID 获取环境 |
| `environment_get_active` | 获取当前激活的环境 |
| `environment_create` | 创建环境 |
| `environment_update` | 更新环境 |
| `environment_delete` | 删除环境 |
| `environment_select` | 切换激活环境 |
| `environment_builtin_variables` | 获取内置变量 |

### 集合 Collection（15 个）

集合、文件夹、API 的完整 CRUD 操作。

### REST 测试（5 个）

| 工具 | 说明 |
|------|------|
| `rest_http_create_from_url` | 从 URL 创建 HTTP 请求 |
| `rest_http_create_from_curl` | 从 cURL 命令创建 HTTP 请求 |
| `rest_http_update` | 更新 HTTP 请求 |
| `rest_websocket_create_from_url` | 从 URL 创建 WebSocket |
| `rest_websocket_update` | 更新 WebSocket |

### 脚本资源 & 上报服务器（9 个）

| 工具 | 说明 |
|------|------|
| `script_framework` | 获取脚本框架信息 |
| `script_template` | 获取脚本模板 |
| `capture_report_server_*` | 上报服务器配置（7 个） |

## 项目结构

```
reqable-mcp/
├── pyproject.toml
├── README.md
└── src/reqable_mcp/
    ├── __init__.py
    ├── __main__.py              # 入口点
    ├── server.py                # 主服务，注册全部 143 个工具
    ├── config.py                # 配置与端口自动检测
    ├── client.py                # Reqable HTTP API 客户端
    ├── utils.py                 # 结果构建与参数验证
    └── tools/
        ├── capture_live.py      # 实时抓包（8 工具）
        ├── folder_tools.py      # 文件夹式 CRUD 工厂（66 工具）
        ├── profile_tools.py     # 配置式 Profile 工厂（32 工具）
        ├── environment.py       # 环境变量（8 工具）
        ├── collection.py        # 集合管理（15 工具）
        ├── rest_http.py         # REST HTTP（3 工具）
        ├── rest_websocket.py    # REST WebSocket（2 工具）
        ├── script_resources.py  # 脚本资源（2 工具）
        └── report_server.py     # 上报服务器（7 工具）
```

## License

MIT
