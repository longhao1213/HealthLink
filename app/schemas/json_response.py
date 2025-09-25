from typing import Optional, Any, Literal

from pydantic import BaseModel


class JsonData(BaseModel):
    """通用的数据响应模型"""
    code:int  = 0 # 状态码
    data: Optional[Any] = None # 响应数据
    msg: str = "" # 响应消息
    type: Literal["stream","text"] = "text" # 响应类型 Literal限定只能是stream或者text

    @classmethod
    def success(cls,data:Any = None) -> "JsonData":
        """成功响应"""
        return cls(code=0,data=data,type="text")

    @classmethod
    def error(cls,msg:str = "error",code:int = -1)-> "JsonData":
        """错误响应"""
        return cls(code=code,msg=msg,type="text")

    @classmethod
    def stream(cls,data:Any = None,msg:str = "")-> "JsonData":
        """流式响应"""
        return cls(code=0,data=data,msg=msg,type="stream")
