import logging

import ijson
logging.basicConfig(level=logging.INFO)
data_path = "/Users/longhao/Downloads/Chinese-medical-dialogue/data/train_0001_of_0001.json"
batch_size = 500
logger = logging.getLogger(__name__)

def stream_json_data(data_path:str):
    """
    流式读取大json文件
    :param data_path:
    :return:
    """
    with open(data_path, 'rb') as file:
        batch = []
        parse = ijson.items(file, 'item')
        total_processed = 0
        for item in parse:
            batch.append(item)
            if len(batch) >= batch_size:
                # todo 开始转换
                # vector(batch)
                total_processed += len(batch)
                logger.info(f"已处理{total_processed}条数据...")
                # 清空数据
                batch = []
    if batch:
        # 处理最后一波数据
        logger.info("处理最后的数据")

stream_json_data(data_path)