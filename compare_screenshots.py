"""Compare miniprogram vs Web screenshots — color and brightness analysis."""
import json
from pathlib import Path
from PIL import Image, ImageStat
import numpy as np

MP_DIR = Path(r"D:\桌面\毕业设计\帖子图片")
WEB_DIR = Path(r"D:\桌面\毕业设计\screenshots-phase1")

mp_files = sorted(MP_DIR.glob("*.png"))
web_files = sorted(WEB_DIR.glob("*.png"))

def analyze(img):
    """Get key stats from an image."""
    hsv = img.convert('HSV')
    s = ImageStat.Stat(hsv)
    # Get color histogram
    small = img.resize((100, int(img.height * 100 / img.width)))
    arr = np.array(small).reshape(-1, 3)
    # Quantize to get dominant colors
    q = (arr // 16) * 16
    uniq, counts = np.unique(q, axis=0, return_counts=True)
    top_idx = np.argsort(-counts)[:5]
    top_colors = ['#{:02x}{:02x}{:02x}'.format(*uniq[i]) for i in top_idx]
    # Overall brightness & saturation
    return {
        'size': img.size,
        'mean_brightness': round(s.mean[2], 1),
        'mean_saturation': round(s.mean[1], 1),
        'top_colors': top_colors,
    }

print("=" * 70)
print("MINIPROGRAM SCREENSHOTS")
print("=" * 70)
mp_analysis = []
for f in mp_files:
    img = Image.open(f).convert('RGB')
    a = analyze(img)
    a['name'] = f.name
    mp_analysis.append(a)
    print(f"\n{f.name} ({a['size'][0]}x{a['size'][1]})")
    print(f"  Brightness: {a['mean_brightness']:.0f}, Sat: {a['mean_saturation']:.0f}")
    print(f"  Dominant: {', '.join(a['top_colors'][:3])}")
    img.close()

print("\n" + "=" * 70)
print("WEB SCREENSHOTS (after alignment)")
print("=" * 70)
web_analysis = []
for f in web_files:
    img = Image.open(f).convert('RGB')
    a = analyze(img)
    a['name'] = f.name
    web_analysis.append(a)
    print(f"\n{f.name} ({a['size'][0]}x{a['size'][1]})")
    print(f"  Brightness: {a['mean_brightness']:.0f}, Sat: {a['mean_saturation']:.0f}")
    print(f"  Dominant: {', '.join(a['top_colors'][:3])}")
    img.close()

# Quick comparison
print("\n" + "=" * 70)
print("COMPARISON SUMMARY")
print("=" * 70)
for mp, web in zip(mp_analysis, web_analysis):
    b_diff = web['mean_brightness'] - mp['mean_brightness']
    s_diff = web['mean_saturation'] - mp['mean_saturation']
    print(f"\n{mp['name']} vs {web['name']}:")
    print(f"  Brightness diff: {b_diff:+.0f} {'(web lighter)' if b_diff > 0 else '(web darker)'}")
    print(f"  Saturation diff: {s_diff:+.0f} {'(web more saturated)' if s_diff > 0 else '(web less saturated)'}")
