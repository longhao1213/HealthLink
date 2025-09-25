from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlmodel import Session

from app.core.config import settings
from app.db.db import get_session
from app.models.user import AdminUser, PatientUser

# 1. Password Hashing Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. OAuth2 Scheme Setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/token")

# 3. Password Utility Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码和哈希密码是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码的哈希值"""
    return pwd_context.hash(password)

# 4. JWT Generation Function
def create_access_token(subject: Any, user_type: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    :param subject: 令牌的主题，通常是用户ID
    :param user_type: 用户类型 ('admin' or 'patient')
    :param expires_delta: 令牌的有效时间
    :return: JWT令牌字符串
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "user_type": user_type}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

# 5. User Retrieval Dependencies
UserType = Union[AdminUser, PatientUser]

def get_current_user(
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme)
) -> UserType:
    """
    解析JWT令牌，验证用户，并返回用户模型对象。
    这是一个核心依赖，供其他特定角色的依赖调用。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        user_type: str = payload.get("user_type")
        if user_id is None or user_type is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 根据user_type从正确的表中查找用户
    user_model = None
    if user_type == "admin":
        user_model = AdminUser
    elif user_type == "patient":
        user_model = PatientUser
    else:
        raise credentials_exception

    user = session.get(user_model, int(user_id))
    if user is None or user.is_deleted or not user.is_active:
        raise credentials_exception
    
    return user

def get_current_admin_user(
    current_user: UserType = Depends(get_current_user)
) -> AdminUser:
    """
    获取当前登录的后台管理员用户。
    如果当前用户不是管理员，则抛出权限不足的异常。
    """
    if not isinstance(current_user, AdminUser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="没有足够权限"
        )
    return current_user

def get_current_patient_user(
    current_user: UserType = Depends(get_current_user)
) -> PatientUser:
    """
    获取当前登录的患者用户。
    如果当前用户不是患者，则抛出权限不足的异常。
    """
    if not isinstance(current_user, PatientUser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="没有足够权限"
        )
    return current_user

