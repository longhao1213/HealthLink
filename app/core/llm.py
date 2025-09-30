from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import settings

_model = ChatOpenAI(
    model=settings.MODE_NAME,
    base_url=settings.MODEL_URL,
    api_key=settings.MODEL_KEY,
    temperature=0.2,
    streaming=True,
    max_retries=3, # 最大重试次数
    model_kwargs={ # 额外参数，这里配置了联网搜索
        "extra_body": {
            "enable_search": True
        }
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
    return _model

def get_default_embeddings() -> DashScopeEmbeddings:
    """
    获取默认embeddings对象
    :return:
    """
    return _embeddings