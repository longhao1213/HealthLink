import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class BaseModel(SQLModel):
    """
    所有数据模型的基类，包含通用字段。
    """
    id: Optional[int] = Field(default=None, primary_key=True, description="主键ID (雪花ID)")

    created_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
        description="创建时间"
    )

    updated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
        sa_column_kwargs={"onupdate": lambda: datetime.datetime.now(datetime.timezone.utc)},
        description="更新时间"
    )

    is_deleted: bool = Field(default=False, nullable=False, description="是否逻辑删除")