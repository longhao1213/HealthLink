import logging
from typing import List

import ijson
from langchain_community.document_loaders import JSONLoader
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
data_path = "/Users/longhao/Downloads/Chinese-medical-dialogue/data/train_0001_of_0001.json"
batch_size = 500
continue_position = 36000

_embeddings = DashScopeEmbeddings(
    model=settings.TEXT_EMBEDDING_MODEL,
    max_retries=3,
    dashscope_api_key=settings.MODEL_KEY,
)

connections.connect(
    alias="default",
    host=settings.MILVUS_HOST,
    port=settings.MILVUS_PORT
)
logger.info(f"成功连接到Milvus")
fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="file_id", dtype=DataType.INT64, description="关联的源文件id"),
            FieldSchema(name="knowledge_base_id", dtype=DataType.INT64, description="关联的知识库id"),
            FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=4000, description="分块的文本内容"),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1024, description="向量表示")
        ]
collection = Collection(name="health_documents", schema=CollectionSchema(fields=fields, description="医疗健康文档合集", enable_dynamic_field=False))

def stream_json_data(data_path:str):
    """
    流式读取大json文件
    :param data_path:
    :return:
    """
    with open(data_path,'rb') as file:
        batch = []
        parse = ijson.items(file,'item')
        total_processed = 0
        for item in parse:
            batch.append(item)
            if total_processed > continue_position and len(batch) >= batch_size:
                # todo 开始转换
                vector( batch)
                total_processed += len(batch)
                logger.info(f"已处理{total_processed}条数据...")
                # 清空数据
                batch = []
    if batch:
        # 处理最后一波数据
        logger.info("处理最后的数据")

def vector(data:List):
    """
    向量化数据
    :param data:
    :return:
    """
    # 创建文本分块器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2500,      # 每块最大2500字符
        chunk_overlap=200,    # 块之间重叠200字符
    )
    # 处理数据并进行文本分块
    chunked_texts = []  # 存储分块后的文本
    chunk_metadata = []  # 存储分块的元数据（如原始数据索引）
    texts_to_embed = []
    # 处理数据
    for i,item in enumerate(data):
        instruction = item.get("instruction", "")
        input_text = item.get("input", "")
        output_text = item.get("output", "")
        full_text = f"问题：{instruction}\n详细信息：{input_text}\n回答：{output_text}"

        # 对长文本进行分块
        chunks = text_splitter.split_text(full_text)
        # 对每个块保存文本和数据
        for j,chunk in enumerate(chunks):
            chunked_texts.append(chunk)
            chunk_metadata.append({
                "original_index": i,  # 原始数据索引
                "chunk_index": j,  # 块索引
                "total_chunks": len(chunks)  # 总块数
            })
        # texts_to_embed.append(full_text)
    # 向量化数据
    vectors = _embeddings.embed_documents(chunked_texts)
    # 封装一个dict key为原始文本，value为向量
    save_data = []
    for i,(text, meta) in enumerate(zip(chunked_texts, chunk_metadata)):
        save_data.append({
            "chunk_text": text,
            "vector": vectors[i],
            "file_id": -1,
            "knowledge_base_id": -1
        })

    # 拿到了完整的向量，开始调用milvus数据存储
    save_to_milvus(save_data)

def save_to_milvus(data:List):
    """
    保存数据到数据库
    :param data:
    :return:
    """
    # 提取字段

    # 处理数据
    data_to_insert = [
        [item["file_id"] for item in data],
        [item["knowledge_base_id"] for item in data],
        [item["chunk_text"] for item in data],
        [item["vector"] for item in data]
    ]
    # for item in data:
    # )
    # transposed_data = list(zip(*data_to_insert))
    collection.insert(data_to_insert)
    logger.info(f"向量保存成功")


stream_json_data(data_path)