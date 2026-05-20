"""Analyze miniprogram screenshots — extract colors, layout, and design tokens."""
import json, os, sys
from pathlib import Path
from PIL import Image, ImageFilter, ImageStat
import numpy as np
from collections import Counter

IMG_DIR = Path(r"D:\桌面\毕业设计\帖子图片")
files = sorted(IMG_DIR.glob("*.png"))

def dominant_colors(img, n=6):
    """K-means on resized image to find dominant colors."""
    small = img.resize((150, int(img.height * 150 / img.width)))
    arr = np.array(small).reshape(-1, 3)
    # Pick n most frequent after quantizing to 32 levels
    quantized = (arr // 8) * 8
    # Get unique colors with counts
    uniq, counts = np.unique(quantized, axis=0, return_counts=True)
    top_idx = np.argsort(-counts)[:n*3]
    top = uniq[top_idx]
    # Cluster nearby colors by merging within 30 distance
    colors = []
    seen = set()
    for c in top:
        key = tuple(c)
        if key in seen:
            continue
        # Average with similar colors
        similar = [c2 for c2 in top if np.linalg.norm(c.astype(float) - c.astype(float)) < 50]
        avg = np.mean(similar, axis=0).astype(int)
        tk = tuple(avg)
        if tk not in seen:
            colors.append({'hex': '#{:02x}{:02x}{:02x}'.format(*avg), 'rgb': avg.tolist()})
            for s in similar:
                seen.add(tuple(s))
    return colors[:n]

def layout_hints(img):
    """Detect horizontal bands by looking at row variance."""
    small = img.resize((300, int(img.height * 300 / img.width)))
    gray = small.convert('L')
    arr = np.array(gray)
    # Row-wise variance — low variance = solid band
    row_var = np.var(arr, axis=1)
    # Find transitions (gradient of variance)
    grad = np.abs(np.diff(row_var))
    # Normalize
    grad = grad / (grad.max() or 1)
    # Find peaks (layout boundaries)
    threshold = np.percentile(grad, 85)
    boundaries = [int(i * img.height / len(grad)) for i, v in enumerate(grad) if v > threshold]
    # Merge nearby boundaries
    merged = []
    for b in boundaries:
        if not merged or b - merged[-1] > 30:
            merged.append(b)
    return merged

def color_statistics(img):
    """Get brightness, saturation stats."""
    hsv = img.convert('HSV')
    stat = ImageStat.Stat(hsv)
    return {
        'mean_brightness': round(stat.mean[2], 1),
        'mean_saturation': round(stat.mean[1], 1),
    }

def guess_typography(img):
    """Rough guess: check aspect ratio and dominant text-like regions."""
    w, h = img.size
    aspect = round(w / h, 2)
    is_mobile = aspect < 1  # portrait
    return {
        'orientation': 'portrait' if is_mobile else 'landscape',
        'aspect_ratio': aspect,
        'is_mobile': is_mobile,
    }

for f in files:
    print(f"\n{'='*60}")
    print(f"FILE: {f.name}")
    print(f"{'='*60}")
    img = Image.open(f).convert('RGB')
    w, h = img.size
    print(f"Size: {w}x{h}")

    typo = guess_typography(img)
    print(f"Orientation: {typo['orientation']} ({typo['aspect_ratio']})")

    # Dominant colors
    colors = dominant_colors(img, 6)
    print("Dominant colors (approx):")
    for i, c in enumerate(colors):
        bar = '█' * (6 - i)
        print(f"  {bar} {c['hex']}  rgb({c['rgb'][0]},{c['rgb'][1]},{c['rgb'][2]})")

    # Stats
    stats = color_statistics(img)
    print(f"Brightness: {stats['mean_brightness']:.1f}, Saturation: {stats['mean_saturation']:.1f}")

    # Layout boundaries
    bounds = layout_hints(img)
    if bounds:
        print(f"Layout boundaries at y ≈ {bounds}")

    img.close()
