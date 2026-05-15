from __future__ import annotations

import requests

js = requests.get('http://ich.tju.edu.cn/assets/index-d4d90bcf.js', timeout=30).text
keywords = ['/api', '/news', '/article', '/detail', '/list', '/page', 'baseURL', 'router', 'createRouter']
for keyword in keywords:
    idx = js.find(keyword)
    print(f'=== {keyword} @ {idx} ===')
    if idx != -1:
        snippet = js[max(0, idx - 300): idx + 1200]
        print(snippet)
        print('---')
