from fastapi import Depends

from app.core.auth import get_password_hash
from app.db.db import engine, get_session  # Import engine
from sqlmodel import Session  # Import Session
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
        session: Session = Depends(get_session())) -> AdminUser:
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
        session: Session = Depends(get_session())) -> None:
    """删除一个后台用户"""
    admin_user = session.get(AdminUser, user_id)
    if not admin_user:
        raise ApiException(msg="用户不存在")
    session.delete(admin_user)

def get_admin_user(
        user_id: int,
        session: Session = Depends(get_session())) -> AdminUser:
    """获取一个后台用户"""
    admin_user = session.get(AdminUser, user_id)
    if not admin_user:
        raise ApiException(msg="用户不存在")
    return admin_user