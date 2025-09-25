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
