"""
数据库模型定义

使用 SQLAlchemy ORM 定义数据库表结构
"""

import json

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, TypeDecorator
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from ..core.constants import RecordStatus


class UnicodeJSON(TypeDecorator):
    """自定义JSON类型，确保中文字符不被转义"""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


Base = declarative_base()


class Record(Base):
    """记录表 - 存储所有处理记录"""

    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    feed_url = Column(String(1000), nullable=False, index=True)  # Feed URL
    title = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)  # LLM生成的内容摘要
    article_url = Column(String(1000), nullable=True)
    status = Column(
        String(20),
        nullable=False,
        default=RecordStatus.FAILED,
        index=True
    )  # skip, success_filtered, success_unfiltered, failed
    filter_result = Column(UnicodeJSON, nullable=True)  # LLM过滤结果
    filtered = Column(Boolean, nullable=True)  # 是否被过滤
    readwise_id = Column(String(100), nullable=True)  # Readwise文档ID
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Record(id={self.id}, feed_url='{self.feed_url}', status='{self.status}')>"


class Queue(Base):
    """队列表 - 专门用于队列处理"""

    __tablename__ = "queue"

    id = Column(Integer, primary_key=True, index=True)
    feed_url = Column(String(1000), nullable=False, index=True)  # Feed URL
    title = Column(String(500), nullable=False)  # 文章标题
    content = Column(Text, nullable=False)  # 文章内容
    article_url = Column(String(1000), nullable=False)  # 文章URL
    created_at = Column(DateTime, default=func.now(), index=True)

    def __repr__(self):
        return f"<Queue(id={self.id}, feed_url='{self.feed_url}')>"
