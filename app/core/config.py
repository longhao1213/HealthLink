from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# 构建到项目根目录的.env文件的绝对路径
# Path(__file__) -> app/core/config.py
# .parent -> app/core
# .parent -> app
# .parent -> project root
ENV_PATH = Path(__file__).parent.parent.parent / ".env"

class Settings(BaseSettings):
    """
    项目配置类
    自动从环境变量或 .env 文件中读取配置
    """
    # --- 数据库配置 (MySQL) ---
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # 拼接成SQLAlchemy的连接字符串
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # --- Redis 配置 ---
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str

    # --- MinIO 配置 ---
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool
    MINIO_DEFAULT_BUCKET: str

    # --- Milvus 配置 ---
    MILVUS_HOST: str
    MILVUS_PORT: int
    MILVUS_DB_NAME: str

    # --- 大语言模型 API Key ---
    # 重要提示: API密钥必须在.env文件中设置，而不是在这里硬编码。
    MODEL_KEY: str
    EMBEDDING_MODEL: str
    EMBEDDING_MODEL_URL: str
    TEXT_EMBEDDING_MODEL: str
    MODEL_URL: str
    MODE_NAME: str

    # --- ai业务相关 ---
    TEMP_MEMORY_SIZE: int

    # --- 项目配置 ---
    PROJECT_NAME: str

    # --- JWT 配置 ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_LOGIN_SUBJECT: str

    # Pydantic-Settings的配置类
    model_config = SettingsConfigDict(env_file=ENV_PATH, env_file_encoding='utf-8')

# 创建一个全局可用的配置实例
settings = Settings()
