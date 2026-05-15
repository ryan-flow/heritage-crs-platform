#!/usr/bin/env python3
"""精简ai_service.py中的装饰性分隔线和版本号注释"""

filepath = r"d:\桌面\毕业设计\backend\app\services\ai_service.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

import re

# 删除装饰性分隔线（════════════════════════════════════════════════）
content = re.sub(r'^# ═+\s*$', '', content, flags=re.MULTILINE)

# 删除纯版本号注释行（如 # v2.0, # v2.1, # v2.1.3, # v2.4, # v2.5）
content = re.sub(r'^#\s*v\d+\.\d+[\d.]*\s*(新增|重构|升级)?\s*$', '', content, flags=re.MULTILINE)

# 删除连续多余空行（3个以上空行压缩为2个）
content = re.sub(r'\n{4,}', '\n\n\n', content)

# 删除 "── xxx ──" 格式的分隔线
content = re.sub(r'^# ──[^─]*──\s*$', '', content, flags=re.MULTILINE)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

# 统计行数
lines = content.split('\n')
print(f"精简完成! 当前行数: {len(lines)}")
