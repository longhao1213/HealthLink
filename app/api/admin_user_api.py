import logging

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.db import get_session
from app.models.user import CreatUser
from app.schemas.json_response import JsonData
from app.services.admin_user_service import create_admin_user

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/admin/user/v1",
    tags=["后台用户管理"],
)

@router.post("/create",summary="创建后台用户",response_model=JsonData)
def create_admin(userinfo:CreatUser, session: Session = Depends(get_session)) -> JsonData:
    """创建后台用户"""
    logger.info(f"f创建后台用户：{userinfo}")
    admin_user = create_admin_user(userinfo,session)
    return JsonData.success(admin_user)