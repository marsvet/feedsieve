import logging

from app.core.config import config
from app.core.constants import RecordStatus
from app.core.logging import get_queue_logger
from app.repositories.queue_repository import QueueRepository
from app.services.llm_service import LLMService
from app.services.readwise_service import ReadwiseService
from app.services.record_service import record_service

logger = logging.getLogger(__name__)
queue_logger = get_queue_logger()


class QueueService:
    """队列业务逻辑层"""

    def __init__(self):
        self.queue_repository = QueueRepository()
        self.record_service = record_service
        self.llm_service = LLMService()
        self.readwise_service = ReadwiseService()
        self.retry_times = config.get_queue_config()["retry_times"]

    async def add_to_queue(self, feed_url: str, title: str, content: str, article_url: str) -> int:
        """添加数据到队列"""
        try:
            queue_id = self.queue_repository.add_to_queue(
                feed_url=feed_url,
                title=title,
                content=content,
                article_url=article_url
            )
            queue_logger.info(
                f"数据已添加到队列: queue_id={queue_id}, feed_url={feed_url}")
            return queue_id
        except Exception as e:
            queue_logger.error(f"添加数据到队列失败: {e}")
            raise

    async def process_queue(self) -> int:
        """处理队列中的数据 - 一个一个处理"""
        try:
            # 只获取一个待处理的项目
            queue_item = self.queue_repository.get_next_pending_item()

            if not queue_item:
                return 0

            queue_logger.info(
                f"开始处理队列项: id={queue_item.id}, feed_url={queue_item.feed_url}")

            # 处理单个项目
            success = await self._process_single_item(queue_item)

            if success:
                # 处理成功后删除队列项
                self.queue_repository.delete_queue_item(queue_item.id)
                queue_logger.info(f"队列项处理完成并已删除: id={queue_item.id}")
            else:
                # 处理失败，检查重试次数
                if queue_item.retry_count < queue_item.max_retries:
                    # 增加重试次数
                    self.queue_repository.update_queue_status(
                        queue_item.id,
                        status="pending",
                        retry_count=queue_item.retry_count + 1
                    )
                    queue_logger.info(
                        f"将重试队列项: id={queue_item.id}, 重试次数={queue_item.retry_count + 1}")
                else:
                    # 达到最大重试次数，删除队列项
                    self.queue_repository.delete_queue_item(queue_item.id)
                    queue_logger.error(f"达到最大重试次数，已删除: id={queue_item.id}")

            return 1

        except Exception as e:
            queue_logger.error(f"处理队列失败: {e}")
            return 0

    async def _process_single_item(self, queue_item):
        """处理单个队列项目"""
        feed_url = queue_item.feed_url
        title = queue_item.title
        content = queue_item.content
        article_url = queue_item.article_url

        queue_logger.info(f"处理队列项: feed_url={feed_url}, title={title}")

        try:
            # 1. 检查是否有对应的prompt
            prompts = config.get_prompts()
            prompt = None
            for url_pattern, prompt_text in prompts.items():
                if any(pattern in feed_url for pattern in url_pattern):
                    prompt = prompt_text
                    break

            if not prompt:
                # 没有对应prompt，记录为SKIP
                await self.record_service.create_record(
                    feed_url=feed_url,
                    title=title,
                    summary="无prompt配置，未进行内容摘要",
                    article_url=article_url,
                    status=RecordStatus.SKIP,
                    error_message="没有对应的prompt配置"
                )
                queue_logger.info(f"没有对应prompt，已记录为SKIP: feed_url={feed_url}")

                return True

            # 2. 使用LLM进行判断
            try:
                filter_result = await self.llm_service.filter_content(
                    title=title,
                    content=content,
                    source=feed_url,
                )

                # 3. 根据判断结果处理
                if filter_result.get("useful", False):
                    # 符合要求，发送到Readwise Reader
                    try:
                        readwise_id = await self.readwise_service.save_article(
                            url=article_url,
                            title=title,
                            summary=filter_result.get("summary", ""),
                            author="",
                            html=content,
                        )

                        # 记录有用的（符合要求，发送到Readwise）
                        await self.record_service.create_record(
                            feed_url=feed_url,
                            title=title,
                            summary=filter_result.get("summary", ""),
                            article_url=article_url,
                            status=RecordStatus.USEFUL,
                            filter_result=filter_result,
                            filtered=False,
                            readwise_id=readwise_id
                        )

                        queue_logger.info(
                            f"内容已发送到Readwise: readwise_id={readwise_id}")

                        # 处理成功
                        return True

                    except Exception as e:
                        # Readwise发送失败
                        error_msg = f"发送到Readwise失败: {str(e)}"
                        await self.record_service.create_record(
                            feed_url=feed_url,
                            title=title,
                            summary=filter_result.get("summary", ""),
                            article_url=article_url,
                            status=RecordStatus.FAILED,
                            filter_result=filter_result,
                            filtered=False,
                            error_message=error_msg
                        )
                        queue_logger.error(error_msg)
                        return False

                else:
                    # 不符合要求，无用的
                    await self.record_service.create_record(
                        feed_url=feed_url,
                        title=title,
                        summary=filter_result.get("summary", ""),
                        article_url=article_url,
                        status=RecordStatus.USELESS,
                        filter_result=filter_result,
                        filtered=True
                    )
                    queue_logger.info(
                        f"内容被过滤，已记录: reason={filter_result.get('reason', '')}")

                    # 处理成功
                    return True

            except Exception as e:
                # LLM处理失败
                error_msg = f"LLM处理失败: {str(e)}"
                await self.record_service.create_record(
                    feed_url=feed_url,
                    title=title,
                    summary="LLM处理失败，无法生成摘要",
                    article_url=article_url,
                    status=RecordStatus.FAILED,
                    error_message=error_msg
                )
                queue_logger.error(error_msg)
                return False

        except Exception as e:
            # 其他处理失败
            error_msg = f"处理队列项失败: {str(e)}"
            await self.record_service.create_record(
                feed_url=feed_url,
                title=title,
                summary="处理失败，无法生成摘要",
                article_url=article_url,
                status=RecordStatus.FAILED,
                error_message=error_msg
            )
            queue_logger.error(error_msg)
            return False

    async def get_queue_stats(self) -> dict:
        """获取队列统计"""
        return self.queue_repository.get_queue_stats()

    async def cleanup_queue(self) -> int:
        """清理队列"""
        try:
            return self.queue_repository.cleanup_old_queue_items(days=7)
        except Exception as e:
            logger.error(f"清理队列失败: {e}")
            return 0


# 全局队列服务实例
queue_service = QueueService()
