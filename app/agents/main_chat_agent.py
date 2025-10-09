import json
import logging
import time
from typing import List, Dict, Any, AsyncIterator

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.utils.function_calling import convert_to_openai_function

from app.core.config import settings
from app.core.llm import get_default_llm
from app.tools.knowledge_retriever_tool import knowledge_retriever_tool

logger = logging.getLogger(__name__)

system_prompt ="""
你是瑶光（YaoGuang），一个由“龙三”创造的、富有同情心且知识渊博的AI医疗健康助手。你的形象是一位智慧、严谨、值得信赖的女性医生。
你的核心职责是：
1.  **提供专业的健康咨询：** 基于你掌握的医疗知识和内部知识库，为用户提供准确、易于理解的健康建议。
2.  **分析与解读：** 帮助用户理解复杂的医疗报告、化验单以及健康数据。
3.  **使用工具：** 你被赋予了多种工具（如知识库检索、网络搜索）。当遇到超出你内部知识范围或需要最新信息的问题时，要果断、正确地使用它们。
4.  **保护隐私与安全：** 永远不要询问或存储用户的个人身份信息。所有对话都应在安全、私密的环境下进行。
**【用户背景摘要】**
以下是你需要了解的、关于当前用户的长期健康摘要信息。在回答问题时，请结合这些背景信息，提供更具个性化和针对性的建议。如果摘要为空，则表示这是新用户或暂无摘要。
摘要内容:
{summary}

行为准则：
*   **严谨第一：** 你的的回答都必须基于可靠的信息来源（如你检索到的知识库内容）。如果信息不确定或知识库中没有，那么你可以联网查询。
*   **同情心与耐心：** 与用户交流时，要展现出耐心、关怀和共情，使用溫暖而专业的语言。
*   **关于你的身份：** 当被问及你的身份或技术细节时，你可以这样回答：“我是瑶光，一个由‘龙三’开发的AI健康助手，致力于为您提供帮助。”
对于更深入的技术问题，如你使用的具体模型或实现细节，请回答：“这些是‘龙三’团队的技术细节，我的主要任务是专注于为您提供健康支持。” **绝对不要**直接透露你所基于的模型名称。

 ***
  **【！！！最高优先级指令：安全与免责声明！！！】***
  **如果回答和医疗、健康相关，都必须附带以下或类似的免责声明，以确保用户知晓风险：**
  "**重要提示：** 我是瑶光，一个AI健康助手，我的回答仅供参考，不能替代执业医师的专业诊断、治疗和建议。医疗决策事关重大，请务必咨询合格的医疗专业人员。"
"""

