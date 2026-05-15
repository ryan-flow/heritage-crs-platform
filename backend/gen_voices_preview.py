"""批量生成20个音色试听文件"""
import asyncio
import sys
import json
import base64
import time
import uuid
from pathlib import Path

# 确保utf-8输出
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.core.config import settings
import httpx

V3_URL = 'https://openspeech.bytedance.com/api/v3/tts/unidirectional'
V1_URL = 'https://openspeech.bytedance.com/api/v1/tts'

# 20个候选音色
voices = [
    ('saturn_zh_female_keainvsheng_tob', 'v3', '01_keai_nvsheng', '可爱女生'),
    ('saturn_zh_female_tiaopigongzhu_tob', 'v3', '02_tiaopi_gongzhu', '调皮公主'),
    ('saturn_zh_female_cancan_tob', 'v3', '03_zhixing_cancan', '知性灿灿'),
    ('zh_female_vv_uranus_bigtts', 'v3', '04_vivi', 'Vivi 2.0'),
    ('zh_female_xiaohe_uranus_bigtts', 'v3', '05_xiaohe', '小何'),
    ('zh_female_cancan_uranus_bigtts', 'v3', '06_cancan_2', '灿灿 2.0'),
    ('zh_female_tianmeixiaoyuan_moon_bigtts', 'v1', '07_tianmei_xiaoyuan', '甜美小源'),
    ('zh_female_yuanqinvyou_moon_bigtts', 'v1', '08_sajiao_xuemei', '撒娇学妹'),
    ('zh_female_sajiaonvyou_moon_bigtts', 'v1', '09_roumei_nvyou', '柔美女友'),
    ('zh_female_daimengchuanmei_moon_bigtts', 'v1', '10_daimeng_chuanmei', '呆萌川妹'),
    ('zh_female_linjianvhai_moon_bigtts', 'v1', '11_linjia_girl', '邻家女孩'),
    ('zh_female_wenrouxiaoya_moon_bigtts', 'v1', '12_wenrou_xiaoya', '温柔小雅'),
    ('zh_female_qingchezizi_moon_bigtts', 'v1', '13_qingche_zizi', '清澈梓梓'),
    ('zh_female_tianmeiyueyue_moon_bigtts', 'v1', '14_tianmei_yueyue', '甜美悦悦'),
    ('zh_female_kailangjiejie_moon_bigtts', 'v1', '15_kailang_jiejie', '开朗姐姐'),
    ('zh_female_meilinvyou_moon_bigtts', 'v1', '16_meili_nvyou', '魅力女友'),
    ('zh_female_gaolengyujie_moon_bigtts', 'v1', '17_gaoleng_yujie', '高冷御姐'),
    ('BV113_streaming', 'v1', '18_tianchong_shaoyu', '甜宠少御'),
    ('BV115_streaming', 'v1', '19_gufeng_shaoyu', '古风少御'),
    ('BV700_streaming', 'v1', '20_cancan_classic', '灿灿经典'),
]

test_text = '你好呀，欢迎来到非遗世界，我是你的导览官黑塔！今天想聊些什么呢？'
storage = Path(__file__).resolve().parent / 'storage' / 'tts'
storage.mkdir(parents=True, exist_ok=True)

v3_hdrs = {
    'Content-Type': 'application/json',
    'X-Api-App-Id': settings.doubao_tts_appid,
    'X-Api-Access-Key': settings.doubao_tts_access_token,
    'X-Api-Resource-Id': 'seed-tts-2.0',
}

v1_hdrs = {
    'Content-Type': 'application/json; charset=utf-8',
    'Authorization': f'Bearer;{settings.doubao_tts_access_token}',
}


async def gen_v3(voice):
    payload = {
        'user': {'uid': 'herta_test'},
        'req_params': {
            'text': test_text,
            'speaker': voice,
            'audio_params': {'format': 'mp3', 'sample_rate': 24000},
        }
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(V3_URL, json=payload, headers=v3_hdrs)
        chunks = []
        for line in resp.text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            data_str = obj.get('data')
            if obj.get('code') == 0 and data_str:
                chunks.append(base64.b64decode(data_str))
        return b''.join(chunks) if chunks else None


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
    print('=== 20 Voices Preview ===')
    print()
    for voice, api_ver, fname, cn_name in voices:
        t = time.time()
        try:
            if api_ver == 'v3':
                audio = await gen_v3(voice)
            else:
                audio = await gen_v1(voice)
            cost = time.time() - t
            if audio and len(audio) > 0:
                fpath = storage / f'{fname}.mp3'
                fpath.write_bytes(audio)
                kb = len(audio) // 1024
                print(f'[OK] {fname:30s} | {cn_name:10s} | {kb:3d}KB | {cost:.1f}s')
            else:
                print(f'[FAIL] {fname:30s} | {cn_name:10s} | no audio')
        except Exception as e:
            print(f'[ERR] {fname:30s} | {cn_name:10s} | {str(e)[:50]}')


if __name__ == '__main__':
    asyncio.run(main())
