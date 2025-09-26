from typing import Optional

from fastapi import Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

from app.core.auth import get_password_hash, verify_password, create_access_token
from app.db.db import engine, get_session  # Import engine
from sqlmodel import Session, select  # Import Session
from app.models.user import AdminUser, CreatUser
from app.core.exceptions import ApiException  # Import ApiException for rollback handling


def create_admin_user(
        userinfo: CreatUser,
        session: Session = Depends(get_session())) -> AdminUser:
    """创建一个后台用户"""
    admin_user = AdminUser()
    admin_user.username = userinfo.username
    admin_user.password = get_password_hash(userinfo.password)
    admin_user.email = userinfo.email
    session.add(admin_user)
    return admin_user

def update_admin_user(
        userinfo: CreatUser,
        session: Session) -> AdminUser:
    """更新一个后台用户"""
    admin_user = session.get(AdminUser, userinfo.id)
    if not admin_user:
        raise ApiException(msg="用户不存在")
    admin_user.username = userinfo.username
    admin_user.password = get_password_hash(userinfo.password)
    admin_user.email = userinfo.email
    session.add(admin_user)
    return admin_user

def delete_admin_user(
        user_id: int,
        session: Session) -> None:
    """删除一个后台用户"""
    admin_user = session.get(AdminUser, user_id)
    if not admin_user:
        raise ApiException(msg="用户不存在")
    session.delete(admin_user)

def get_admin_user(
        user_id: int,
        session: Session) -> AdminUser:
    """获取一个后台用户"""
    admin_user = session.get(AdminUser, user_id)
    if not admin_user:
        raise ApiException(msg="用户不存在")
    return admin_user

def query_admin_user(
        session: Session,
        username: Optional[str] = None,
        is_active: Optional[bool] = None) -> Page[AdminUser]:
    """分页查询后台用户"""
    # 构建查询语句
    statement = select(AdminUser)
    # 动态构建where条件
    if username is not None:
        statement = statement.where(AdminUser.username.contains(username))
    if is_active is not None:
        statement = statement.where(AdminUser.is_active == is_active)

    # 添加排序
    statement = statement.order_by(AdminUser.created_at)
    # 执行分页查询
    return paginate(session, statement)

def login(
        session:Session,
        username: Optional[str],
        password: Optional[str]
)->str:
    """用户登录"""
    statement = select(AdminUser).where(AdminUser.username == username)
    admin_user = session.exec(statement).first()
    if not admin_user or not verify_password(password, admin_user.password):
        raise ApiException(msg="用户名或密码错误")
    return create_access_token(admin_user.id, "admin")
