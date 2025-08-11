import logging
from typing import Optional

import httpx

from app.core.config import config

logger = logging.getLogger(__name__)


class ReadwiseService:
    def __init__(self):
        self.api_token = config.get_api_config()["readwise_token"]
        self.base_url = "https://readwise.io/api/v3"

    async def save_article(self, url: str) -> Optional[str]:
        """保存文章到Readwise Reader，只传递URL让Readwise自动抓取内容"""
        try:
            headers = {
                "Authorization": f"Token {self.api_token}",
                "Content-Type": "application/json",
            }

            data = {
                "url": url,
                "location": "feed",  # 保存到feed位置
                "category": "article",
                "saved_using": "feedsieve",
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/save/", headers=headers, json=data
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    readwise_id = result.get("id")
                    logger.info(f"文章保存成功: {url}, ID: {readwise_id}")
                    return readwise_id
                else:
                    logger.error(
                        f"保存文章失败: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Readwise API调用失败: {e}")
            return None

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            headers = {"Authorization": f"Token {self.api_token}"}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://readwise.io/api/v2/auth/", headers=headers
                )

                return response.status_code == 204

        except Exception as e:
            logger.error(f"Readwise健康检查失败: {e}")
            return False
