import logging

from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import get_default_llm

logger = logging.getLogger(__name__)
system_prompt = """
# 角色与目标
你是一个专业的医疗信息摘要员。你的任务是阅读一段新的对话记录，并结合已有的旧摘要，生成一个更新后的、简洁、精确、结构化的新摘要。这个摘要将作为长期记忆，帮助AI助手在未来的对话中更好地理解用户。

# 工作流程
1.  **分析新对话:** 阅读“新对话记录”，理解用户在本轮对话中提出的主要问题、AI给出的核心建议，以及任何透露出的用户健康状况、疑虑或偏好。
2.  **融合旧摘要:** 阅读“历史摘要”，理解用户的长期背景。
3.  **生成新摘要:** 将新对话中的关键信息，以“增量更新”或“合并重写”的方式，整合进历史摘要中，生成一份全新的、全面的摘要。如果历史摘要为空，则根据新对话直接创建第一份摘要。

# 摘要格式要求
请严格按照以下JSON格式输出，不要添加任何额外的解释或对话。

```json
{
  "health_status": "用户的整体健康状况总结。例如：'自述有2型糖尿病史5年，目前在通过饮食控制血糖。'",
  "recent_concerns": [
    "近期关注的主要问题列表。例如：'询问了关于夜间低血糖的症状和处理方法。'",
    "对化验单中的“甘油三酯偏高”表示担忧。"
  ],
  "preferences": "用户的偏好或特定要求。例如：'倾向于通过自然疗法和生活方式调整来改善健康。'",
  "key_info": {
    "medications": "提及的关键药物。例如：'二甲双胍'",
    "allergies": "提及的过敏史。例如：'青霉素过敏'",
    "vitals": "提及的关键生理指标。例如：'最近一次空腹血糖为7.8 mmol/L'"
  }
}
```

# 指导原则
*   **精炼:** 只保留最核心、最关键的信息。忽略闲聊和不重要的细节。
*   **客观:** 忠实于对话内容，不要进行推断或提供额外建议。
*   **结构化:** 严格遵守JSON输出格式。如果某个字段没有信息，请使用空字符串`""`或空列表`[]`作为值。
*   **合并更新:** 新摘要应该是对旧摘要的补充和完善，而不是简单地拼接。

# 输入变量
*   **历史摘要:** {old_summary}
*   **新对话记录:** {temp_history}
"""

class SummaryGenerationAgent:
    """
    一个用于生成摘要的Agent。
    """
    def __init__(self):
        self.agent_executor = None
        llm = get_default_llm()
        try:
            # 创建提示词模版
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "{temp_history}"),
                ("user", "{old_summary}")
            ])
            agent_chain = (
                {
                    "temp_history": lambda x: x["temp_history"],
                    "old_summary": lambda x: x["old_summary"],
                }
                | prompt
                | llm
            )
            # 创建agent Executor
            self.agent_executor = AgentExecutor(
                agent=agent_chain,
                tools=[],
                verbose=True,
                handle_parsing_errors=True,
                return_intermediate_steps=False,
                max_iterations=5,
                max_execution_time=300,
            )
            logger.info("成功创建摘要生成agent")
        except Exception as e:
            logger.error(f"初始化摘要生成agent失败: {e}")

    async def invoke(self, temp_history:str, old_summary:str) -> str:
        """
        调用生成摘要的智能体
        :param temp_history:
        :param old_summary:
        :return:
        """
        if not self.agent_executor:
            return "摘要生成服务未初始化"
        try:
            resource = await self.agent_executor.ainvoke({
                "temp_history":temp_history,
                "old_summary":old_summary,
            })
            return resource.get("output","")
        except Exception as e:
            logger.error(f"调用摘要生成agent时发生错误: {e}", exc_info=True)
            return ""

summary_generation_agent = SummaryGenerationAgent()