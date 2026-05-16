#!/usr/bin/env python3
"""Migration: Update cover_url to point to real _1.jpg images.

Run this on the production server:
  python scripts/fix_cover_urls.py
"""
import sqlite3
import os
import re
import hashlib
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'heritage_platform.db')
COVERS_DIR = os.path.join(os.path.dirname(__file__), '..', 'storage', 'covers')

def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if not os.path.exists(COVERS_DIR):
        print(f"WARNING: Covers dir not found at {COVERS_DIR}")
        os.makedirs(COVERS_DIR, exist_ok=True)

    files = os.listdir(COVERS_DIR) if os.path.exists(COVERS_DIR) else []

    # ── 1. Update content cover_url to real _1.jpg files ──
    updated_content = 0
    for f in files:
        m = re.match(r'^content_(\d+)_1\.jpg$', f)
        if m:
            cid = int(m.group(1))
            new_url = f'/storage/covers/{f}'
            cur.execute('UPDATE contents SET cover_url=? WHERE id=?', (new_url, cid))
            if cur.rowcount > 0:
                updated_content += 1

    conn.commit()
    print(f'[Content] Updated {updated_content} records to real JPG images')

    # ── 2. Update activity cover_url to real _1.jpg files ──
    updated_activity = 0
    for f in files:
        m = re.match(r'^activity_(\d+)_1\.jpg$', f)
        if m:
            aid = int(m.group(1))
            new_url = f'/storage/covers/{f}'
            cur.execute('UPDATE activities SET cover_url=? WHERE id=?', (new_url, aid))
            if cur.rowcount > 0:
                updated_activity += 1

    conn.commit()
    print(f'[Activity] Updated {updated_activity} records to real JPG images')

    # ── 3. Generate SVG covers for content without real images ──
    cur.execute("SELECT id, title FROM contents WHERE cover_url NOT LIKE '%_1.jpg'")
    missing_content = cur.fetchall()

    COLORS = [
        ('#6B3A2A', '#9B4F3C', '\U0001F4D6'),
        ('#2E5A3D', '#4A8C5E', '\U0001F3DB'),
        ('#5B2A5A', '#8B4580', '\U0001F3AD'),
        ('#2A3A6B', '#4A5C9B', '\U0001F3B5'),
        ('#6B5A2A', '#9B8B4C', '\U0001F3FA'),
    ]

    for cid, title in missing_content:
        h = int(hashlib.md5(title.encode() if title else b'content').hexdigest()[:8], 16)
        c1, c2, emoji = COLORS[h % len(COLORS)]
        slug = hashlib.md5((title or 'content').encode()).hexdigest()[:8]

        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300"><defs><linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:{c1}"/><stop offset="100%" style="stop-color:{c2}"/></linearGradient><pattern id="dots" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="0.8" fill="rgba(255,255,255,0.12)"/></pattern></defs><rect width="400" height="300" fill="url(#bg)"/><rect width="400" height="300" fill="url(#dots)"/><text x="200" y="130" text-anchor="middle" font-size="48" fill="rgba(255,255,255,0.85)">{emoji}</text><text x="200" y="190" text-anchor="middle" font-size="15" fill="rgba(255,255,255,0.75)" font-family="sans-serif">{(title or 'Content')[:15]}</text></svg>'

        filename = f'cover_{cid}_{slug}.svg'
        filepath = os.path.join(COVERS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg)

        cur.execute('UPDATE contents SET cover_url=? WHERE id=?', (f'/storage/covers/{filename}', cid))

    conn.commit()
    print(f'[Content] Generated {len(missing_content)} SVG covers')

    # ── 4. Generate SVG covers for activities without real images ──
    cur.execute("SELECT id, title FROM activities WHERE cover_url NOT LIKE '%_1.jpg'")
    missing_activity = cur.fetchall()

    ACT_COLORS = [
        ('#8B4513', '#A0522D', '\U0001F4C5'),
        ('#5B3A7A', '#7B5AAA', '\U0001F3AA'),
        ('#2E7D32', '#4CAF50', '\U0001F3AF'),
        ('#E65100', '#FF9800', '\U0001F91D'),
        ('#1565C0', '#42A5F5', '\U0001F389'),
    ]

    for aid, title in missing_activity:
        h = int(hashlib.md5(title.encode() if title else b'activity').hexdigest()[:8], 16)
        c1, c2, emoji = ACT_COLORS[h % len(ACT_COLORS)]
        slug = hashlib.md5((title or 'activity').encode()).hexdigest()[:8]

        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300"><defs><linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:{c1}"/><stop offset="100%" style="stop-color:{c2}"/></linearGradient><pattern id="dots" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="0.8" fill="rgba(255,255,255,0.12)"/></pattern></defs><rect width="400" height="300" fill="url(#bg)"/><rect width="400" height="300" fill="url(#dots)"/><text x="200" y="130" text-anchor="middle" font-size="48" fill="rgba(255,255,255,0.85)">{emoji}</text><text x="200" y="190" text-anchor="middle" font-size="15" fill="rgba(255,255,255,0.75)" font-family="sans-serif">{(title or 'Activity')[:15]}</text></svg>'

        filename = f'activity_{aid}_{slug}.svg'
        filepath = os.path.join(COVERS_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg)

        cur.execute('UPDATE activities SET cover_url=? WHERE id=?', (f'/storage/covers/{filename}', aid))

    conn.commit()
    print(f'[Activity] Generated {len(missing_activity)} SVG covers')

    # ── Final stats ──
    cur.execute('SELECT COUNT(*) FROM contents WHERE cover_url IS NOT NULL AND cover_url != ""')
    c = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM activities WHERE cover_url IS NOT NULL AND cover_url != ""')
    a = cur.fetchone()[0]
    print(f'\nDone: {c} contents + {a} activities have cover images')
    conn.close()

if __name__ == '__main__':
    main()
