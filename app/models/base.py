from datetime import datetime, timezone
from sonyflake import Sonyflake
from sqlmodel import Field, SQLModel

# 初始化 Sonyflake 生成器
# start_time 是计算时间戳的起始时间点
# 你可以根据需要配置机器ID等参数
sonyflake = Sonyflake(start_time=datetime(2023, 1, 1, tzinfo=timezone.utc))

def generate_snowflake_id():
    """生成雪花ID"""
    return sonyflake.next_id()

def get_utc_now():
    """返回当前UTC时间"""
    return datetime.now(timezone.utc)


class BaseModel(SQLModel):
    """
    所有数据模型的基类，包含通用字段。
    """
    id: int = Field(default_factory=generate_snowflake_id, primary_key=True, description="主键ID (雪花ID)")

    created_at: datetime = Field(
        default_factory=get_utc_now,
        nullable=False,
        description="创建时间 (UTC)"
    )

    updated_at: datetime = Field(
        default_factory=get_utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": get_utc_now},
        description="更新时间 (UTC)"
    )

    is_deleted: bool = Field(default=False, nullable=False, description="是否逻辑删除")