#!/usr/bin/env python3
"""删除ai_service.py中与crs/子包重复的代码"""

import re

filepath = r"d:\桌面\毕业设计\backend\app\services\ai_service.py"

with open(filepath, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 找到需要删除的行范围
start_marker = "# 从本地知识库动态提取问题作为推荐按钮，确保100%KB命中率"
end_marker = "def _ask_doubao_with_fallback("

start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if start_marker in line and start_idx is None:
        start_idx = i
    if line.strip().startswith(end_marker) and end_idx is None and start_idx is not None:
        end_idx = i
        break

if start_idx is not None and end_idx is not None:
    print(f"找到重复代码范围: L{start_idx+1} - L{end_idx}")
    print(f"将删除 {end_idx - start_idx} 行")
    
    # 删除中间的重复代码，保留end_marker行
    new_lines = lines[:start_idx] + ["\n"] + lines[end_idx:]
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    print(f"删除完成! 原始行数: {len(lines)}, 新行数: {len(new_lines)}")
else:
    print(f"未找到标记! start_idx={start_idx}, end_idx={end_idx}")
