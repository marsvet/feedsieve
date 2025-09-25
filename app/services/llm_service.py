import json
import logging
from typing import Any, Dict

import httpx

from app.core.config import config

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.api_key = config.get_api_config()["openrouter_key"]
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "moonshotai/kimi-k2:free"

    async def filter_content(
        self, title: str, content: str, source: str = "default"
    ) -> Dict[str, Any]:
        """使用LLM过滤内容"""
        try:
            # 构建prompt
            prompt = self._build_prompt(title, content, source)

            # 调用OpenRouter API
            response = await self._call_openrouter(prompt)

            # 解析响应
            result = self._parse_response(response)

            logger.info(
                f"LLM过滤完成 - 标题: {title}, 结果: {result.get('useful', False)}"
            )
            return result

        except Exception as e:
            logger.error(f"LLM过滤失败: {e}")
            return {
                "useful": False,
                "reason": f"LLM调用失败: {str(e)}",
                "summary": "处理失败",
                "title": title,
            }

    def _build_prompt(self, title: str, content: str, source: str) -> str:
        """构建prompt"""
        # 获取对应的prompt内容
        prompts = config.get_prompts()
        base_prompt = None

        # 在prompt配置中查找匹配的feed URL
        for url_patterns, prompt_text in prompts.items():
            if any(pattern in source for pattern in url_patterns):
                base_prompt = prompt_text
                break

        if not base_prompt:
            logger.warning(f"未找到来源 {source} 的prompt配置，使用默认prompt")
            # 使用第一个可用的prompt作为默认
            if prompts:
                base_prompt = list(prompts.values())[0]
            else:
                base_prompt = "请分析以下内容是否有价值。"

        # 构建完整prompt
        full_prompt = f"{base_prompt}\n\n请分析以下内容：\n标题：{title}\n内容：{content}\n\n请返回JSON格式的结果。"

        return full_prompt

    async def _call_openrouter(self, prompt: str) -> str:
        """调用OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://feedsieve.local",
            "X-Title": "feedsieve",
        }

        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1000,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=data
            )

            if response.status_code != 200:
                raise Exception(
                    f"OpenRouter API调用失败: {response.status_code} - {response.text}"
                )

            result = response.json()

            # 调试：打印完整响应
            logger.debug(f"OpenRouter API响应: {result}")

            # 检查响应格式
            if "choices" not in result:
                logger.error(f"API响应中缺少choices字段: {result}")
                raise Exception(f"API响应格式错误，缺少choices字段: {result}")

            if not result["choices"]:
                logger.error(f"API响应中choices为空: {result}")
                raise Exception(f"API响应中choices为空: {result}")

            if "message" not in result["choices"][0]:
                logger.error(f"API响应中缺少message字段: {result}")
                raise Exception(f"API响应中缺少message字段: {result}")

            return result["choices"][0]["message"]["content"]

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试提取JSON
            start = response.find("{")
            end = response.rfind("}") + 1

            if start == -1 or end == 0:
                raise ValueError("未找到JSON格式的响应")

            json_str = response[start:end]
            result = json.loads(json_str)

            # 验证必要字段
            required_fields = ["useful", "reason", "summary", "title"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"响应缺少必要字段: {field}")

            return result

        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}, 原始响应: {response}")
            return {
                "useful": False,
                "reason": f"响应解析失败: {str(e)}",
                "summary": "解析失败",
                "title": "未知",
            }
