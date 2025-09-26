from typing import Optional
from sqlmodel import Field
from app.models.base import BaseModel
from app.core.constants import FileStatus

class KnowledgeBase(BaseModel, table=True):
    """
    知识库表模型
    """
    __tablename__ = "knowledge_base"

    name: str = Field(max_length=255, nullable=False, description="知识库名称")
    description: Optional[str] = Field(default=None, description="知识库描述")
    admin_user_id: Optional[int] = Field(default=None, description="创建该知识库的管理员ID")

class KnowledgeFile(BaseModel, table=True):
    """
    知识库文件表模型
    """
    __tablename__ = "knowledge_file"

    filename: str = Field(max_length=255, nullable=False, description="原始文件名")
    file_ext: Optional[str] = Field(default=None, max_length=50, description="文件扩展名")
    mime_type: Optional[str] = Field(default=None, max_length=100, description="文件的MIME类型")
    size_in_bytes: Optional[int] = Field(default=None, description="文件大小（字节）")
    file_path: Optional[str] = Field(default=None, max_length=1024, description="文件在对象存储中的路径")
    file_hash: Optional[str] = Field(default=None, max_length=255, description="文件内容的哈希值")
    admin_user_id: Optional[int] = Field(default=None, description="上传文件的管理员ID")
    knowledge_base_id: Optional[int] = Field(default=None, description="所属知识库ID")
    upload_id: Optional[str] = Field(default=None, max_length=255, description="分片上传任务ID")
    status: str = Field(default=FileStatus.PENDING, max_length=50, nullable=False, description="文件处理状态")

class PatientFile(BaseModel, table=True):
    """
    患者上传文件表模型
    """
    __tablename__ = "patient_file"

    filename: str = Field(max_length=255, nullable=False, description="原始文件名")
    file_ext: Optional[str] = Field(default=None, max_length=50, description="文件扩展名")
    mime_type: Optional[str] = Field(default=None, max_length=100, description="文件的MIME类型")
    size_in_bytes: Optional[int] = Field(default=None, description="文件大小（字节）")
    file_path: str = Field(max_length=1024, nullable=False, description="文件在对象存储中的路径")
    file_hash: Optional[str] = Field(default=None, max_length=255, description="文件内容的哈希值")
    patient_user_id: Optional[int] = Field(default=None, description="上传文件的患者ID")
    upload_id: Optional[str] = Field(default=None, max_length=255, description="分片上传任务ID")
    status: str = Field(default=FileStatus.PENDING, max_length=50, nullable=False, description="文件处理状态")