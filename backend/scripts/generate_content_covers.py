"""Generate SVG cover images for all content that lacks them."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.content import Content
import hashlib

# Category-based color schemes
CATEGORY_COLORS = {
    '传统工艺': ('#8B4513', '#D2691E', '🪡'),
    '戏曲音乐': ('#800020', '#B22222', '🎭'),
    '民俗节俗': ('#D2691E', '#CD853F', '🏮'),
    '饮食医药': ('#2E8B57', '#3CB371', '🍵'),
    '民间文学': ('#4169E1', '#6495ED', '📚'),
    '传统美术': ('#8B008B', '#BA55D3', '🎨'),
    '传统体育': ('#006400', '#228B22', '⚔️'),
    '传统舞蹈': ('#C71585', '#FF69B4', '💃'),
    '传统医药': ('#008080', '#20B2AA', '🌿'),
}

DEFAULT_COLOR = ('#5C3317', '#8B5A3C', '🏛️')

def generate_cover(title: str, category: str = '') -> str:
    colors = CATEGORY_COLORS.get(category, DEFAULT_COLOR)
    c1, c2, emoji = colors
    slug = hashlib.md5(title.encode()).hexdigest()[:8]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{c1}"/>
      <stop offset="100%" style="stop-color:{c2}"/>
    </linearGradient>
    <pattern id="dots" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
      <circle cx="20" cy="20" r="1.5" fill="rgba(255,255,255,0.12)"/>
    </pattern>
  </defs>
  <rect width="400" height="300" fill="url(#bg)"/>
  <rect width="400" height="300" fill="url(#dots)"/>
  <text x="200" y="140" text-anchor="middle" font-size="48" font-family="sans-serif" fill="rgba(255,255,255,0.85)">{emoji}</text>
  <text x="200" y="200" text-anchor="middle" font-size="16" font-family="sans-serif" fill="rgba(255,255,255,0.7)">
    {title[:12]}{'...' if len(title) > 12 else ''}
  </text>
</svg>'''
    return svg

def main():
    covers_dir = os.path.join(os.path.dirname(__file__), '..', 'storage', 'covers')
    os.makedirs(covers_dir, exist_ok=True)

    db = SessionLocal()
    try:
        contents = db.query(Content).all()
        updated = 0
        for c in contents:
            if c.cover_url and c.cover_url.strip():
                continue  # already has cover

            svg = generate_cover(c.title or '非遗内容', c.content_type or '')
            filename = f'cover_{c.id}_{hashlib.md5((c.title or "").encode()).hexdigest()[:6]}.svg'
            filepath = os.path.join(covers_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(svg)

            c.cover_url = f'/storage/covers/{filename}'
            updated += 1

        db.commit()
        print(f'Generated {updated} cover images out of {len(contents)} total contents')
    finally:
        db.close()

if __name__ == '__main__':
    main()
