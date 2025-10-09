import json
import logging
import time
from typing import List, Dict, Any, AsyncIterator

from fastapi import BackgroundTasks
from sqlmodel import Session

from app.core.auth import UserType
from app.core.config import settings
from app.db.redis_config import redis_service
from app.models.chat import ChatMessage, ChatSession, Memory
from app.models.user import PatientUser, AdminUser
from app.schemas.chat_schema import ChatRequest
from app.agents.main_chat_agent import llm_service
from app.agents.summarization_agent import summary_generation_agent
from app.agents.title_generation_agent import title_generation_agent

logger = logging.getLogger(__name__)

"""
Service: ChatService (业务流程编排)

这个服务是处理聊天交互的核心业务流程编排者。它不直接执行AI推理或数据库操作，
而是像一个“项目经理”，负责调用和协调其他更专业的服务（如LLMService、数据库模型等），
以完成一次完整的、端到端的聊天请求。

主要职责 (以一次流式聊天为例):

1.  **接收与准备 (Receive & Prepare):**
    - 从API层接收原始的用户输入（问题、文件、图片等）以及会话ID（session_id）。

2.  **加载上下文 (Load Context):**
    - 根据会话ID，访问数据库，加载近期的对话历史记录（chat_history）。
    - (可选) 根据用户ID，加载用户的长期记忆摘要（memory），并将其作为上下文的一部分。

3.  **调用AI核心 (Invoke AI Core):**
    - 将用户输入、对话历史和记忆摘要等所有上下文信息，传递给`LLMService`的`stream_invoke`方法。
    - `LLMService`是纯粹的AI能力提供者，它接收上下文并返回一个AI回答的流式生成器。

4.  **处理与返回响应 (Process & Return Response):**
    - 遍历从`LLMService`获取的回答生成器。
    - 将AI生成的每一个文本块（chunk）立即`yield`回API层，以便API层可以将其流式传输给前端。
    - 在遍历的过程中，将所有文本块拼接成一个完整的回答字符串。

5.  **持久化 (Persist):**
    - 在AI的完整回答生成后：
        a.  将用户的当前问题和AI的完整回答，作为两条新记录存入数据库的`chat_message`表，并关联到当前的会话ID。
        b.  (可选) 更新`chat_session`表的元数据，如最后活跃时间、会话主题等。

6.  **触发后台任务 (Trigger Background Tasks):**
    - 在所有主要流程完成后，启动一个或多个后台任务来执行非阻塞的、可延迟的操作。
    - 主要任务是调用`MemoryService`，让它根据刚刚完成的这次对话，在后台异步地为用户生成或更新长期记忆摘要。

通过这种方式，`ChatService`确保了核心聊天流程的快速响应，同时将数据库写入和记忆生成等耗时操作解耦，
实现了高性能和高可维护性的架构。
"""


