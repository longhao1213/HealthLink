import logging
from pymilvus import (
    connections,
    utility,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
)
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)
#向量集合名称
DEFAULT_COLLECTION_NAME = "health_documents"
# 向量维度
VECTOR_DIMENSION = 1024

class MilvusService:
    def __init__(self):
        """
        初始化milvus连接，并确保collection存在
        """
        try:
            logger.info(f"尝试连接到 Milvus: host={settings.MILVUS_HOST}, port={settings.MILVUS_PORT}")
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT
            )
            logger.info(f"成功连接到Milvus")
            self._ensure_collection_exists()
        except Exception as e:
            logger.error(f"初始化Milvus失败: {e}")
            raise ConnectionError("无法连接到Milvus服务") from e

    def _ensure_collection_exists(self):
        """
        内部方法，用来检测并创建所需的Collection和索引
        :return:
        """
        try:
            if not utility.has_collection(DEFAULT_COLLECTION_NAME):
                fields = [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="file_id", dtype=DataType.INT64, description="关联的源文件id"),
                    FieldSchema(name="knowledge_base_id", dtype=DataType.INT64, description="关联的知识库id"),
                    FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=4000, description="分块的文本内容"),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIMENSION, description="向量表示")
                ]
                schema = CollectionSchema(fields=fields, description="医疗健康文档合集", enable_dynamic_field=False)
                self.collection = Collection(name=DEFAULT_COLLECTION_NAME, schema=schema)
                index_params = {
                    "metric_type": "L2",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 1024},
                }
                self.collection.create_index(field_name="vector", index_params=index_params)
                logger.info(f"成功创建Milvus Collection: '{DEFAULT_COLLECTION_NAME}'")
            else:
                self.collection = Collection(name=DEFAULT_COLLECTION_NAME)
                logger.info(f"已找到Milvus Collection: '{DEFAULT_COLLECTION_NAME}'")
            # 加载collection到内存
            self.collection.load()
        except Exception as e:
            logger.error(f"创建Milvus Collection失败: {e}")
            raise ConnectionError("无法创建Milvus Collection") from e

    async def insert(self, entities: List[Dict[str, Any]]) -> List[int]:
        """
        批量插入实体
        :param entities: 一个字典列表，每个字典包含 'file_id', 'knowledge_base_id', 'chunk_text', 'vector'
        :return:插入记录的主键ID列表。
        """
        if not entities:
            return []
        try:
            # 组织数据
            data_to_insert = [
                [entity["file_id"] for entity in entities],
                [entity["knowledge_base_id"] for entity in entities],
                [entity["chunk_text"] for entity in entities],
                [entity["vector"] for entity in entities],
            ]
            # 插入
            mutation_result = self.collection.insert(data_to_insert)
            # 确保数据被写入
            self.collection.flush()
            logger.info(f"成功向milvus插入{mutation_result.insert_count}条数据")
            return mutation_result.primary_keys
        except Exception as e:
            logger.error(f"插入数据失败: {e}")
            raise ValueError("插入数据失败") from e

    async def search(self, query_vector: List[float], top_k: int = 5, knowledge_base_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        执行向量搜索
        :param query_vector: 用于查询到单条向量
        :param top_k: 返回最相似结果的数量
        :param knowledge_base_id: （可选）用于过滤的知识库id
        :return: 一个结果表，每个结果包含距离、ID和所有输出字段
        """
        search_params = {"metric_type": "L2",
                         "params": {"nprobe": 16}# nprobe是查询时要搜索的聚类数量
                         }
        expr = f"knowledge_base_id == {knowledge_base_id}" if knowledge_base_id else ""
        try:
            results = self.collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["file_id", "chunk_text", "knowledge_base_id"],
            )
            # 解析并且格式化结果
            formatted_results = []
            for hit in results[0]: # results[0] 对应第一个查询向量的结果
                entity = hit.entity
                formatted_results.append({
                    "id": hit.id,
                    "distance": hit.distance,
                    "file_id": entity.get("file_id"),
                    "knowledge_base_id": entity.get("knowledge_base_id"),
                    "chunk_text": entity.get("chunk_text"),
                })
            return formatted_results
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []

    async def delete_by_file_id(self, file_id: int) -> int:
        """
        根据文件ID删除相关的向量记录
        :param file_id: 文件ID
        :return: 被删除的记录数量
        """
        expr = f"file_id == {file_id}"
        try:
            delete_result = self.collection.delete(expr)
            self.collection.flush()
            logger.info(f"从Milvus中删除了 {delete_result.delete_count} 条与File ID {file_id} 相关的记录。")
            return delete_result.delete_count
        except Exception as e:
            logger.error(f"删除数据失败: {e}")
            return 0

milvus_service = MilvusService()
