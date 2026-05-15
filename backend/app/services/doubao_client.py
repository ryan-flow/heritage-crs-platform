"""
豆包大模型客户端 — Chat Completions API

- 使用火山方舟标准 Chat Completions 接口（兼容 OpenAI 格式）
- 默认关闭深度思考（thinking: disabled），响应速度 6s → 2.7s 首字
- 支持流式输出（SSE）
- 支持多轮对话（传入历史 messages）
"""

import httpx
import json
import time
import logging
from typing import Generator

from app.core.config import settings

logger = logging.getLogger(__name__)

# 标准 Chat Completions 端点
CHAT_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"


def _build_headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.doubao_api_key}",
        "Content-Type": "application/json",
    }


def _build_messages(
    question: str,
    system_prompt: str | None = None,
    history: list[dict] | None = None,
    context: str | None = None,
) -> list[dict]:
    """构建 messages 数组，支持多轮对话和上下文注入。"""
    messages = []

    # 系统提示词
    sys_content = system_prompt or settings.ai_system_prompt
    if context:
        sys_content += f"\n\n【参考信息】\n{context}"
    messages.append({"role": "system", "content": sys_content})

    # 历史对话（最近4轮，避免token过长）
    if history:
        for turn in history[-8:]:
            role = turn.get("role", "")
            content = turn.get("content", "") or turn.get("text", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

    # 当前问题
    messages.append({"role": "user", "content": question})

    return messages


def ask_doubao(
    question: str,
    system_prompt: str | None = None,
    history: list[dict] | None = None,
    context: str | None = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """
    调用豆包 Chat Completions API（非流式）。

    Args:
        question: 用户问题
        system_prompt: 自定义系统提示词（覆盖默认）
        history: 历史对话 [{"role": "user/assistant", "content": "..."}]
        context: 注入的参考信息（如知识库答案）
        max_tokens: 最大输出token数
        temperature: 温度参数

    Returns:
        模型回复文本
    """
    messages = _build_messages(question, system_prompt, history, context)

    payload = {
        "model": settings.doubao_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "thinking": {"type": "disabled"},  # 关闭深度思考，提速3倍
    }

    headers = _build_headers()
    last_error = None

    for attempt in range(2):
        try:
            with httpx.Client(timeout=25.0) as client:
                resp = client.post(CHAT_URL, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            # Chat Completions 标准响应格式
            choices = data.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                if content and content.strip():
                    return content.strip()

            logger.warning("豆包返回空内容: %s", json.dumps(data, ensure_ascii=False)[:200])
            return ""

        except httpx.TimeoutException as e:
            last_error = e
            logger.warning("豆包请求超时 (attempt %d): %s", attempt + 1, e)
            time.sleep(0.3)
        except httpx.HTTPStatusError as e:
            last_error = e
            logger.error(
                "豆包HTTP错误 %d: %s",
                e.response.status_code,
                e.response.text[:300],
            )
            if e.response.status_code == 429:
                time.sleep(1.0)  # 限流等待
            else:
                break  # 其他HTTP错误不重试
        except Exception as e:
            last_error = e
            logger.error("豆包请求异常: %s", e)
            break

    if last_error:
        raise last_error
    raise RuntimeError("豆包接口请求失败")


def ask_doubao_stream(
    question: str,
    system_prompt: str | None = None,
    history: list[dict] | None = None,
    context: str | None = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> Generator[str, None, None]:
    """
    调用豆包 Chat Completions API（流式输出）。

    逐token返回，适合SSE推送和打字机效果。
    首token延迟约2.7秒。

    Yields:
        每次yield一个文本片段
    """
    messages = _build_messages(question, system_prompt, history, context)

    payload = {
        "model": settings.doubao_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "thinking": {"type": "disabled"},
        "stream": True,
    }

    headers = _build_headers()

    try:
        with httpx.Client(timeout=30.0) as client:
            with client.stream("POST", CHAT_URL, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    payload_str = line[6:].strip()
                    if payload_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload_str)
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

    except httpx.TimeoutException:
        logger.error("豆包流式请求超时")
        yield "[请求超时，请稍后重试]"
    except httpx.HTTPStatusError as e:
        logger.error("豆包流式HTTP错误 %d: %s", e.response.status_code, e.response.text[:200])
        yield "[AI服务暂时不可用，请稍后重试]"
    except Exception as e:
        logger.error("豆包流式请求异常: %s", e)
        yield "[AI服务异常，请稍后重试]"