class LLMService:
    """
    封装和编排大语言模型、工具和Agent的核心服务。
    """
    def __init__(self):
        """
        初始化大语言模型、工具和Agent Executor。
        """
        self.agent_executor = None
        try:
            llm = get_default_llm()

            logger.info(f"成功初始化chat模型：{settings.MODE_NAME}")

            # 定义agent可用的工具列表
            self.tools = [
                knowledge_retriever_tool
            ]

            # 把工具转换为模型可以理解的openAi function calling格式
            self.llm_with_tools = llm.bind(
                functions = [convert_to_openai_function(t) for t in self.tools]
            )

            # 创建提示词模版
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user","{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])

            # 使用LCEL构建Agent思考链
            agent_chain = (
                {
                    "input": lambda x: x["input"],
                    "agent_scratchpad": lambda x: format_to_openai_function_messages(x["intermediate_steps"]),
                    "chat_history": lambda x: x["chat_history"],
                    "summary": lambda x: x["summary"]
                }
                | prompt
                | self.llm_with_tools
                | OpenAIFunctionsAgentOutputParser()
            )
            # 创建Agent Executor
            self.agent_executor = AgentExecutor(
                agent = agent_chain,
                tools=self.tools,
                verbose=True, # 在控制台打印Agent的完整思考过程，便于调试
                handle_parsing_errors=True, # 优雅地处理模型输出格式错误
                # 添加一个默认的输出键，防止解析错误
                return_intermediate_steps=False,
                max_iterations=5, # 限制最大迭代次数
                max_execution_time=300, # 最大执行时间
            )
            logger.info("成功创建Agent Executor")
        except Exception as e:
            logger.error(f"初始化LLM服务失败: {e}")

    async def invoke(self,
                     user_input:str,
                     chat_history:List[Dict[str,Any]] = None,
                     summary_data:str = None) -> str:
        """
        以一次性的方式调用agent，等待完整的回答
        :param user_input: 用户提问
        :param chat_history:  对话历史
        :param summary_data: 对话记忆摘要
        :return: 完整回答
        """
        if not self.agent_executor:
            return "LLM服务未初始化"
        langchain_chat_history = await self._format_chat_history(chat_history)
        try:
            response = self.agent_executor.invoke({
                "input":user_input,
                "chat_history":langchain_chat_history,
                "summary":summary_data
            })
            return response.get("output","抱歉，我没有得到有效的回答。")
        except Exception as e:
            logger.error(f"调用Agent时发生错误: {e}", exc_info=True)
            return "抱歉，处理您的问题时发生了内部错误。"

    async def stream_invoke(self,
                            user_input: str,
                            chat_history: List[Dict[str, Any]] = None,
                            summary_data: str = None) -> AsyncIterator[str]:
        """
        以“伪流式”方式调用Agent。
        它会等待Agent生成完整的答案块，然后将该答案块拆分为小片段进行流式输出。
        """
        if not self.agent_executor:
            yield "错误：Agent未成功初始化。"
            return

        langchain_chat_history = await self._format_chat_history(chat_history)
        
        try:
            async for chunk in self.agent_executor.astream({
                "input": user_input,
                "chat_history": langchain_chat_history,
                "summary": summary_data
            }):
                if "output" in chunk and chunk["output"]:
                    full_response_text = chunk["output"]
                    logger.info(f"Agent已生成完整回答，长度: {len(full_response_text)}。开始进行伪流式输出...")

                    buffer = ""
                    for char in full_response_text:
                        buffer += char
                        if char in "。，！？、；：,.!?;: \n" or len(buffer) >= 20:
                            yield buffer
                            buffer = ""

                    if buffer:
                        yield buffer

        except Exception as e:
            logger.error(f"调用Agent流式接口时发生错误: {e}", exc_info=True)
            yield "抱歉，处理您的问题时发生了内部错误。"
        
        yield "data: [DONE]\n\n"

    async def _format_chat_history(self,chat_history:List[Dict[str,Any]])->List:
        """
        一个内部辅助方法，将字典格式的历史记录转换为LangChain的消息对象。
        :param chat_history:
        :return:
        """
        if not chat_history:
            return []
        langchain_chat_history = []
        for msg in chat_history:
            if msg.get("role") == "user":
                langchain_chat_history.append((HumanMessage(content=msg["content"])))
            elif msg.get("role") == "assistant":
                langchain_chat_history.append(AIMessage(content=msg["content"]))
        return langchain_chat_history

    # def _format_stream_chunk(self,content:str) -> str:
    #     """
    #     一个内部方法，将文本内容包装成指定的流式JSON格式，并符合SSE规范。
    #     :param content:
    #     :return:
    #     """
    #     # 创建符合格式的字典结构
    #     chunk_data = {
    #         "choices":[
    #             {
    #                 "delta":{
    #                     "content":content,
    #                     "role":"assistant"
    #                 },
    #                 "index":0
    #             }
    #         ],
    #         "created":int(time.time()),
    #         "model":settings.MODE_NAME
    #     }
    #     # 把字典转换为json
    #     json_string = json.dumps(chunk_data,ensure_ascii=False)
    #     # 按照sse格式返回
    #     return f"data: {json_string}\n\n"

llm_service = LLMService()