class ChatService:
    async def invoke(self,
                     request: ChatRequest,
                     current_user: UserType,
                     background_tasks: BackgroundTasks,
                     session: Session
                     ) -> str:
        """
        完整调用业务
        :param request: 请求
        :param current_user:  用户信息
        :param background_tasks:
        :param session:
        :return:
        """

        # 获取redis客户端
        redis_client = redis_service.get_client()
        try:
            # 构建一个通用存储到redis的key，这个key用来存储对话摘要
            summary_key = f"summary:{current_user.id}:{request.session_id}"
            # 构建一个用户对话临时缓存key，这个缓存根据摘要生成策略，数量不会太多
            temp_history_key = f"temp_history:{current_user.id}:{request.session_id}"
            # 解析用户信息，区分web端用户和app端用户
            if isinstance(current_user, PatientUser):
                # app用户
                summary_key = f"app:{summary_key}"
                temp_history_key = f"app:{temp_history_key}"
            elif isinstance(current_user, AdminUser):
                # web用户
                summary_key = f"web:{summary_key}"
                temp_history_key = f"web:{temp_history_key}"
            # 从redis中获取之前的对话摘要，可能没有
            summary_data = await redis_client.get(summary_key)
            temp_chat_history = []
            chat_history = await redis_client.get(temp_history_key)
            if chat_history:
                # 存在临时对话记录缓存
                temp_chat_history = json.loads(chat_history)
            # 携带对话摘要去调用大模型
            result = llm_service.invoke(request.user_input, temp_chat_history, summary_data)
            # 拿到了对话返回值，异步的保存用户的对话信息,并且判断是否需要生成摘要
            background_tasks.add_task(
                self.save_temp_chat_history_and_create_summary,
                temp_history_key,
                summary_key,
                temp_chat_history,
                summary_data,
                request,
                result,
                session,
                current_user.id
            )
            return result
        finally:
            redis_client.close()

    async def stream_invoke(self,
                     request: ChatRequest,
                     current_user: UserType,
                     background_tasks: BackgroundTasks,
                     session: Session) -> AsyncIterator[str]:
        """
        异步调用
        :param request:
        :param current_user:
        :param background_tasks:
        :param session:
        :return:
        """
        # 获取redis客户端
        redis_client = redis_service.get_client()
        try:
            # 构建一个通用存储到redis的key，这个key用来存储对话摘要
            summary_key = f"summary:{current_user.id}:{request.session_id}"
            # 构建一个用户对话临时缓存key，这个缓存根据摘要生成策略，数量不会太多
            temp_history_key = f"temp_history:{current_user.id}:{request.session_id}"
            # 解析用户信息，区分web端用户和app端用户
            if isinstance(current_user, PatientUser):
                # app用户
                summary_key = f"app:{summary_key}"
                temp_history_key = f"app:{temp_history_key}"
            elif isinstance(current_user, AdminUser):
                # web用户
                summary_key = f"web:{summary_key}"
                temp_history_key = f"web:{temp_history_key}"
            # 从redis中获取之前的对话摘要，可能没有
            summary_data = await redis_client.get(summary_key)
            temp_chat_history = []
            chat_history = await redis_client.get(temp_history_key)
            if chat_history:
                # 存在临时对话记录缓存
                temp_chat_history = json.loads(chat_history)
            # 携带对话摘要去调用大模型
            response_generator = llm_service.stream_invoke(request.user_input, temp_chat_history, summary_data)
            result = ""
            async for chunk in response_generator:
                result += chunk
                yield self._format_stream_chunk( chunk)
            # 拿到了对话返回值，异步的保存用户的对话信息,并且判断是否需要生成摘要
            background_tasks.add_task(
                self.save_temp_chat_history_and_create_summary,
                temp_history_key,
                summary_key,
                temp_chat_history,
                summary_data,
                request,
                result,
                session,
                current_user.id
            )
        finally:
            redis_client.close()


    def save_temp_chat_history_and_create_summary(self,
                               temp_history_key: str,
                               summary_key: str,
                               temp_chat_history: List[Dict[str, Any]],
                               summary_data: str,
                               request: ChatRequest,
                               ai_message: str,
                               session: Session,
                               user_id: int
                               ):
        """
        保存用户的临时对话记录
        :param temp_history_key: 临时对话历史的key
        :param summary_key: 对话摘要的key
        :param temp_chat_history: 对话历史
        :param summary_data: 对话摘要
        :param request: 用户请求
        :param ai_message: ai回答
        :param session: 数据库对象
        :param user_id: 用户ID
        :return:
        """
        redis_client = redis_service.get_client()
        # 判断对话历史的数量是否达到设置返回，如果达到，就调用生成摘要，并且删除临时对话记录
        temp_chat_history.append({"user": request.user_input, "assistant": ai_message})
        try:
            # 判断sessionId是否存在
            if not request.session_id:
                # session_id不存在，那么调用ai生成标题
                title = title_generation_agent.invoke(request.user_input)
                chat_session = ChatSession()
                chat_session.patient_user_id = request.patient_user_id
                chat_session.topic = title
                session.add(chat_session)
                request.session_id = chat_session.id
            # 保存用户聊天历史
            user_message = ChatMessage()
            user_message.session_id = request.session_id
            user_message.role = "user"
            user_message.content = request.user_input
            session.add(user_message)
            assistant_message = ChatMessage()
            assistant_message.session_id = request.session_id
            assistant_message.role = "assistant"
            assistant_message.content = ai_message
            session.add(assistant_message)
            if len(temp_chat_history) >= settings.TEMP_MEMORY_SIZE:
                # 调用摘要生成
                new_summary = summary_generation_agent.invoke(json.dumps(temp_chat_history), summary_data)
                if new_summary:
                    redis_client.save(summary_key, new_summary)
                    redis_client.delete(temp_history_key)
                    # 保存到数据库
                    memory = Memory()
                    memory.summary = new_summary
                    memory.user_id = user_id
                    memory.source_session_id = request.session_id
                    session.add(memory)
                else:
                    logger.error("生成摘要失败")
                    redis_client.save(temp_history_key, json.dumps(temp_chat_history))
            else:
                # 保存临时对话记录
                redis_client.save(temp_history_key, json.dumps(temp_chat_history))
        finally:
            redis_client.close()

    def _format_stream_chunk(self,content:str) -> str:
        """
        一个内部方法，将文本内容包装成指定的流式JSON格式，并符合SSE规范。
        :param content:
        :return:
        """
        # 创建符合格式的字典结构
        chunk_data = {
            "choices":[
                {
                    "delta":{
                        "content":content,
                        "role":"assistant"
                    },
                    "index":0
                }
            ],
            "created":int(time.time()),
            "model":settings.MODE_NAME
        }
        # 把字典转换为json
        json_string = json.dumps(chunk_data,ensure_ascii=False)
        # 按照sse格式返回
        return f"data: {json_string}\n\n"

chat_service = ChatService()