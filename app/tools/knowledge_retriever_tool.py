import logging
from langchain.tools import tool
from typing import List,Dict,Any

from app.services.milvus_service import milvus_service
from app.services.vectorization_service import embeddings
from pydantic import BaseModel,Field

class KnowledgeSearchInput(BaseModel):
    query: str = Field(description="需要进行向量相似度搜索的自然语言问题或关键词。")

@tool(args_schema=KnowledgeSearchInput)
def knowledge_retriever_tool(query:str) -> str:
    """
     当需要查询与医疗、健康、疾病、诊断、治疗方案等相关的专业知识时，使用此工具。
     它会从内部知识库中检索最相关的文档片段来回答问题。
     输入应该是一个具体的医学问题或术语。
    :param query: KnowledgeSearchInput
    :return:
    """
    logging.info(f"知识库检索工具被调用，查询类容：{query}")
    if not embeddings:
        return "错误：Embedding模型未初始化，无法执行知识库查询"
    if not milvus_service:
        return "错误：Milvus服务未初始化，无法执行知识库查询"
    try:
        # 把用户的查询文本进行向量化
        query_vector = embeddings.embed_query(query)
        # 使用向量在milvus里面搜索，查询3个相关的结果
        search_results = milvus_service.search(query_vector, 3)
        if not search_results:
            return "在知识库中没有查询到相关信息"
        # 格式化处理，把检索到的文本块拼成一个字符串
        content = ""
        for i,result in enumerate(search_results):
            content += f"--- 参考资料 {i+1} (来源文件ID：{result['file_id']}) ---\n"
            content += result['chunk_text'] + "\n\n"
        logging.info(f"知识库检索工具返回了{len(search_results)}条结果")
        return content
    except Exception as e:
        logging.error(f"知识库检索工具执行错误：{e}")
        return "错误：知识库检索工具执行错误"