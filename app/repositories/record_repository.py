import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import and_, desc

from app.models import Record
from app.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class RecordRepository(BaseRepository):
    """记录数据访问层"""

    def create_record(
        self,
        feed_url: str,
        title: str,
        summary: str = None,
        article_url: str = None,
        status: str = None,
        filter_result: Optional[Dict[str, Any]] = None,
        filtered: Optional[bool] = None,
        readwise_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> int:
        """创建记录"""
        session = self.get_session()
        try:
            record = Record(
                feed_url=feed_url,
                title=title,
                summary=summary,
                article_url=article_url,
                status=status,
                filter_result=filter_result,
                filtered=filtered,
                readwise_id=readwise_id,
                error_message=error_message
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.id
        except Exception as e:
            session.rollback()
            logger.error(f"创建记录失败: {e}")
            raise
        finally:
            self.close_session(session)

    def get_record_by_id(self, record_id: int) -> Optional[Record]:
        """根据ID获取记录"""
        session = self.get_session()
        try:
            return session.query(Record).filter(Record.id == record_id).first()
        finally:
            self.close_session(session)

    def update_record(self, record_id: int, **kwargs) -> bool:
        """更新记录"""
        session = self.get_session()
        try:
            record = session.query(Record).filter(
                Record.id == record_id).first()
            if record:
                for key, value in kwargs.items():
                    setattr(record, key, value)
                record.updated_at = datetime.now()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"更新记录失败: {e}")
            return False
        finally:
            self.close_session(session)

    def delete_record(self, record_id: int) -> bool:
        """删除记录"""
        session = self.get_session()
        try:
            record = session.query(Record).filter(
                Record.id == record_id).first()
            if record:
                session.delete(record)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"删除记录失败: {e}")
            return False
        finally:
            self.close_session(session)

    def get_records(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取记录列表"""
        session = self.get_session()
        try:
            query = session.query(Record)

            # 状态过滤
            if status:
                query = query.filter(Record.status == status)

            # 搜索过滤
            if search:
                search_filter = Record.title.contains(search)
                query = query.filter(search_filter)

            # 总数
            total = query.count()

            # 分页
            offset = (page - 1) * page_size
            records = (
                query.order_by(desc(Record.created_at))
                .offset(offset)
                .limit(page_size)
                .all()
            )

            return {
                "records": records,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            }
        finally:
            self.close_session(session)

    def get_record_stats(self, days: int = 1) -> Dict[str, Any]:
        """获取记录统计"""
        session = self.get_session()
        try:
            start_date = datetime.now() - timedelta(days=days)

            # 总接收量
            total_count = (
                session.query(Record).filter(
                    Record.created_at >= start_date).count()
            )

            # SKIP数量
            skip_count = (
                session.query(Record)
                .filter(and_(Record.status == "skip", Record.created_at >= start_date))
                .count()
            )

            # 有用的数量（符合要求）
            useful_count = (
                session.query(Record)
                .filter(and_(Record.status == "useful", Record.created_at >= start_date))
                .count()
            )

            # 无用的数量（不符合要求）
            useless_count = (
                session.query(Record)
                .filter(and_(Record.status == "useless", Record.created_at >= start_date))
                .count()
            )

            # 失败数量
            failed_count = (
                session.query(Record)
                .filter(and_(Record.status == "failed", Record.created_at >= start_date))
                .count()
            )

            # 计算成功率（useful + useless + skip）
            success_total = useful_count + useless_count + skip_count
            success_rate = (success_total / total_count *
                            100) if total_count > 0 else 0

            return {
                "total": total_count,
                "useful": useful_count,
                "useless": useless_count,
                "failed": failed_count,
                "skip": skip_count,
                "success_rate": round(success_rate, 2),
            }
        finally:
            self.close_session(session)

    def cleanup_old_records(self, days: int = 30) -> int:
        """清理旧记录"""
        session = self.get_session()
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = (
                session.query(Record).filter(
                    Record.created_at < cutoff_date).delete()
            )
            session.commit()
            return deleted_count
        except Exception as e:
            session.rollback()
            logger.error(f"清理旧记录失败: {e}")
            return 0
        finally:
            self.close_session(session)
