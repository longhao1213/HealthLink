# 知识库功能开发计划 (v1.0)

本文档旨在规划和指导智能医疗助手项目中，关于知识库文件上传、处理及向量化的功能开发。

---

## 1. 整体设计思路

我们将构建一个以MinIO为文件存储，MySQL为元数据记录，Milvus为向量存储的异步处理管道。整个流程强调前后端分离、资源解耦和异步化处理，以确保系统的可扩展性和高性能。

### 核心流程

1.  **获取上传凭证:** 客户端（前端/Apifox）向FastAPI后端发起请求，告知希望上传的文件信息。
    *   后端在`knowledge_file`表中预创建一条`pending`状态的记录。
    *   后端生成一个带有时效性的MinIO预签名URL (Presigned URL)。
    *   后端将文件ID和预签名URL返回给客户端。

2.  **文件上传 (前端直传):** 客户端使用获取到的预签名URL，通过`PUT`请求直接将文件二进制流上传到MinIO服务器。此过程不占用后端服务资源。

3.  **上传回调与确认:** MinIO在文件成功上传后，通过配置好的Webhook向后端发送一个回调通知。
    *   后端API接收此通知，验证并解析。
    *   根据通知内容，更新`knowledge_file`表中对应文件的状态为`completed`，并补全文件大小等元数据。

4.  **触发向量化 (异步任务):** 文件状态更新为`completed`后，后端将触发一个后台异步任务，将文件ID推入处理队列。此操作必须是非阻塞的。

5.  **后台向量化处理:**
    *   一个独立的Worker进程从队列中获取待处理的文件ID。
    *   从MinIO下载原始文件。
    *   使用`LangChain`的`DocumentLoader`对文档进行加载、解析和切块(Chunking)。
    *   调用Embedding模型（如OpenAI API）将文本块转换为向量。
    *   将向量及相关元数据批量存入Milvus向量数据库。
    *   更新`knowledge_file`表中的文件状态为`vectorized`或`failed`。

---

## 2. 开发步骤规划

我们将按照以下四个主要步骤进行功能开发：

### 第一步：MinIO集成与客户端封装

*   **目标:** 建立FastAPI应用与MinIO服务器的通信基础。
*   **任务:**
    1.  在`app/services/`目录下创建`minio_service.py`。
    2.  在服务中初始化MinIO Python客户端，并从`app/core/config.py`读取配置。
    3.  封装核心函数：
        *   `generate_presigned_upload_url(file_path: str, content_type: str)`: 生成用于上传的预签名URL。
        *   `check_bucket_exists_and_create(bucket_name: str)`: 检查并创建存储桶。
        *   `get_file_url(file_path: str)`: （可选）生成文件的公共或私有访问URL。

### 第二步：创建文件上传核心API

*   **目标:** 实现文件上传的申请、代理和回调逻辑。
*   **任务:**
    1.  在`app/api/v1/`目录下创建`knowledge_file_api.py`。
    2.  **实现获取上传凭证接口 (`POST /files/upload-request`)**: 核心接口，用于前端直传模式。
    3.  **实现上传回调接口 (`POST /files/upload-callback`)**: 接收MinIO的通知，确认上传并触发下一步的异步任务。
    4.  (可选) **实现后端代理上传接口 (`POST /files/upload-proxy`)**: 作为备用或内部使用的上传方式。

### 第三步：实现异步向量化任务

*   **目标:** 构建文件处理和AI向量化的核心管道。
*   **任务:**
    1.  **技术选型:** 确定后台任务框架。初期建议使用FastAPI内置的`BackgroundTasks`进行快速实现和验证。
    2.  在`app/services/`目录下创建`vectorization_service.py`。
    3.  定义核心处理函数`vectorize_file(file_id: int)`，并在其中完成文件下载、解析、切分、向量化、存入Milvus的完整逻辑。
    4.  在第二步的回调接口中，注入`BackgroundTasks`依赖，并使用`background_tasks.add_task(vectorize_file, file_id)`来调用任务。

### 第四步：完善与安全加固

*   **目标:** 确保功能稳定、安全、可靠。
*   **任务:**
    1.  为`knowledge_file_api.py`中的所有接口添加`Depends(get_current_admin_user)`依赖，确保只有管理员可以操作知识库。
    2.  配置MinIO的CORS策略，允许来自前端域名的`PUT`请求。
    3.  配置MinIO的Webhook，使其能够正确调用我们的回调接口。
    4.  增加完善的日志记录和统一的异常处理。

