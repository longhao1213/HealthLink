# Agent开发计划 (v2.0 - 基于qwen-max原生多模态能力)

本文档旨在规划和指导基于通义千问`qwen-max`原生多模态大模型的AI Agent开发阶段。

---

## 1. 核心架构设计

本阶段的核心是利用`qwen-max`强大的原生多模态能力，构建一个能够统一处理文本、图片、文档和工具调用的高级Agent。此架构将不再需要独立的视觉模型或复杂的“图片到文本”预处理流程，使系统更简洁、高效。

### 请求处理流程

1.  **输入组装 (Input Assembly):**
    *   后端Chat API接收来自客户端的混合输入请求（可能包含文字、图片URL、新上传的文件等）。
    *   **文件处理:** 如果请求中包含新文件，API会先调用现有服务完成文件的上传和数据库记录，获取`file_id`。
    *   **格式化:** API将所有输入（文本、图片URL、代表文档引用的`file_id`）统一组装成一个符合LangChain和`qwen-max`多模态消息格式的列表（例如，一个`HumanMessage`的`content`列表中包含多个不同类型的字典）。

2.  **Agent核心执行 (Agent Executor):**
    *   基于`qwen-max`的Agent Executor直接接收这个组装好的多模态输入。
    *   `qwen-max`模型凭借其原生能力，能够一步到位地同时理解输入中的文本和图片内容，并识别出对文档的引用。
    *   Agent根据对全部信息的综合理解，决定是直接回答，还是需要调用工具来获取额外信息。

3.  **工具调用 (Tool Invocation):**
    *   Agent可以自主选择调用一个或多个预定义的工具：
        *   **知识库检索工具 (RAG):** 当需要专业领域知识时，提取问题中的文本，在Milvus知识库中进行向量搜索。
        *   **文档分析工具:** 当需要深入理解某个被引用的文档时，使用`file_id`从Milvus中检索该文档的全部内容。
        *   **联网搜索工具:** 当需要获取最新信息时，调用搜索引擎API。

4.  **最终回答生成 (Final Response Generation):**
    *   `qwen-max`模型整合所有上下文信息（原始的多模态输入 + 所有工具的返回结果）。
    *   生成一个全面的、有理有据的、融合了所有信息来源的最终回答。

---

## 2. 开发步骤规划

### 第一阶段：模型与工具集成

*   **目标:** 搭建一个能使用所有工具的多模态`qwen-max` Agent框架。
*   **任务:**
    1.  **安装/更新依赖:** 确保`langchain-community`或相关阿里提供的LangChain扩展包中包含对`qwen-max`多模态输入的正确支持。
    2.  **集成`qwen-max`模型:** 在`app/services/llm_service.py`中，使用`ChatDashScope`来初始化`qwen-max`模型，并确保其配置为可接受多模态输入。
    3.  **创建所有核心工具:**
        *   `knowledge_retriever_tool`: 封装`milvus_service.search`，用于RAG。
        *   `document_analyzer_tool`: 根据`file_id`从Milvus检索文档内容。
        *   `web_search_tool`: 集成联网搜索API。
    4.  **构建Agent Executor:** 使用LangChain Expression Language (LCEL)，将`qwen-max`模型、一个支持多模态输入的Prompt模板以及所有工具绑定在一起，创建Agent Executor。

### 第二阶段：实现Chat API与多模态输入组装

*   **目标:** 创建一个能接收前端混合请求，并将其正确格式化后传递给Agent的API接口。
*   **任务:**
    1.  **创建`chat_api.py`:** 在`app/api/v1/`目录下创建新的路由文件。
    2.  **设计API接口 (`POST /chat`)**: 设计一个灵活的请求体模型，允许客户端在一次请求中发送文本、图片URL和文件ID等多种类型的数据。
    3.  **实现输入组装逻辑:** 在接口内部，编写代码将接收到的各类输入，转换成LangChain的多模态消息格式。

### 第三阶段：对话历史与记忆管理

*   **目标:** 实现流畅的多轮对话，让Agent具备上下文记忆能力。
*   **任务:**
    1.  **集成对话记忆组件:** 为Agent Executor添加`ConversationBufferMemory`或类似的记忆管理机制。
    2.  **数据库持久化:** 在`chat_api.py`中，每次完成问答后，将用户输入和AI的输出完整地存入`chat_session`和`chat_message`表。
    3.  **加载历史:** 在每次新请求时，从数据库加载对话历史并填充到Agent的记忆中。