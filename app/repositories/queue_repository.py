import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import asc

from app.models import Queue
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class QueueRepository(BaseRepository):
    """队列数据访问层"""

    def exists_by_url(self, article_url: str) -> bool:
        """检查URL是否已存在于队列中"""
        session = self.get_session()
        try:
            return session.query(Queue).filter(
                Queue.article_url == article_url
            ).first() is not None
        finally:
            self.close_session(session)

    def add_to_queue(
        self, feed_url: str, title: str, content: str, article_url: str
    ) -> int:
        """添加数据到队列"""
        session = self.get_session()
        try:
            queue_item = Queue(
                feed_url=feed_url,
                title=title,
                content=content,
                article_url=article_url,
            )
            session.add(queue_item)
            session.commit()
            session.refresh(queue_item)
            return queue_item.id
        except Exception as e:
            session.rollback()
            logger.error(f"添加数据到队列失败: {e}")
            raise
        finally:
            self.close_session(session)

    def get_next_pending_item(self) -> Optional[Queue]:
        """获取下一个待处理的项目"""
        session = self.get_session()
        try:
            return (
                session.query(Queue)
                .order_by(asc(Queue.created_at))
                .first()
            )
        finally:
            self.close_session(session)

    def delete_queue_item(self, queue_id: int) -> bool:
        """删除队列项"""
        session = self.get_session()
        try:
            queue_item = session.query(Queue).filter(
                Queue.id == queue_id).first()
            if queue_item:
                session.delete(queue_item)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"删除队列项失败: {e}")
            return False
        finally:
            self.close_session(session)

    def get_queue_stats(self) -> dict:
        """获取队列统计"""
        session = self.get_session()
        try:
            total_count = session.query(Queue).count()
            return {
                "total": total_count,
            }
        finally:
            self.close_session(session)

    def cleanup_old_queue_items(self, days: int = 7) -> int:
        """清理旧的队列项"""
        session = self.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = (
                session.query(Queue)
                .filter(Queue.created_at < cutoff_date)
                .delete()
            )
            session.commit()
            return deleted_count
        except Exception as e:
            session.rollback()
            logger.error(f"清理旧队列项失败: {e}")
            return 0
        finally:
            self.close_session(session)
