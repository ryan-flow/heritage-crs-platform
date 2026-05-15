import win32gui, win32api, win32con, win32ui, ctypes
from PIL import Image
import numpy as np

def find_wechat_devtools():
    result = []
    def callback(hwnd, extra):
        title = win32gui.GetWindowText(hwnd)
        if title:
            rect = win32gui.GetWindowRect(hwnd)
            visible = win32gui.IsWindowVisible(hwnd)
            cls = win32gui.GetClassName(hwnd)
            if visible and rect[2] > 100 and rect[3] > 100:
                result.append({'hwnd': hwnd, 'title': title, 'rect': rect, 'cls': cls})
    win32gui.EnumWindows(callback, None)
    # 按标题过滤可能相关的窗口
    relevant = [w for w in result if any(k in w['title'] for k in ['微信', 'devtools', 'miniprogram', '非遗'])]
    return relevant, result[:20]

relevant, all_windows = find_wechat_devtools()
print("=== 可能相关的窗口 ===")
for w in relevant:
    print(f"标题: {w['title']}")
    print(f"  类名: {w['cls']}")
    print(f"  位置: {w['rect']}")
    print()
print("=== 前20个窗口 ===")
for w in all_windows:
    print(f"标题: {w['title'][:50]} | 类: {w['cls'][:30]} | {w['rect']}")
