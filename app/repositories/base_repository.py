from sqlalchemy.orm import Session

from app.core.database import db


class BaseRepository:
    """基础Repository类"""

    def __init__(self):
        self.db = db

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.db.get_session()

    def close_session(self, session: Session):
        """关闭数据库会话"""
        self.db.close_session(session)
