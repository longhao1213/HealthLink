from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# 显式加载 .env 文件
load_dotenv()

class Settings(BaseSettings):
    """
    项目配置类
    自动从环境变量或 .env 文件中读取配置
    """
    # --- 数据库配置 (MySQL) ---
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "user"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "healthlink"
    # 拼接成SQLAlchemy的连接字符串
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # --- Redis 配置 ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # --- MinIO 配置 ---
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_DEFAULT_BUCKET: str = "healthlink"

    # --- Milvus 配置 ---
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_DB_NAME: str = "healthlink_db"

    # --- 大语言模型 API Key ---
    EMBEDDING_MODEL: str = "multimodal-embedding-v1"
    EMBEDDING_MODEL_URL: str = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/multimodal-embedding/multimodal-embedding"
    TEXT_EMBEDDING_MODEL:str = "text-embedding-v4"
    MODEL_URL:str =  "https://dashscope.aliyuncs.com/compatible-mode/v1"
    MODEL_KEY:str = "sk-42e1606eea99432fa7062fde563ea3d2"
    MODE_NAME:str = "qwen3-max"

    # --- ai业务相关 ---
    TEMP_MEMORY_SIZE: int = 10

    # --- 项目配置 ---
    PROJECT_NAME: str = "HealthLink AI Assistant"

    # --- JWT 配置 ---
    JWT_SECRET_KEY: str = "a_very_secret_key_that_should_be_changed"  # IMPORTANT: Should be loaded from .env in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    JWT_LOGIN_SUBJECT: str = "HealthLink"

    # Pydantic-Settings的配置类
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

# 创建一个全局可用的配置实例
settings = Settings()
