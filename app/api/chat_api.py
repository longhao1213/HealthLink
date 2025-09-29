import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.db.db import get_session
from app.schemas.json_response import JsonData
from app.services.llm_service import llm_service
from app.core.auth import get_current_admin_user, UserType

logger = logging.getLogger(__name__)

# 修正路由前缀，使其与功能匹配
router = APIRouter(
    prefix="/api/chat/v1",
    tags=["AI聊天管理"],
)


@router.post("/invoke", summary="非流式调用Agent")
def chat_invoke(
        request: str,
        session: Session = Depends(get_session),
        current_admin: UserType = Depends(get_current_admin_user)
) -> JsonData:
    """
    以一次性请求的方式与Agent进行对话，等待完整回答。
    """
    logger.info(f"接收到非流式聊天请求: {request}...")

    # 调用非流式服务
    answer = llm_service.invoke(
        user_input=request
    )

    return JsonData.success(data={"answer": answer})


@router.post("/stream", summary="流式调用Agent")
def chat_stream(
        request: str,
        session: Session = Depends(get_session),
        current_admin: UserType = Depends(get_current_admin_user)
):
    """
    以流式响应（Server-Sent Events）的方式与Agent进行对话。
    """
    logger.info(f"接收到流式聊天请求: {request}...")

    # 调用流式服务，它会返回一个生成器
    response_generator = llm_service.stream_invoke(
        user_input=request
    )

    # 使用StreamingResponse将生成器包装成HTTP响应
    return StreamingResponse(response_generator, media_type="text/event-stream")
