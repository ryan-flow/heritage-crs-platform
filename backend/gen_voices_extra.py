"""补充3个音色试听"""
import asyncio, sys, json, base64, time, uuid
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.core.config import settings
import httpx

V1_URL = 'https://openspeech.bytedance.com/api/v1/tts'

voices = [
    ('zh_female_wanwanxiaohe_moon_bigtts', '18_wanwan_xiaohe', '湾湾小何'),
    ('zh_female_xinlingjitang_moon_bigtts', '19_xinling_jitang', '心灵鸡汤'),
    ('BV005_streaming', '20_huopo_nsheng', '活泼女声'),
]

test_text = '你好呀，欢迎来到非遗世界，我是你的导览官黑塔！今天想聊些什么呢？'
storage = Path(__file__).resolve().parent / 'storage' / 'tts'
v1_hdrs = {
    'Content-Type': 'application/json; charset=utf-8',
    'Authorization': f'Bearer;{settings.doubao_tts_access_token}',
}

async def gen_v1(voice):
    payload = {
        'app': {'appid': settings.doubao_tts_appid, 'token': 'access_token', 'cluster': 'volcano_tts'},
        'user': {'uid': 'herta_test'},
        'audio': {'voice_type': voice, 'encoding': 'mp3', 'speed_ratio': 1.0, 'loudness_ratio': 1.0},
        'request': {'reqid': str(uuid.uuid4()), 'text': test_text, 'operation': 'query'},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(V1_URL, json=payload, headers=v1_hdrs)
        data = resp.json()
        if data.get('code') == 3000 and data.get('data'):
            return base64.b64decode(data['data'])
    return None

async def main():
    for voice, fname, cn_name in voices:
        t = time.time()
        try:
            audio = await gen_v1(voice)
            cost = time.time() - t
            if audio and len(audio) > 0:
                fpath = storage / f'{fname}.mp3'
                fpath.write_bytes(audio)
                kb = len(audio) // 1024
                print(f'[OK] {fname:30s} | {cn_name:10s} | {kb:3d}KB | {cost:.1f}s')
            else:
                print(f'[FAIL] {fname:30s} | {cn_name:10s}')
        except Exception as e:
            print(f'[ERR] {fname:30s} | {cn_name:10s} | {str(e)[:50]}')

if __name__ == '__main__':
    asyncio.run(main())
