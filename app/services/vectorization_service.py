import json
import logging
import os
import tempfile
from contextlib import contextmanager
from io import BytesIO

import requests
from langchain_community.embeddings import DashScopeEmbeddings

from app.services.milvus_service import milvus_service

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlmodel import Session

from app.core.config import settings
from app.core.constants import SupportedMimeTypes, FileStatus
from app.models.knowledge import KnowledgeFile
from app.services.minio_service import minio_service
from app.db.db import engine
from langchain_community.document_loaders import (
    TextLoader,          #文本加载
    PyPDFLoader,          # PDF
    Docx2txtLoader,       # Word
    UnstructuredFileLoader, # 通用文件加载器
    CSVLoader,            # CSV
    JSONLoader,           # JSON
    WebBaseLoader          #网页加载
)

"""
向量转换
"""
logger = logging.getLogger(__name__)

# 初始化embedding
try:
    embeddings = DashScopeEmbeddings(
    model=settings.TEXT_EMBEDDING_MODEL,
    max_retries=3,
    dashscope_api_key=settings.MODEL_KEY,
)
    logger.info(f"成功初始化embedding模型: {settings.TEXT_EMBEDDING_MODEL}")
except Exception as e:
    logger.error(f"初始化embedding模型失败: {e}")

# 定义文档加载器的类型映射
LOADER_MAPPING = {
    SupportedMimeTypes.PDF.value: PyPDFLoader,
    SupportedMimeTypes.DOCX.value: Docx2txtLoader,
    SupportedMimeTypes.TXT.value: TextLoader,
    SupportedMimeTypes.DOC.value: UnstructuredFileLoader,
    SupportedMimeTypes.CSV.value: CSVLoader,
    SupportedMimeTypes.JSON.value: JSONLoader,
    SupportedMimeTypes.WEB_URL.value: WebBaseLoader,
    # TODO 还可以添加更多支持的类型
}
# 创建一个集合，存放需要启用OCR的复杂文档类型
OCR_ENABLED_MIME_TYPES = {
    SupportedMimeTypes.PDF.value,
    SupportedMimeTypes.DOCX.value,
    SupportedMimeTypes.DOC.value,
    SupportedMimeTypes.WEB_URL.value,
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
                api_key = settings.MODEL_KEY
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
                if not file_data and db_file.mime_type != SupportedMimeTypes.WEB_URL.value:
                    logger.error(f"向量化任务失败，无法下载文件: {db_file.id}")
                    return
                # 把文件内容读取到内存中
                file_stream = BytesIO(file_data)
                # 加载文档
                logger.info(f"正在加载文件内容，MIME Type：{db_file.mime_type}")
                docs = []
                loader_class = LOADER_MAPPING.get(db_file.mime_type)
                logger.info(f"获取的加载器类型：{loader_class}")
                if not loader_class:
                    logger.error(f"向量化任务失败，不支持的MIME Type: {db_file.mime_type}")
                    return
                with as_temp_file(file_stream, suffix=db_file.file_ext) as temp_path:
                    loader_kwargs = {}
                    # 针对不同类型的文档做一些关于ocr的处理
                    if db_file.mime_type in OCR_ENABLED_MIME_TYPES:
                        loader_kwargs['strategy'] = "hi_res"
                        loader_kwargs['ocr_languages'] = "ch_sim+en"
                        loader_kwargs['mode'] = "elements"
                        logger.info(f"为 {db_file.mime_type} 文件启用OCR策略。")
                        if loader_class is WebBaseLoader:
                            loader = WebBaseLoader([db_file.file_path], **loader_kwargs)
                            docs = loader.load()
                        else:
                            loader = loader_class(temp_path, **loader_kwargs)
                            docs = loader.load()
                    else:
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
                    # 添加调试信息
                    logger.debug(f"切分后的文本块数量: {len(chunk_texts)}")
                else:
                    logger.warning("文档加载器未返回任何内容")
                    chunk_texts = []

                # 生成向量
                if not embeddings:
                    raise ConnectionError("无法初始化embedding模型")
                logger.info(f"正在生成向量，向量数量：{len(chunk_texts)}")
                # 修复：确保chunk_texts不为空且都是字符串
                if not chunk_texts:
                    logger.warning("没有文本需要向量化")
                    vectors = []
                else:
                    # 确保所有chunk都是字符串并且长度合适
                    validated_texts = []
                    for chunk in chunk_texts:
                        str_chunk = str(chunk)
                        # 过滤掉空字符串和只包含空白字符的字符串
                        if str_chunk and str_chunk.strip():
                            # 限制文本长度以避免API限制
                            if len(str_chunk) > 10000:  # 限制长度到10000字符
                                str_chunk = str_chunk[:10000]
                                logger.warning("文本过长，已截断到10000字符")
                            validated_texts.append(str_chunk)
                    
                    if validated_texts:
                        # 添加调试信息
                        logger.debug(f"验证后的文本数量: {len(validated_texts)}")
                        for i, text in enumerate(validated_texts):
                            logger.debug(f"验证后文本 {i+1} 长度: {len(text)} 字符")
                        
                        # 修复：确保传递给embed_documents的文本符合要求
                        try:
                            vectors = embeddings.embed_documents(validated_texts)
                        except Exception as embed_error:
                            logger.error(f"向量化过程中发生错误: {embed_error}")
                            logger.error(f"错误类型: {type(embed_error)}")
                            # 尝试单个文本向量化以定位问题
                            vectors = []
                            for i, text in enumerate(validated_texts):
                                try:
                                    text_vector = embeddings.embed_query(text)
                                    vectors.append(text_vector)
                                    logger.info(f"成功向量化文本段 {i+1}/{len(validated_texts)}")
                                except Exception as single_error:
                                    logger.error(f"单个文本向量化失败 (文本段 {i+1}): {single_error}")
                                    # 添加空向量作为占位符，确保索引对齐
                                    vectors.append([])
                    else:
                        logger.warning("没有有效的文本内容需要向量化")
                        vectors = []
                logger.info(f"向量生成完成，向量数量：{len(vectors)}")

                # 把数据存储到向量数据库
                entities_to_insert = []
                if vectors and len(vectors) == len(chunk_texts):  # 修复：确保向量和文本数量匹配
                    for text, vec in zip(chunk_texts, vectors):
                        # 只有当向量非空时才插入
                        if vec:
                            entities_to_insert.append({
                                "file_id": db_file.id,
                                "knowledge_base_id": db_file.knowledge_base_id,
                                "chunk_text": text,
                                "vector": vec
                            })
                    if entities_to_insert:
                        milvus_service.insert(entities_to_insert)
                        logger.info(f"向量存储完成，向量数量：{len(entities_to_insert)}")
                else:
                    logger.warning("向量数量与文本数量不匹配或没有有效向量")
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
