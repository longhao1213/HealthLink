import logging

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        """
        初始化异步redis连接池
        """
        self.pool = None

        try:
            # 创建一个异步连接池 decode_responses=True 会自动将从Redis获取的bytes解码为utf-8字符串
            self.pool = redis.ConnectionPool.from_url(
                f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                decode_responses=True
            )
            logger.info(f"成功创建Redis连接池: {self.pool}")
        except Exception as e:
            logger.error(f"创建Redis连接池失败: {e}")

    def get_client(self) -> redis.Redis:
        """
        从连接池中获取一个redis客户端
        异步
        :return:
        """
        if not self.pool:
            raise ConnectionError("Redis连接池未初始化")
        return redis.Redis(connection_pool=self.pool)

# 创建一个全局的redisService实例
redis_service = RedisService()