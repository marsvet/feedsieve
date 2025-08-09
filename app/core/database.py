import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import config

logger = logging.getLogger(__name__)


class Database:
    """数据库管理类"""

    def __init__(self):
        self.database_url = config.get_database_url()
        self.engine = None
        self.SessionLocal = None
        self._init_engine()

    def _init_engine(self):
        """初始化数据库引擎"""
        try:
            # 对于SQLite，使用同步引擎
            if self.database_url.startswith("sqlite"):
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                    echo=False,
                )
            else:
                self.engine = create_engine(self.database_url, echo=False)

            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            logger.info(f"数据库引擎初始化成功: {self.database_url}")
        except Exception as e:
            logger.error(f"数据库引擎初始化失败: {e}")
            raise RuntimeError(f"数据库引擎初始化失败: {e}")

    def create_tables(self):
        """创建数据库表"""
        try:
            # 需要导入模型来创建表
            from ..models import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"数据库表创建失败: {e}")
            raise RuntimeError(f"数据库表创建失败: {e}")

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    @contextmanager
    def get_session_context(self):
        """获取数据库会话上下文管理器"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"数据库操作失败: {e}")
        finally:
            session.close()

    def close_session(self, session: Session):
        """关闭数据库会话"""
        if session:
            session.close()

    def health_check(self) -> bool:
        """健康检查"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return False


# 全局数据库实例
db = Database()
