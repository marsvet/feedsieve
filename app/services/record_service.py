import logging
from typing import Any, Dict, Optional

from app.repositories.record_repository import RecordRepository

logger = logging.getLogger(__name__)


class RecordService:
    """记录业务逻辑层"""

    def __init__(self):
        self.record_repository = RecordRepository()

    async def create_record(
        self,
        feed_url: str,
        title: str,
        summary: str,
        article_url: str,
        status: str,
        filter_result: Optional[Dict[str, Any]] = None,
        filtered: Optional[bool] = None,
        readwise_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> int:
        """创建记录"""
        try:
            record_id = self.record_repository.create_record(
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
            logger.info(f"记录已创建: record_id={record_id}, feed_url={feed_url}")
            return record_id
        except Exception as e:
            logger.error(f"创建记录失败: {e}")
            raise

    async def get_record_stats(self, days: int = 1) -> Dict[str, Any]:
        """获取记录统计"""
        return self.record_repository.get_record_stats(days)

    async def get_records(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取记录列表"""
        return self.record_repository.get_records(
            status=status, page=page, page_size=page_size, search=search
        )

    async def delete_record(self, record_id: int) -> bool:
        """删除记录"""
        try:
            return self.record_repository.delete_record(record_id)
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            return False

    async def cleanup_old_data(self, record_days: int = 30) -> Dict[str, int]:
        """清理旧数据"""
        try:
            record_count = self.record_repository.cleanup_old_records(
                record_days)
            return {"records_deleted": record_count}
        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            return {"records_deleted": 0}


# 全局记录服务实例
record_service = RecordService()
