"""
公共依赖项

定义在控制器中使用的依赖项，如认证、数据库会话等
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .config import config
from .database import db

security = HTTPBasic()


def get_database_session():
    """获取数据库会话依赖项"""
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


def get_current_user(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """验证当前用户"""
    auth_config = config.get_auth()

    if (
        credentials.username != auth_config["username"]
        or credentials.password != auth_config["password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
