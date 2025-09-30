import sys
import os
import logging
from typing import List, Dict, Any

# ----------------- 设置项目根路径 -----------------
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# ----------------- 配置日志 -----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ----------------- 导入模块 -----------------
from modelscope.msdatasets import MsDataset
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- 导入我们自己的服务和函数 ---
from app.core.llm import get_default_embeddings
from app.services.milvus_service import milvus_service

# ----------------- 配置区 -----------------
DATASET_NAME = "xiaofengalg/Chinese-medical-dialogue"
DATASET_SPLIT = "train"
TEXT_FIELDS = ["ask", "answer"]
BATCH_SIZE = 128

def process_and_insert_batch(batch_entities: List[Dict[str, Any]], embeddings):
    """
    处理一个批次的实体：向量化并插入Milvus。
    """
    if not batch_entities:
        return

    texts_to_embed = [entity["chunk_text"] for entity in batch_entities]
    
    logging.info(f"正在为 {len(texts_to_embed)} 个文本块生成向量...")
    try:
        if not embeddings:
            raise ConnectionError("Embedding模型未成功初始化")

        vectors = embeddings.embed_documents(texts_to_embed)
        
        for i, entity in enumerate(batch_entities):
            entity["vector"] = vectors[i]
            
        milvus_service.insert(entities=batch_entities)
        logging.info(f"成功插入 {len(batch_entities)} 条记录到Milvus。")

    except Exception as e:
        logging.error(f"处理批次时发生错误: {e}", exc_info=True)

def main():
    """
    主函数：加载数据集，处理并存入向量数据库。
    """
    # 1. 获取向量模型实例
    embeddings = get_default_embeddings()
    if not embeddings:
        logging.error("无法获取Embedding模型，脚本终止。")
        return

    logging.info(f"开始从ModelScope加载数据集: {DATASET_NAME}")
    try:
        # 使用MsDataset.load来加载魔搭社区的数据集
        dataset = MsDataset.load(DATASET_NAME, split=DATASET_SPLIT)
    except Exception as e:
        logging.error(f"加载数据集失败: {e}")
        return

    logging.info("数据集加载成功！开始处理...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    batch_to_insert = []
    total_chunks = 0

    for i, item in enumerate(dataset):
        question = item.get("ask", "")
        answer = item.get("answer", "")
        full_text = f"问题：{question}\n回答：{answer}"
        
        if not full_text.strip():
            continue

        chunks = text_splitter.split_text(full_text)
        
        for chunk_text in chunks:
            entity = {
                "file_id": i, 
                "knowledge_base_id": 1, # 假设都属于知识库1
                "chunk_text": chunk_text,
                "vector": []
            }
            batch_to_insert.append(entity)
            
            if len(batch_to_insert) >= BATCH_SIZE:
                process_and_insert_batch(batch_to_insert, embeddings)
                total_chunks += len(batch_to_insert)
                batch_to_insert = []

        if (i + 1) % 1000 == 0:
            logging.info(f"已处理 {i + 1} 条原始数据...")

    if batch_to_insert:
        process_and_insert_batch(batch_to_insert, embeddings)
        total_chunks += len(batch_to_insert)

    logging.info(f"所有数据处理完毕！总共插入了 {total_chunks} 个文本块到Milvus。")

if __name__ == "__main__":
    main()
