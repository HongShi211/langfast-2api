# 🚀 langfast-2api：你的私人 AI 万能转换器 🚀

<div align="center">

[![Apache 2.0 License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![GitHub Repo stars](https://img.shields.io/github/stars/lzA6/langfast-2api?style=social)
![Docker Ready](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)
![Python Version](https://img.shields.io/badge/Python-3.10+-blue?logo=python)

**中文** | [English](README_EN.md) 📖

> "我们站在巨人的肩膀上，是为了看得更远，而不是为了成为巨人脚下的阴影。这个项目，就是让你把任何强大的 AI 服务，都变成你自己的'巨人'。"

[![快速开始](https://img.shields.io/badge/快速开始-部署指南-brightgreen?style=for-the-badge)](##-一键部署指南)
[![在线演示](https://img.shields.io/badge/在线演示-立即体验-orange?style=for-the-badge)](##-使用示例)

</div>

## 📖 目录
- [项目概述](#-项目概述)
- [核心特性](#-核心特性)
- [系统架构](#-系统架构)
- [一键部署指南](#-一键部署指南)
- [使用示例](#-使用示例)
- [技术原理](#-技术原理)
- [开发路线图](#-开发路线图)
- [项目结构](#-项目结构)
- [开源协议](#-开源协议)

## 🌟 项目概述

`langfast-2api` 是一个轻量级高性能代理服务，核心使命是将 **[langfast](https://langfa.st)** 原生接口无缝转换为完全兼容 **OpenAI API** 的格式。

🔗 **仓库地址**: [https://github.com/lzA6/langfast-2api](https://github.com/lzA6/langfast-2api)

### 解决的问题
- 🎯 **兼容性痛点**：你的工具只支持 OpenAI API，但想使用 langfast 的强大模型
- ⚡ **无缝切换**：无需修改现有代码，直接接入 langfast 服务
- 🔄 **标准接口**：为所有支持 OpenAI 的应用程序提供统一接入点

## ✨ 核心特性

| 特性 | 描述 | 状态 |
|------|------|------|
| 🌍 **万能转换** | 将 langfast 接口转换为标准 OpenAI API | ✅ 已实现 |
| 🚀 **高性能** | 基于 FastAPI + Uvicorn 的异步架构 | ✅ 已实现 |
| 💬 **双模支持** | 同时支持流式和非流式响应 | ✅ 已实现 |
| 🔐 **智能认证** | 动态凭证池管理与自动维护 | ✅ 已实现 |
| 🐳 **容器化** | Docker 一键部署，开箱即用 | ✅ 已实现 |
| 📊 **模型列表** | 提供完整的 `/v1/models` 接口 | ✅ 已实现 |

## 🏗️ 系统架构

### 整体架构图

```mermaid
graph TB
    subgraph "客户端应用"
        A[NextChat] --> B[API 请求]
        C[LobeChat] --> B
        D[Python SDK] --> B
        E[自定义应用] --> B
    end
    
    subgraph "langfast-2api 网关"
        F[Nginx 反向代理] --> G[FastAPI 应用]
        G --> H{身份验证}
        H -->|通过| I[LangfastProvider]
        I --> J[CredentialManager]
        I --> K[SocketIOManager]
    end
    
    subgraph "上游服务"
        L[langfast.st API] --> M[WebSocket 连接]
        J --> N[匿名凭证池]
    end
    
    B --> F
    K --> M
    I --> L
    
    style A fill:#e1f5fe
    style C fill:#e1f5fe
    style D fill:#e1f5fe
    style E fill:#e1f5fe
    style F fill:#fff3e0
    style G fill:#fff3e0
    style I fill:#f3e5f5
    style J fill:#e8f5e8
    style K fill:#fff8e1
```

### 组件职责说明

| 组件 | 图标 | 职责描述 | 技术栈 |
|------|------|-----------|---------|
| **Nginx** | 🚪 | 反向代理、负载均衡、流式优化 | Nginx |
| **FastAPI** | 🎯 | Web 框架、请求路由、身份验证 | FastAPI, Uvicorn |
| **LangfastProvider** | 🧠 | 业务逻辑核心、协议转换 | Python, asyncio |
| **CredentialManager** | 🔑 | 动态凭证池管理、自动注册 | aiohttp |
| **SocketIOManager** | 📡 | WebSocket 通信、实时数据流 | socket.io |

## 🚀 一键部署指南

### 环境要求
- 🐳 **Docker** & **Docker Compose**
- 💻 至少 1GB 可用内存
- 🌐 网络连接（用于访问 langfast.st）

### 三步快速部署

#### 步骤 1：克隆项目
```bash
git clone https://github.com/lzA6/langfast-2api.git
cd langfast-2api
```

#### 步骤 2：配置环境
```bash
cp .env.example .env
# 编辑 .env 文件，修改 API_MASTER_KEY
```

**配置文件示例** (`/.env`)：
```env
# API 主密钥 - 请修改为复杂的自定义密钥
API_MASTER_KEY=sk-your-super-secure-key-here-12345

# 服务配置
HOST=0.0.0.0
PORT=8088

# 凭证池配置
MIN_CREDENTIALS=3
MAX_CREDENTIALS=10
```

#### 步骤 3：启动服务
```bash
docker-compose up -d
```

**验证服务状态**：
```bash
docker-compose ps
# 应该看到 app 和 nginx 服务都在运行状态
```

### 服务访问
- 🌐 **API 端点**: `http://localhost:8088/v1`
- 🔍 **健康检查**: `http://localhost:8088/health`
- 📚 **API 文档**: `http://localhost:8088/docs`

## 💡 使用示例

### 客户端配置

#### 1. NextChat / LobeChat 配置
```yaml
API 地址: http://localhost:8088/v1
API 密钥: Bearer sk-your-super-secure-key-here-12345
模型: gpt-4o-mini  # 或任何 langfast 支持的模型
```

#### 2. Python 代码示例
```python
import openai

# 配置客户端
client = openai.OpenAI(
    base_url="http://localhost:8088/v1",
    api_key="Bearer sk-your-super-secure-key-here-12345"
)

# 流式聊天
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "你好，请介绍一下你自己"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

#### 3. cURL 示例
```bash
curl http://localhost:8088/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-super-secure-key-here-12345" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

## 🔧 技术原理

### 核心工作流程

```mermaid
sequenceDiagram
    participant C as Client
    participant N as Nginx
    participant F as FastAPI
    participant L as LangfastProvider
    participant CM as CredentialManager
    participant SM as SocketIOManager
    participant LS as langfast.st

    C->>N: 发送 OpenAI 格式请求
    N->>F: 代理请求
    F->>F: 验证 API Key
    F->>L: 处理业务逻辑
    
    L->>CM: 获取访问凭证
    CM->>L: 返回 access_token
    
    L->>SM: 创建 SocketIO 连接
    SM->>LS: 建立 WebSocket 连接
    
    L->>LS: 触发任务执行
    LS->>SM: 流式返回数据块
    SM->>L: 推送至消息队列
    L->>F: 转换为 OpenAI 格式
    F->>N: 流式响应
    N->>C: 实时返回数据
```

### 关键技术实现

#### 1. 协议转换引擎 (`/app/providers/langfast_provider.py`)
```python
async def chat_completion(self, request_data: dict):
    """核心转换方法：将 OpenAI 请求转换为 langfast 格式"""
    if request_data.get("stream", False):
        return await self._stream_generator(request_data)
    else:
        return await self._collect_full_response(request_data)

async def _stream_generator(self, request_data: dict):
    """流式响应生成器 - 实现打字机效果"""
    async for content_chunk in self._receive_stream_data():
        # 计算增量内容，优化带宽使用
        delta_content = content_chunk[len(self.last_content):]
        yield self._format_openai_chunk(delta_content)
```

#### 2. 智能凭证管理 (`/app/services/credential_manager.py`)
```python
async def maintain_credentials(self):
    """自动维护凭证池，确保始终有可用凭证"""
    while True:
        await asyncio.sleep(60)  # 每分钟检查一次
        
        async with self._lock:
            if len(self._credentials) < self.min_credentials:
                await self._replenish_credentials()
```

#### 3. 实时通信管理 (`/app/services/socketio_manager.py`)
```python
@sio.on('execution:chunk')
async def on_execution_chunk(data):
    """监听 langfast 的实时数据流"""
    content = data.get('content', '')
    await self.message_queue.put(content)
```

## 🗺️ 开发路线图

### ✅ 已实现功能
- [x] 核心代理与协议转换
- [x] 流式/非流式双模支持
- [x] 动态凭证池管理
- [x] 模型列表接口
- [x] Docker 容器化部署
- [x] 基础安全认证

### 🚧 进行中功能
- [ ] Token 使用统计 (`usage` 字段)
- [ ] 精细化错误处理与传递
- [ ] 凭证有效性自动验证

### 📅 规划中功能
- [ ] 多上游服务支持（AI 服务网关）
- [ ] 请求缓存与性能优化
- [ ] 可视化监控面板
- [ ] 负载均衡与水平扩展
- [ ] 速率限制与配额管理

### 功能优先级矩阵

```mermaid
quadrantChart
    title 功能开发优先级矩阵
    x-axis "实现复杂度" --> "高"
    y-axis "业务价值" --> "高"
    "Token统计": [0.7, 0.9]
    "错误处理": [0.5, 0.7]
    "凭证验证": [0.4, 0.6]
    "多上游支持": [0.8, 0.8]
    "请求缓存": [0.6, 0.5]
    "监控面板": [0.7, 0.4]
```

## 📂 项目结构

```
langfast-2api/
├── 🐳 Docker 相关文件
│   ├── Dockerfile              # 应用容器构建
│   └── docker-compose.yml      # 服务编排配置
├── 🔧 配置文件
│   ├── .env.example           # 环境配置模板
│   ├── nginx.conf             # Nginx 配置
│   └── requirements.txt       # Python 依赖
├── 🎯 应用入口
│   └── main.py                # FastAPI 主应用
└── 📁 核心代码 (app/)
    ├── core/                  # 核心配置
    │   ├── config.py          # Pydantic 配置模型
    │   └── __init__.py
    ├── providers/             # 业务逻辑提供者
    │   ├── base_provider.py   # 提供者基类
    │   ├── langfast_provider.py # Langfast 协议转换
    │   └── __init__.py
    ├── services/              # 后端服务
    │   ├── credential_manager.py # 凭证池管理
    │   ├── socketio_manager.py   # SocketIO 管理
    │   └── __init__.py
    └── utils/                 # 工具函数
        ├── sse_utils.py       # SSE 响应工具
        └── __init__.py
```

## 📜 开源协议

本项目采用 **Apache License 2.0** 开源协议。

### 主要条款
- ✅ **允许**：商业使用、修改、分发、专利授权
- ✅ **要求**：保留版权声明、变更说明
- ❌ **不提供**：商标授权、责任担保
- ❌ **禁止**：使用项目名称进行背书

### 完整协议
请查看 [LICENSE](LICENSE) 文件获取完整条款，或访问 [Apache 2.0 协议官网](https://www.apache.org/licenses/LICENSE-2.0)。

---

<div align="center">

## 💝 感谢使用

如果这个项目对你有帮助，请给我们一个 ⭐️ 支持！

**快乐编码！** 🎉

[![Star History Chart](https://api.star-history.com/svg?repos=lzA6/langfast-2api&type=Date)](https://star-history.com/#lzA6/langfast-2api&Date)

</div>

---

*最后更新: ${new Date().toLocaleDateString('zh-CN')}*
