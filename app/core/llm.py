import logging

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)
_model = ChatOpenAI(
    model=settings.MODE_NAME,
    base_url=settings.MODEL_URL,
    api_key=settings.MODEL_KEY,
    temperature=0.2,
    streaming=True,
    max_retries=3, # 最大重试次数
    extra_body={   # 显式指定额外参数，而不是通过model_kwargs
        "enable_search": True
    }
)

_embeddings = DashScopeEmbeddings(
    model=settings.TEXT_EMBEDDING_MODEL,
    max_retries=3,
    dashscope_api_key=settings.MODEL_KEY,
)

def get_default_llm() -> ChatOpenAI:
    """
    获取默认llm对象
    :return:
    """
    logger.info(f"Model config: model={settings.MODE_NAME}, base_url={settings.MODEL_URL}")
    logger.info(f"API Key exists: {bool(settings.MODEL_KEY)}")
    return _model

def get_default_embeddings() -> DashScopeEmbeddings:
    """
    获取默认embeddings对象
    :return:
    """
    return _embeddings