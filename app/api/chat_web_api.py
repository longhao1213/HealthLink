import logging

from fastapi import APIRouter, Depends
from sqlmodel import Session
from starlette.responses import StreamingResponse

from app.core.auth import get_current_admin_user
from app.db.db import get_session
from app.models.user import AdminUser
from app.schemas.chat_schema import ChatRequest
from app.schemas.json_response import JsonData
from app.agents.main_chat_agent import llm_service

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/web/chat/v1",
    tags=["web端ai调用管理"],
)

@router.post("/invoke",summary="web端非流式调用agent")
async def chat_invoke(
        request: ChatRequest,
        current_admin: AdminUser = Depends(get_current_admin_user),
        session: Session = Depends(get_session)
) -> JsonData:
    """
    web端非流式调用ai聊天
    :param request:
    :param current_admin:
    :param session:
    :return:
    """
    logger.info(f"接收到web端非流式聊天请求: {request}...")
    answer = llm_service.invoke(
        user_input= request.user_input
    )
    return JsonData.success(data={"answer": answer})

@router.post("/stream",summary="web端流式调用agent")
async def chat_stream(
        request: ChatRequest,
        current_admin: AdminUser = Depends(get_current_admin_user),
        session: Session = Depends(get_session)
):
    """
    web端流式调用ai聊天
    :param request:
    :param current_admin:
    :param session:
    :return:
    """
    logger.info(f"接收到web端流式聊天请求: {request}...")
    return StreamingResponse(
        llm_service.stream_invoke(user_input=request.user_input),
        media_type="text/event-stream",
    )
