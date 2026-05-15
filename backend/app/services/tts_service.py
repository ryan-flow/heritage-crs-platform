"""
TTS 语音合成服务 —— 豆包语音合成模型 2.0（主） + Edge-TTS（降级回退）

架构：
  1. 优先使用豆包语音合成模型 2.0 API（v3 HTTP SSE）
     - 支持 2.0 标准音色（_uranus_ 系列）和角色扮演音色（saturn_ 系列）
     - 支持情感控制（context_texts）
  2. 豆包 v3 失败时尝试 v1 接口（兼容 1.0 音色）
  3. 都不可用时自动降级到 Edge-TTS
  4. 缓存机制：MD5(引擎+音色+文本) → 文件名，命中则直接返回

v3 API 参考：https://www.volcengine.com/docs/6561/1598757
v1 API 参考：https://www.volcengine.com/docs/6561/1257584
"""

import asyncio
import base64
import hashlib
import json
import logging
import uuid
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Edge-TTS 延迟导入 ──
_edge_tts = None


def _get_edge_tts():
    global _edge_tts
    if _edge_tts is None:
        try:
            import edge_tts as _et
            _edge_tts = _et
        except ImportError:
            raise RuntimeError(
                "Edge-TTS 不可用：pip install edge-tts"
            )
    return _edge_tts


# ── 工具函数 ──

def _build_audio_filename(engine: str, voice: str, text: str) -> str:
    """根据引擎+音色+文本生成唯一文件名"""
    key = f"{engine}|{voice}|{text}".encode("utf-8")
    digest = hashlib.md5(key).hexdigest()
    return f"{digest}.mp3"


def _get_storage_dir() -> Path:
    """获取 TTS 存储目录，不存在则创建"""
    storage_dir = settings.backend_dir / settings.tts_storage_dir
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


def _is_v3_voice(speaker: str) -> bool:
    """判断音色是否需要 v3 接口（2.0 音色和角色扮演音色）"""
    return "_uranus_" in speaker or speaker.startswith("saturn_")


# ── 豆包 TTS v3 接口（支持 2.0 + 角色扮演音色） ──

DOUBAO_TTS_V3_URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"


