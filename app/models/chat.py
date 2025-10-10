from typing import Optional
from sqlmodel import Field, TEXT
from app.models.base import BaseModel
from sqlalchemy import Column

class ChatSession(BaseModel, table=True):
    """
    聊天会话表模型
    """
    __tablename__ = "chat_session"

    user_id: int = Field(nullable=False, description="用户ID")
    topic: Optional[str] = Field(default=None, max_length=255, description="会话主题")

class ChatMessage(BaseModel, table=True):
    """
    聊天记录表模型
    """
    __tablename__ = "chat_message"

    session_id: int = Field(nullable=False, description="所属会话ID")
    role: str = Field(max_length=50, nullable=False, description="消息发送者角色 (user or assistant)")
    content: str = Field(sa_column=Column(TEXT, nullable=False), description="消息内容")

class Memory(BaseModel, table=True):
    """
    用户记忆表模型
    """
    __tablename__ = "memory"

    user_id: int = Field(nullable=False, description="用户患者ID")
    summary: str = Field(sa_column=Column(TEXT, nullable=False), description="关键信息摘要")
    source_session_id: Optional[int] = Field(default=None, description="该记忆来源的会话ID")