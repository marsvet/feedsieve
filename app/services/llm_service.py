import json
import logging
from typing import Any, Dict

import httpx

from app.core.config import config

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        # 获取LLM配置
        llm_config = config.get_llm_config()

        # 过滤启用的endpoints
        self.endpoints = [
            endpoint for endpoint in llm_config["endpoints"]
            if endpoint.get("enabled", True)
        ]

        if not self.endpoints:
            raise ValueError("没有启用的LLM endpoints")

        # 轮询索引
        self.current_index = 0

        logger.info(f"LLM服务初始化完成，支持 {len(self.endpoints)} 个endpoints")

    def _get_next_endpoint(self) -> Dict[str, Any]:
        """获取下一个endpoint（轮询）"""
        if not self.endpoints:
            raise ValueError("没有可用的endpoints")

        endpoint = self.endpoints[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.endpoints)
        return endpoint

    async def filter_content(
        self, title: str, content: str, source: str = "default"
    ) -> Dict[str, Any]:
        """使用LLM过滤内容"""
        try:
            # 选择endpoint
            endpoint = self._get_next_endpoint()

            # 构建prompt
            prompt = self._build_prompt(title, content, source)

            # 调用LLM API
            response = await self._call_llm_api(prompt, endpoint)

            # 解析响应
            result = self._parse_response(response)

            logger.info(
                f"LLM过滤完成 - endpoint: {endpoint['name']}, 标题: {title}, 结果: {result.get('useful', False)}"
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
        for url_patterns, prompt_config in prompts.items():
            if any(pattern in source for pattern in url_patterns):
                base_prompt = prompt_config["prompt"]
                break

        if not base_prompt:
            logger.warning(f"未找到来源 {source} 的prompt配置，使用默认prompt")
            # 使用第一个可用的prompt作为默认
            if prompts:
                base_prompt = list(prompts.values())[0]["prompt"]
            else:
                base_prompt = "请分析以下内容是否有价值。"

        # 构建完整prompt
        full_prompt = f"""{base_prompt}

请分析以下内容：
标题：{title}
内容：{content}

请严格按照以下JSON格式返回结果：
{{
  "title": "文章标题",
  "summary": "文章核心内容摘要（1-2句话）",
  "useful": true,  // true=保留，false=过滤掉
  "reason": "保留/过滤的具体原因"
}}

注意：
- 必须返回有效的JSON格式
- useful字段必须是布尔值（true或false）
- summary字段应该是1-2句话的简洁摘要
- reason字段应该说明判断的具体原因
- 不要包含任何其他文本，只返回JSON"""

        return full_prompt

    async def _call_llm_api(self, prompt: str, endpoint: Dict[str, Any]) -> str:
        """调用LLM API"""
        headers = self._get_headers(endpoint)
        data = self._get_request_data(prompt, endpoint)

        for attempt in range(endpoint["max_retries"] + 1):
            try:
                async with httpx.AsyncClient(timeout=endpoint["timeout"]) as client:
                    response = await client.post(
                        f"{endpoint['base_url']}/chat/completions",
                        headers=headers,
                        json=data
                    )

                    if response.status_code != 200:
                        error_msg = f"LLM API调用失败: {response.status_code} - {response.text}"
                        if attempt < endpoint["max_retries"]:
                            logger.warning(
                                f"第{attempt + 1}次尝试失败，将重试: {error_msg}")
                            continue
                        else:
                            raise Exception(error_msg)

                    result = response.json()
                    logger.debug(f"LLM API响应: {result}")

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

            except httpx.TimeoutException:
                if attempt < endpoint["max_retries"]:
                    logger.warning(f"第{attempt + 1}次尝试超时，将重试")
                    continue
                else:
                    raise Exception(
                        f"LLM API调用超时，已重试{endpoint['max_retries']}次")
            except Exception as e:
                if attempt < endpoint["max_retries"]:
                    logger.warning(f"第{attempt + 1}次尝试失败，将重试: {e}")
                    continue
                else:
                    raise e

    def _get_headers(self, endpoint: Dict[str, Any]) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Authorization": f"Bearer {endpoint['api_key']}",
            "Content-Type": "application/json",
        }

        # 根据提供商添加特定的请求头
        provider = endpoint["provider"]
        if provider == "openrouter":
            headers.update({
                "HTTP-Referer": "https://feedsieve.local",
                "X-Title": "feedsieve",
            })
        elif provider == "openai":
            # OpenAI 不需要额外头部
            pass
        elif provider == "anthropic":
            # Anthropic 使用不同的API格式，这里暂时不支持
            pass
        elif provider == "custom":
            # 自定义提供商，可以根据需要添加头部
            pass

        return headers

    def _get_request_data(self, prompt: str, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """获取请求数据"""
        return {
            "model": endpoint["model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": endpoint["temperature"],
            "max_tokens": endpoint["max_tokens"],
        }

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

    def get_status(self) -> Dict[str, Any]:
        """获取LLM服务状态"""
        return {
            "total_endpoints": len(self.endpoints),
            "enabled_endpoints": len([ep for ep in self.endpoints if ep.get("enabled", True)]),
            "current_index": self.current_index,
            "endpoints": [
                {
                    "name": ep["name"],
                    "provider": ep["provider"],
                    "model": ep["model"],
                    "enabled": ep.get("enabled", True)
                }
                for ep in self.endpoints
            ]
        }
