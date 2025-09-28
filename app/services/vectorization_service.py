import json
import logging
import os
import tempfile
from contextlib import contextmanager
from io import BytesIO

import requests

from app.services.milvus_service import milvus_service

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader, UnstructuredFileLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlmodel import Session

from app.core.config import settings
from app.core.constants import SupportedMimeTypes, FileStatus
from app.db.db import get_session
from app.models.knowledge import KnowledgeFile
from app.services.minio_service import minio_service
from app.db.db import engine

"""
向量转换
"""
logger = logging.getLogger(__name__)

# 初始化embedding
try:
    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        openai_api_base=settings.EMBEDDING_MODEL_URL,
        openai_api_key=settings.EMBEDDING_MODEL_KEY
    )
    logger.info(f"成功初始化embedding模型")
except Exception as e:
    logger.error(f"初始化embedding模型失败: {e}")

# 定义文档加载器的类型映射
LOADER_MAPPING = {
    SupportedMimeTypes.PDF.value: PyPDFLoader,
    SupportedMimeTypes.DOCX.value: Docx2txtLoader,
    SupportedMimeTypes.TXT.value: TextLoader,
    SupportedMimeTypes.DOC.value: UnstructuredFileLoader
    # TODO 还可以添加更多支持的类型
}


@contextmanager
def as_temp_file(file_stream: BytesIO, suffix: str = None):
    """
    一个上下文管理器，将内存中的文件流写入临时对象
    退出上下文的时候回自动删除临时文件
    :param file_stream:
    :param suffix:
    :return:
    """
    # 使用delete=False确保在with块内文件是可访问的
    # NamedTemporaryFile会返回一个类文件对象
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_f:
        # 把内存流写入到临时文件
        temp_f.write(file_stream.getvalue())
        temp_file_path = temp_f.name
    try:
        # yield临时文件的路径
        yield temp_file_path
    finally:
        # with块结束后，清理临时文件
        os.unlink(temp_file_path)


def vectorize_file(file_id: int):
    """
    核心处理函数：下载、加载、切分、向量化并存储文件
    设计为在后台任务中进行
    :param file_id:
    :return:
    """
    # 使用with语句确保session被正常关闭
    with Session(engine) as session:
        try:
            # 在数据库中查询文件
            db_file = session.get(KnowledgeFile, file_id)
            if not db_file:
                logger.error(f"向量化任务失败，在数据库中午发找到文件: {file_id}")
                return
            db_file.status = FileStatus.PROCESSING
            # 更新文件状态
            session.add(db_file)
            session.commit()
            # 图片处理
            if db_file.mime_type.startswith("image/"):
                # 图片处理
                logger.info(f"开始处理图片文件: {db_file.id}")
                # 为图片生成一个临时地址
                image_url = minio_service.generate_presigned_download_url(
                    bucket_name=settings.MINIO_DEFAULT_BUCKET,
                    object_name=db_file.file_path,
                    expires_in_minutes=10
                )
                if not image_url:
                    logger.error(f"向量化任务失败，无法生成图片下载地址: {db_file.id}")
                    return
                # 构建http请求
                api_url = settings.EMBEDDING_MODEL_URL
                api_key = settings.EMBEDDING_MODEL_KEY
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                # 根据阿里云文档，构造请求体
                payload = {
                    "model": settings.EMBEDDING_MODEL,
                    "input": {
                        "contents": [
                            {
                                "image": image_url
                            }
                        ]
                    }
                }
                logger.info(f"http请求向量化headers：{json.dumps(headers)}")
                logger.info(f"http请求向量化参数：{json.dumps(payload)}")
                # 发送http请求
                response = requests.post(api_url, headers=headers, data=json.dumps(payload))
                response.raise_for_status()
                response_data = response.json()
                logger.info(f"http请求向量化结果：{json.dumps(response_data)}")
                # 提取向量
                if not response_data.get("output") or not response_data["output"].get("embeddings"):
                    raise ValueError("阿里云API响应格式不正确，未找到embeddings列表")
                image_vector = response_data["output"]["embeddings"][0]["embedding"]
                # 构建实体存储milvus
                entities_to_insert = [{
                    "file_id": db_file.id,
                    "knowledge_base_id": db_file.knowledge_base_id,
                    "chunk_text": f"Image: {db_file.filename}",
                    "vector": image_vector
                }]
                milvus_service.insert(entities_to_insert)
                logger.info(f"向量化任务成功，向Milvus插入数据")
            else:
                # 下载文件
                logger.info(f"开始下载文件: {db_file.id}")
                file_data = minio_service.download_file(
                    bucket_name=settings.MINIO_DEFAULT_BUCKET,
                    object_name=db_file.file_path
                )
                if not file_data:
                    logger.error(f"向量化任务失败，无法下载文件: {db_file.id}")
                    return
                # 把文件内容读取到内存中
                file_stream = BytesIO(file_data)
                # 加载文档
                logger.info(f"正在加载文件内容，MIME Type：{db_file.mime_type}")
                docs = []
                loader_class = LOADER_MAPPING.get(db_file.mime_type)
                if not loader_class:
                    logger.error(f"向量化任务失败，不支持的MIME Type: {db_file.mime_type}")
                    return
                if loader_class in [PyPDFLoader]:
                    # 这些loader支持文件流
                    loader = loader_class(file_stream)
                    docs = loader.load()
                else:
                    with as_temp_file(file_stream, suffix=db_file.file_ext) as temp_path:
                        loader = loader_class(temp_path)
                        docs = loader.load()
                # 切分文本
                if docs:
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=1000,
                        chunk_overlap=200
                    )
                    chunks = text_splitter.split_documents(docs)
                    chunk_texts = [chunk.page_content for chunk in chunks]

                # 生成向量
                if not embeddings:
                    raise ConnectionError("无法初始化embedding模型")
                logger.info(f"正在生成向量，向量数量：{len(chunk_texts)}")
                vectors = embeddings.embed_documents(chunk_texts)
                logger.info(f"向量生成完成，向量数量：{len(vectors)}")

                # 把数据存储到向量数据库
                entities_to_insert = []
                for text, vec in zip(chunk_texts, vectors):
                    entities_to_insert.append({
                        "file_id": db_file.id,
                        "knowledge_base_id": db_file.knowledge_base_id,
                        "chunk_text": text,
                        "vector": vec
                    })
                if entities_to_insert:
                    milvus_service.insert(entities_to_insert)
                    logger.info(f"向量存储完成，向量数量：{len(entities_to_insert)}")
            logger.info(f"修改数据库状态: {db_file.id}")
            # 更新状态
            db_file.status = FileStatus.VECTORIZED
            session.add(db_file)
            session.commit()
            logger.info(f"向量化任务完成，文件ID: {db_file.id}")
        except Exception as e:
            logger.error(f"向量化任务失败，文件ID: {db_file.id}，错误信息: {e}")
            if 'db_file' in locals() and db_file:
                db_file.status = FileStatus.FAILED
                session.add(db_file)
                session.commit()
