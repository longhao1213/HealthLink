from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    user_input: str = Field(..., description="用户的当前问题或输入")
    chat_history: Optional[List[Dict[str, Any]]] = Field(None, description="对话历史记录")
