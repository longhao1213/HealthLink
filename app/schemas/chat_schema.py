from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    user_input: str = Field(..., description="用户的当前问题或输入")
    session_id: Optional[int] = Field(None, description="会话ID")
