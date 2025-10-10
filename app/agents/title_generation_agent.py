import logging

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.llm import get_default_llm

logger = logging.getLogger(__name__)
system_prompt = """
你是一个智能标题生成助手，能够根据用户输入的内容自动生成简洁明了的标题。

请遵循以下规则：
1. 标题长度控制在10个汉字以内
2. 使用中文表达
3. 标题应准确概括用户核心问题
4. 避免使用模糊或过于宽泛的表述
5. 保持标题简洁且具有描述性
例如:
用户问题: "你好，我想问一下，我最近体检发现甘油三酯有点偏高，平时应该注意些什么？"
你的输出: "甘油三酯偏高注意事项"
"""


class TitleGenerationAgent:
    """
    一个用于生成标题的Agent。
    """

    def __init__(self):
        """
        初始化
        """
        self.agent_executor = None
        tools = []
        try:
            llm = get_default_llm()
            # 创建提示词模版
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            # 使用LCEL构建Agent
            # agent_chain = (
            #         {
            #             "input": lambda x: x["input"],
            #         }
            #         | prompt
            #         | llm
            # )
            agent = create_openai_functions_agent(llm,tools, prompt)
            # 创建agent Executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                return_intermediate_steps=False,
                max_iterations=5,
                max_execution_time=300,
            )
            logger.info("成功创建标题生成agent")
        except Exception as e:
            logger.error(f"初始化标题生成agent失败: {e}")

    async def invoke(self, user_input: str) -> str:
        """
        调用生成标题的智能体
        :param user_input:
        :return:
        """
        if not self.agent_executor:
            return "标题生成服务未初始化"
        try:
            resource = await self.agent_executor.ainvoke({
                "input": user_input,
            })
            return resource.get("output", "抱歉，没有生成标题。")
        except Exception as e:
            logger.error(f"调用标题生成agent时发生错误: {e}", exc_info=True)
            return "抱歉，没有生成标题。"


title_generation_agent = TitleGenerationAgent()
