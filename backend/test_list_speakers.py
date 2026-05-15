"""调用豆包 ListSpeakers API 获取音色列表"""
import sys
import asyncio
import json
import httpx

sys.stdout.reconfigure(encoding="utf-8")


async def list_speakers():
    appid = "REPLACED_TTS_APPID"
    access_key = "REPLACED_TTS_TOKEN"

    # 尝试 ListSpeakers API
    url = "https://openspeech.bytedance.com/api/v3/tts/speakers"
    headers = {
        "Content-Type": "application/json",
        "X-Api-App-Id": appid,
        "X-Api-Access-Key": access_key,
    }
    payload = {
        "user": {"uid": "test"},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text[:3000]}")


asyncio.run(list_speakers())
