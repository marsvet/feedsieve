"""
网页内容抓取服务

使用 trafilatura 库来抓取和解析网页内容
"""

import logging
from typing import Optional
from urllib.parse import urlparse

import requests
import trafilatura

from app.core.config import config

logger = logging.getLogger(__name__)


class ContentFetcherService:
    """网页内容抓取服务"""

    def __init__(self):
        self.session = requests.Session()
        self._setup_session()
        self._setup_trafilatura()

    def _setup_session(self):
        """设置请求会话"""
        # 设置用户代理
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # 设置超时
        self.session.timeout = 30

        # 设置SSL验证选项
        self.session.verify = False
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # 如果有代理配置，设置代理
        proxy_config = config.get_proxy_config()
        if proxy_config:
            if proxy_config["type"] == "http":
                self.session.proxies = {
                    "http": proxy_config["url"],
                    "https": proxy_config["url"]
                }
            elif proxy_config["type"] == "socks5":
                # 对于 socks5 代理，需要安装 requests[socks] 或 PySocks
                try:
                    import socket

                    import socks
                    proxy_url = urlparse(proxy_config["url"])
                    socks.set_default_proxy(
                        socks.SOCKS5,
                        proxy_url.hostname,
                        proxy_url.port,
                        username=proxy_url.username,
                        password=proxy_url.password
                    )
                    socket.socket = socks.socksocket
                except ImportError:
                    logger.warning("未安装 PySocks，无法使用 SOCKS5 代理")

    def _setup_trafilatura(self):
        """设置 trafilatura 配置"""
        # 使用默认配置，专注于文本提取
        self.trafilatura_config = None

    async def fetch_content(self, url: str) -> Optional[str]:
        """
        抓取网页内容

        Args:
            url: 网页URL

        Returns:
            解析后的纯文本内容，如果失败则返回 None
        """
        try:
            logger.info(f"开始抓取网页内容: {url}")

            # 发送请求获取网页内容
            response = self.session.get(url)
            response.raise_for_status()

            # 检查内容类型
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(f"非HTML内容类型: {content_type}")
                return None

            # 使用 trafilatura 解析内容
            extracted_text = trafilatura.extract(
                response.content,
                config=self.trafilatura_config
            )

            if not extracted_text:
                logger.warning(f"无法提取到有效内容: {url}")
                return None

            logger.info(f"成功抓取网页内容，长度: {len(extracted_text)} 字符")
            return extracted_text

        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {url}, 错误: {e}")
            return None
        except Exception as e:
            logger.error(f"抓取内容失败: {url}, 错误: {e}")
            return None

    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'session'):
            self.session.close()


# 全局内容抓取服务实例
content_fetcher_service = ContentFetcherService()
