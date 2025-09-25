import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import ValidationError

from ..core.logging import get_logger
from ..models.schemas import APIResponse, WebhookPayload
from ..services.queue_service import queue_service

logger = logging.getLogger(__name__)
webhook_logger = get_logger("feedsieve.webhook")

# 创建路由器
router = APIRouter()


class WebhookController:
    """Webhook控制器"""

    def __init__(self):
        self.queue_service = queue_service

    async def receive_webhook(self, payload: Any) -> APIResponse:
        """接收内容webhook"""
        try:
            # 严格校验请求参数格式
            try:
                validated_payload = WebhookPayload(**payload)
            except (ValidationError, TypeError, ValueError) as e:
                # 参数格式不符合要求，返回 404 (无响应内容)
                webhook_logger.warning(f"Webhook 参数格式错误: {e}")
                raise HTTPException(status_code=404)

            # 提取数据
            feed_url = validated_payload.feed.url
            title = validated_payload.entry.title
            content = validated_payload.entry.content or ""
            article_url = validated_payload.entry.url

            webhook_logger.info(
                f"接收到 Webhook: feed_url={feed_url}, title={title}, article_url={article_url}"
            )

            # 验证必要字段
            if not feed_url or not title or not article_url:
                webhook_logger.warning(
                    f"缺少必要字段: feed_url={feed_url}, title={title}, article_url={article_url}")
                raise HTTPException(status_code=404)

            # 直接存入Queue表
            queue_id = await self.queue_service.add_to_queue(
                feed_url=feed_url,
                title=title,
                content=content,
                article_url=article_url
            )

            webhook_logger.info(
                f"Webhook处理成功: queue_id={queue_id}, feed_url={feed_url}, title={title}"
            )

            return APIResponse(
                success=True,
                message="Webhook 处理成功",
                data={"queue_id": queue_id, "feed_url": feed_url},
            )

        except HTTPException:
            # 重新抛出 HTTP 异常 (如 404)
            raise HTTPException(status_code=404)
        except Exception as e:
            webhook_logger.error(f"Webhook处理失败: {e}")
            # 服务器内部错误也返回 404 (无响应内容)
            raise HTTPException(status_code=404)


# 创建控制器实例
webhook_controller = WebhookController()


# 注册路由
@router.post(
    "/api/webhook/053e46c8c41a4de199c4",
    response_model=APIResponse,
    summary="接收内容 Webhook",
    tags=["Webhook"],
    responses={404: {"description": "请求格式错误或端点不存在", "content": {}}},
)
async def receive_webhook(request: Request):
    """
    接收来自 RSS 服务的 Webhook

    路径包含安全密钥: 053e46c8c41a4de199c4

    - 严格校验请求参数格式
    - 解析 Webhook 载荷
    - 创建处理任务
    - 加入队列处理

    注意：
    - 此接口不需要额外认证
    - 参数格式不符合要求时返回 404，无响应内容
    - 必须包含完整的 WebhookPayload 结构
    """
    try:
        # 获取请求体
        payload = await request.json()
    except Exception:
        # JSON 解析失败，返回 404
        raise HTTPException(status_code=404)

    return await webhook_controller.receive_webhook(payload)


# 捕获所有其他 HTTP 方法，返回 404（无内容）
@router.api_route(
    "/api/webhook/053e46c8c41a4de199c4",
    methods=["GET", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def webhook_method_not_allowed():
    """非 POST 请求返回 404，无响应内容"""
    raise HTTPException(status_code=404)
