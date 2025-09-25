from typing import Optional
from sqlmodel import Field
from app.models.base import BaseModel

class AdminUser(BaseModel, table=True):
    """
    后台用户表模型
    """
    __tablename__ = "admin_user"

    username: str = Field(max_length=255, nullable=False, unique=True, description="用户名，用于登录")
    password: str = Field(max_length=255, nullable=False, description="加密后的密码")
    full_name: Optional[str] = Field(default=None, max_length=255, description="用户全名")
    email: Optional[str] = Field(default=None, max_length=255, unique=True, description="电子邮箱")
    is_active: bool = Field(default=True, nullable=False, description="账户是否激活")

class PatientUser(BaseModel, table=True):
    """
    患者用户表模型
    """
    __tablename__ = "patient_user"

    username: str = Field(max_length=255, nullable=False, unique=True, description="用户名，用于登录")
    password: str = Field(max_length=255, nullable=False, description="加密后的密码")
    phone:str = Field(max_length=11,nullable=False,description="手机号")
    full_name: Optional[str] = Field(default=None, max_length=255, description="患者全名")
    email: Optional[str] = Field(default=None, max_length=255, unique=True, description="电子邮箱")
    is_active: bool = Field(default=True, nullable=False, description="账户是否激活")

class CreatUser(BaseModel,table=False):
    """
    用于创建用户
    """
    username: str = Field(max_length=255, nullable=False, unique=True, description="用户名，用于登录")
    password: str = Field(max_length=255, nullable=False, description="密码")
    phone: str = Field(default=None,max_length=11, nullable=False, description="手机号")
    email: Optional[str] = Field(default=None, max_length=255, unique=True, description="电子邮箱")