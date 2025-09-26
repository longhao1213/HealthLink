from pydantic import BaseModel, Field
from typing import Optional

class UploadRequest(BaseModel):
    filename: str = Field(..., description="文件名")
    file_ext: Optional[str] = Field(None, description="文件扩展名")
    mime_type: Optional[str] = Field(None, description="文件的MIME类型")
    size_in_bytes: Optional[int] = Field(None, description="文件大小（字节）")
    part_count: int = Field(1, description="文件被切分的总块数，默认为1（不分片）")
    knowledge_base_id: Optional[int] = Field(None, description="所属知识库ID")
    file_hash: Optional[str] = Field(None, description="文件的哈希值")

class CompleteUploadRequest(BaseModel):
    file_id: int = Field(..., description="文件ID")
