import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi_pagination import Page
from sqlmodel import Session

from app.core.auth import get_current_user
# 注意：请确保您的项目路径是正确的
from app.db.db import get_session
from app.models.user import CreatUser, AdminUser
from app.schemas.json_response import JsonData
from app.services import admin_user_service

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/admin/user/v1",
    tags=["后台用户管理"],
)


@router.post("/create", summary="创建后台用户", response_model=JsonData)
def create_admin(userinfo: CreatUser, session: Session = Depends(get_session)) -> JsonData:
    """创建后台用户"""
    logger.info(f"创建后台用户：{userinfo}")
    admin_user = admin_user_service.create_admin_user(userinfo, session)
    return JsonData.success(admin_user)


@router.put("/update", summary="更新后台用户", response_model=JsonData)
def update_admin(userinfo: CreatUser, session: Session = Depends(get_session)) -> JsonData:
    """更新后台用户信息，需要在请求体中提供用户ID"""
    logger.info(f"更新后台用户ID：{userinfo.id}")
    updated_user = admin_user_service.update_admin_user(userinfo, session)
    return JsonData.success(updated_user)


@router.get("/query", summary="分页查询后台用户", response_model=Page[AdminUser])
def query_admins(
    *,
    session: Session = Depends(get_session),
    username: Optional[str] = Query(None, description="按用户名进行模糊查询"),
    is_active: Optional[bool] = Query(None, description="按账户激活状态查询"),
    admin_user: AdminUser = Depends(get_current_user)
) -> Page[AdminUser]:
    """
    分页并根据条件筛选后台用户

    - **username**: 用户名 (模糊查询)
    - **is_active**: 是否激活 (true/false)
    """
    logger.info("分页查询后台用户")
    logger.info(f"用户ID：{admin_user.id}")
    page_data = admin_user_service.query_admin_user(
        session=session,
        username=username,
        is_active=is_active,
    )
    return page_data


@router.delete("/{user_id}", summary="删除后台用户", response_model=JsonData)
def delete_admin(user_id: int, session: Session = Depends(get_session)) -> JsonData:
    """通过用户ID删除后台用户"""
    logger.info(f"删除后台用户ID：{user_id}")
    admin_user_service.delete_admin_user(user_id, session)
    return JsonData.success("删除成功")


@router.get("/{user_id}", summary="获取单个后台用户", response_model=JsonData)
def get_admin(user_id: int, session: Session = Depends(get_session)) -> JsonData:
    """通过用户ID获取后台用户详细信息"""
    logger.info(f"获取后台用户ID：{user_id}")
    user = admin_user_service.get_admin_user(user_id, session)
    return JsonData.success(user)

from fastapi.security import OAuth2PasswordRequestForm

# ... (其他代码)

@router.post("/login", summary="用户登录获取Token", response_model=JsonData)
def login(
    session: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> JsonData:
    """
    使用用户名和密码登录以获取JWT Token
    """
    logger.info(f"用户登录：{form_data.username}")
    token = admin_user_service.login(session, form_data.username, form_data.password)
    return JsonData.success(token)