async def _doubao_tts_v3(text: str, output_file: Path) -> bool:
    """
    调用豆包语音合成模型 2.0 v3 HTTP SSE 接口。
    支持 _uranus_ 系列和 saturn_ 系列角色扮演音色。
    """
    appid = settings.doubao_tts_appid
    access_key = settings.doubao_tts_access_token
    speaker = settings.doubao_tts_speaker

    if not appid or not access_key:
        logger.warning("豆包 TTS v3 未配置，跳过")
        return False

    # 截断过长文本（建议 <300 字符）
    if len(text.encode("utf-8")) > 1000:
        text = text[:300]

    # 根据 speaker 自动判断 resource_id
    if speaker.startswith("S_"):
        resource_id = "seed-icl-2.0"
    elif _is_v3_voice(speaker):
        resource_id = "seed-tts-2.0"
    else:
        resource_id = "seed-tts-1.0"

    headers = {
        "Content-Type": "application/json",
        "X-Api-App-Id": appid,
        "X-Api-Access-Key": access_key,
        "X-Api-Resource-Id": resource_id,
    }

    payload = {
        "user": {"uid": "heritage_platform"},
        "req_params": {
            "text": text,
            "speaker": speaker,
            "audio_params": {
                "format": settings.doubao_tts_encoding,
                "sample_rate": 24000,
            },
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(DOUBAO_TTS_V3_URL, json=payload, headers=headers)
            resp.raise_for_status()

        # 解析 NDJSON 响应，拼接 base64 音频片段
        audio_chunks = []
        for line in resp.text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            code = obj.get("code")
            data_str = obj.get("data")

            if code == 0 and data_str:
                audio_chunks.append(base64.b64decode(data_str))
            elif code == 20000000:
                pass  # 流结束信号
            elif code and code != 0 and code != 20000000:
                msg = obj.get("message", "")
                logger.warning("豆包 TTS v3 错误: code=%s message=%s", code, msg)
                return False

        if not audio_chunks:
            logger.warning("豆包 TTS v3 返回成功但无音频数据")
            return False

        audio_bytes = b"".join(audio_chunks)
        output_file.write_bytes(audio_bytes)

        logger.info(
            "豆包 TTS v3 生成成功: %s (%d bytes, speaker=%s, resource=%s)",
            output_file.name, len(audio_bytes), speaker, resource_id,
        )
        return True

    except httpx.HTTPStatusError as e:
        logger.warning("豆包 TTS v3 HTTP 错误: %s %s", e.response.status_code, e.response.text[:200])
        return False
    except httpx.TimeoutException:
        logger.warning("豆包 TTS v3 请求超时")
        return False
    except Exception as e:
        logger.error("豆包 TTS v3 异常: %s", e, exc_info=True)
        return False


# ── 豆包 TTS v1 接口（兼容 1.0 音色，降级回退） ──

DOUBAO_TTS_V1_URL = "https://openspeech.bytedance.com/api/v1/tts"


async def _doubao_tts_v1(text: str, output_file: Path) -> bool:
    """
    调用豆包语音合成 v1 HTTP 非流式接口。
    仅支持 1.0 音色（_mars_ / _moon_ 系列）。
    """
    appid = settings.doubao_tts_appid
    access_token = settings.doubao_tts_access_token

    if not appid or not access_token:
        return False

    # 截断过长文本
    if len(text.encode("utf-8")) > 1000:
        text = text[:300]

    payload = {
        "app": {
            "appid": appid,
            "token": "access_token",
            "cluster": "volcano_tts",
        },
        "user": {"uid": "heritage_platform"},
        "audio": {
            "voice_type": settings.doubao_tts_speaker,
            "encoding": settings.doubao_tts_encoding,
            "speed_ratio": settings.doubao_tts_speed,
            "loudness_ratio": settings.doubao_tts_volume,
            "explicit_language": "zh-cn",
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "operation": "query",
        },
    }

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer;{access_token}",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(DOUBAO_TTS_V1_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        code = data.get("code")
        if code != 3000:
            logger.warning("豆包 TTS v1 错误: code=%s message=%s", code, data.get("message"))
            return False

        audio_b64 = data.get("data")
        if not audio_b64:
            return False

        audio_bytes = base64.b64decode(audio_b64)
        output_file.write_bytes(audio_bytes)
        logger.info("豆包 TTS v1 降级成功: %s (%d bytes)", output_file.name, len(audio_bytes))
        return True

    except Exception as e:
        logger.warning("豆包 TTS v1 失败: %s", e)
        return False


# ── Edge-TTS 降级 ──

async def _edge_tts_generate(text: str, output_file: Path) -> bool:
    """调用 Edge-TTS 生成音频，作为最终降级回退。"""
    if len(text) > 500:
        text = text[:497] + "..."

    try:
        edge_module = _get_edge_tts()
        communicator = edge_module.Communicate(
            text=text,
            voice=settings.tts_voice,
            rate=settings.tts_rate,
            volume=settings.tts_volume,
        )
        await communicator.save(str(output_file))

        if output_file.exists() and output_file.stat().st_size > 0:
            logger.info("Edge-TTS 降级成功: %s", output_file.name)
            return True
        else:
            logger.error("Edge-TTS 生成后文件为空")
            return False

    except RuntimeError as e:
        logger.warning("Edge-TTS 不可用: %s", e)
        return False
    except Exception as e:
        logger.error("Edge-TTS 失败: %s", e, exc_info=True)
        if output_file.exists():
            try:
                output_file.unlink()
            except OSError:
                pass
        return False


# ── 公开接口 ──

async def text_to_speech(text: str) -> str | None:
    """
    异步生成 TTS 音频并返回可访问的静态路径。

    调用链：豆包 v3 → 豆包 v1（降级） → Edge-TTS（最终降级）

    Returns:
        静态文件 URL 路径，如 "/static/tts/xxx.mp3"
        失败时返回 None
    """
    clean_text = (text or "").strip()
    if not clean_text:
        raise ValueError("朗读文本不能为空")

    storage_dir = _get_storage_dir()
    speaker = settings.doubao_tts_speaker

    # ── 第一步：尝试豆包 TTS ──
    doubao_filename = _build_audio_filename("doubao", speaker, clean_text)
    doubao_file = storage_dir / doubao_filename

    # 缓存命中
    if doubao_file.exists() and doubao_file.stat().st_size > 0:
        logger.debug("豆包 TTS 缓存命中: %s", doubao_filename)
        return f"/static/tts/{doubao_filename}"

    # 2.0 / saturn 音色用 v3，1.0 音色用 v1
    if _is_v3_voice(speaker):
        doubao_ok = await _doubao_tts_v3(clean_text, doubao_file)
    else:
        doubao_ok = await _doubao_tts_v1(clean_text, doubao_file)

    if doubao_ok:
        return f"/static/tts/{doubao_filename}"

    # v3 失败时尝试 v1 降级
    if _is_v3_voice(speaker):
        logger.info("豆包 TTS v3 失败，尝试 v1 降级")
        doubao_ok = await _doubao_tts_v1(clean_text, doubao_file)
        if doubao_ok:
            return f"/static/tts/{doubao_filename}"

    # ── 第二步：降级 Edge-TTS ──
    logger.info("豆包 TTS 不可用，降级到 Edge-TTS")
    edge_filename = _build_audio_filename("edge", settings.tts_voice, clean_text)
    edge_file = storage_dir / edge_filename

    if edge_file.exists() and edge_file.stat().st_size > 0:
        logger.debug("Edge-TTS 缓存命中: %s", edge_filename)
        return f"/static/tts/{edge_filename}"

    edge_ok = await _edge_tts_generate(clean_text, edge_file)
    if edge_ok:
        return f"/static/tts/{edge_filename}"

    # ── 全部失败 ──
    logger.error("所有 TTS 引擎均失败，文本: %s...", clean_text[:30])
    return None
