import asyncio
import logging
from langchain.tools import tool
from typing import List,Dict,Any
from langchain_community.vectorstores import Milvus

from app.core.config import settings
from app.services.milvus_service import milvus_service, DEFAULT_COLLECTION_NAME
from app.services.vectorization_service import embeddings
from pydantic import BaseModel,Field

class KnowledgeSearchInput(BaseModel):
    query: str = Field(description="需要进行向量相似度搜索的自然语言问题或关键词。")

@tool(args_schema=KnowledgeSearchInput)
async def knowledge_retriever_tool(query:str) -> str:
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
        vector_store = Milvus(
            embedding_function=embeddings,
            collection_name=DEFAULT_COLLECTION_NAME,
            connection_args={"host": settings.MILVUS_HOST, "port": settings.MILVUS_PORT},
        )
        # 将向量存储对象转换为一个配置了MMR的Retriever（检索器）
        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                'k': 5,
                'fetch_k': 20,
                'lambda_mult': 0.5
            },
        )
        # 把用户的查询文本进行向量化
        # query_vector = await embeddings.aembed_query(query)
        relevant_docs = await retriever.ainvoke(query)
        # 使用向量在milvus里面搜索，查询3个相关的结果
        # search_results = await milvus_service.search(query_vector, 3)
        if not relevant_docs:
            return "在知识库中没有查询到相关信息"
        # 格式化处理，把检索到的文本块拼成一个字符串
        content = ""
        for i,result in enumerate(relevant_docs):
            file_id = result.metadata.get('file_id', '未知')
            chunk_text = result.page_content
            content += f"--- 参考资料 {i+1} (来源文件ID: {file_id}) ---\n"
            content += chunk_text + "\n\n"
        logging.info(f"知识库检索工具返回了{len(relevant_docs)}条结果")
        return content
    except Exception as e:
        logging.error(f"知识库检索工具执行错误：{e}")
        return "错误：知识库检索工具执行错误"