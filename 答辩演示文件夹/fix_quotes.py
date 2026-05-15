with open(r'd:\桌面\毕业设计\答辩演示文件夹\generate_ppt.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
for i, line in enumerate(lines):
    for ch in line:
        if ch == '\u201c' or ch == '\u201d' or ch == '\u2018' or ch == '\u2019':
            print(f'Line {i+1}: found smart quote U+{ord(ch):04X}')
            break

for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('"'):
        count = stripped.count('"')
        if count > 2:
            print(f'Line {i+1} has {count} double quotes: {stripped[:100]}')
