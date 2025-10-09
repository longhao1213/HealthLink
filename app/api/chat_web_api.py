import logging

from fastapi import APIRouter, Depends
from sqlmodel import Session
from starlette.responses import StreamingResponse

from app.core.auth import get_current_admin_user
from app.db.db import get_session
from app.models.user import AdminUser
from app.schemas.chat_schema import ChatRequest
from app.schemas.json_response import JsonData
from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/web/chat/v1",
    tags=["web端ai调用管理"],
)

@router.post("/invoke",summary="web端非流式调用agent")
async def chat_invoke(
        request: ChatRequest,
        current_user: AdminUser = Depends(get_current_admin_user),
        session: Session = Depends(get_session)
) -> JsonData:
    """
    web端非流式调用ai聊天
    :param request:
    :param current_user:
    :param session:
    :return:
    """
    logger.info(f"接收到web端非流式聊天请求: {request}...")
    answer = chat_service.invoke(
        user_input= request,session=session, current_user=current_user
    )
    return JsonData.success(data={"answer": answer})

@router.post("/stream",summary="web端流式调用agent")
async def chat_stream(
        request: ChatRequest,
        current_user: AdminUser = Depends(get_current_admin_user),
        session: Session = Depends(get_session)
):
    """
    web端流式调用ai聊天
    :param request:
    :param current_user:
    :param session:
    :return:
    """
    logger.info(f"接收到web端流式聊天请求: {request}...")
    return StreamingResponse(
        chat_service.stream_invoke(user_input= request,session=session, current_user=current_user),
        media_type="text/event-stream",
    )
