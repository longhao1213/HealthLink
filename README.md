# HealthLink (瑶光 · 智能医疗助手)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Framework-FastAPI-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/AI-LangChain-purple.svg" alt="LangChain">
  <img src="https://img.shields.io/badge/Vector_DB-Milvus-orange.svg" alt="Milvus">
  <img src="https://img.shields.io/badge/License-MIT-lightgrey.svg" alt="License">
</p>

**HealthLink** 是一个基于大型语言模型（LLM）和检索增强生成（RAG）技术构建的智能医疗健康助手。项目主角名为 **瑶光（YaoGuang）**，其形象被设定为一位富有同情心、知识渊博且值得信赖的AI医生，旨在为用户提供一个安全、私密的健康咨询环境。

此项目不仅是一个功能性应用，更是一个端到端的AI工程实践展示，涵盖了从需求分析、技术选型、全栈开发到容器化部署的完整软件生命周期。

## ✨ 核心功能

- **智能对话与咨询**: 基于LLM提供通用的健康知识问答。
- **私有知识库问答 (RAG)**: 结合存储在 **Milvus** 向量数据库中的专业医疗文档（如中医典籍、临床指南），提供更精准、更具上下文的回答。
- **个人报告解读**: 支持用户上传自己的病例、化验单等文件，AI能够进行临时解析和解读。
- **长期个性化记忆**: 为不同用户维护独立的对话历史和健康摘要，提供个性化服务。
- **知识库管理**: 提供API接口，支持对私有知识库文档（PDF, DOCX, TXT等）的上传、向量化处理和管理。
- **流式响应**: 对话接口支持流式输出，提升用户交互体验。

## 🏛️ 技术架构

HealthLink 采用现代化的微服务架构，将数据、模型和应用逻辑解耦，以实现高可扩展性和可维护性。

<p align="center">
  <img src="https://raw.githubusercontent.com/mubai-creator/image-hosting/main/20240725160058.png" alt="Architecture Diagram" width="800"/>
</p>

### 技术栈详情

- **后端框架**: **FastAPI**
  - 用于构建高性能、异步的API服务，并利用其特性自动生成交互式API文档 (Swagger UI & ReDoc)。

- **AI 编排框架**: **LangChain**
  - 作为整个AI应用的核心，负责：
    - **Agent构建**: 创建能够思考和使用工具的智能代理。
    - **RAG流程**: 实现“检索-增强-生成”的完整流程。
    - **Prompt管理**: 集中管理和编排复杂的提示词工程。
    - **工具集成**: 将知识库检索等能力封装为Agent可调用的工具。

- **大语言模型 (LLM)**:
  - 采用可插拔设计，通过 `langchain-openai`, `langchain-alibaba` 等库，灵活支持 **OpenAI GPT系列**, **阿里通义千问** 等多种模型。

- **数据存储**:
  - **关系型数据库 (MySQL)**: 使用 **SQLModel** 作为ORM，存储用户、聊天记录、文件元数据等结构化数据。
  - **向量数据库 (Milvus)**: 存储知识文档和用户记忆的向量数据，是实现高效RAG检索的关键。
  - **对象存储 (MinIO)**: 存储所有用户上传的原始文件（如PDF、图片），实现文件与应用服务的解耦。
  - **缓存数据库 (Redis)**: 用于缓存高频数据，提升系统性能。

- **部署与运维**:
  - **容器化**: **Docker** & **Docker Compose**
    - 将所有服务（FastAPI应用, MySQL, Milvus, MinIO, Redis）容器化，实现环境隔离和一致性。
  - **服务器管理**: 可配合 **1Panel** 等面板，通过 Docker Compose 实现一键部署和图形化管理。

- **依赖管理**: **Poetry**
  - 用于管理项目的Python依赖，确保开发和生产环境的一致性。

## 🚀 快速开始

### 1. 环境准备

- [Docker](https://www.docker.com/) 和 [Docker Compose](https://docs.docker.com/compose/)
- [Poetry](https://python-poetry.org/) (用于本地开发)
- Git

### 2. 克隆项目

```bash
git clone https://github.com/your-username/HealthLink.git
cd HealthLink
```

### 3. 环境配置

复制 `.env.example` 文件并重命名为 `.env`，然后根据您的实际情况修改其中的配置，例如数据库密码、MinIO密钥和外部LLM的API Key。

```bash
cp .env.example .env
```

### 4. 启动服务 (推荐)

使用 Docker Compose 一键启动所有后端服务：

```bash
docker-compose up -d
```

服务启动后，您可以：
- **访问API接口**: `http://localhost:28520`
- **查看API文档**: `http://localhost:28520/docs`

### 5. 本地开发 (可选)

如果您希望在本地环境进行开发和调试：

```bash
# 安装依赖
poetry install

# 启动FastAPI应用
poetry run uvicorn app.main:app --reload --port 28520
```
*注意：本地开发模式下，您需要确保能够连接到 `.env` 文件中配置的数据库、Milvus、MinIO等服务。*

## 📁 项目结构

```
.
├── app/                  # 核心后端应用代码
│   ├── api/              # FastAPI 路由模块
│   ├── agents/           # LangChain Agent 和核心AI逻辑
│   ├── core/             # 配置、认证、核心工具函数
│   ├── db/               # 数据库连接与配置
│   ├── models/           # SQLModel 数据表模型
│   ├── schemas/          # Pydantic 数据校验模型
│   ├── services/         # 核心业务逻辑服务 (Milvus, MinIO等)
│   ├── tools/            # LangChain Agent 可用的工具
│   └── main.py           # FastAPI 应用主入口
├── docker/               # Dockerfile 和相关脚本
├── scripts/              # 辅助脚本 (如数据库初始化)
├── tests/                # 测试代码
├── .env.example          # 环境变量示例文件
├── docker-compose.yml    # Docker Compose 配置文件
├── pyproject.toml        # Poetry 依赖管理文件
└── README.md             # 就是您正在看的这个文件
```

## ⚠️ 免责声明

**重要提示**: 本项目是一个技术验证和个人作品展示项目。**瑶光** 提供的所有信息、分析和建议仅供参考，**绝对不能**替代执业医师的专业诊断、治疗和建议。在做出任何医疗决策之前，请务必咨询合格的医疗专业人员。对于因使用本系统提供的信息而导致的任何后果，开发者不承担任何责任。