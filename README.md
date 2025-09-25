# 智能医疗助手 (HealthLink)

本项目旨在开发一个基于大型语言模型（LLM）的“智能医疗助手”。该助手旨在为用户提供一个安全、私密的交流环境，用户可以咨询健康问题、解读个人病例报告。系统的核心能力在于其结合了通用AI能力和特定领域知识库，通过检索增强生成（RAG）技术，为用户提供更精准、更具上下文的回答。

## 项目结构

```
HealthLink/
├── app/                  # 核心后端应用代码
│   ├── api/              # API路由模块 (e.g., chat.py, users.py)
│   ├── core/             # 项目配置、核心工具函数
│   ├── db/               # 数据库连接与会话管理
│   ├── models/           # 数据模型定义 (SQLModel tables)
│   ├── schemas/          # 数据校验模型 (Pydantic schemas)
│   ├── services/         # 核心业务逻辑 (RAG, file processing)
│   └── main.py           # FastAPI应用主入口
├── docker/               # Docker相关配置文件
├── scripts/              # 辅助脚本 (e.g., data migration)
├── tests/                # 测试代码
├── .gitignore
├── README.md             # 项目说明
└── requirements.txt      # Python依赖
```

## 下一步计划

1.  **完善`requirements.txt`**: 添加项目所需的所有Python库。
2.  **编写`docker-compose.yml`**: 定义后端、数据库(MySQL)、向量存储(Milvus)和对象存储(MinIO)服务。
3.  **创建`Dockerfile`**: 为FastAPI应用创建容器化配置。
4.  **实现基础API**: 在`app/main.py`中创建一个简单的`hello world`接口，并使用Docker Compose启动整个后端服务进行验证。

