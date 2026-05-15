import sys; sys.path.insert(0, ".")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.services.recommendation_service import calc_confidence

engine = create_engine(settings.sqlite_url)
db = sessionmaker(bind=engine)()

for uid in [16, 229]:
    u = db.query(User).filter(User.id == uid).first()
    if not u:
        print(f"User[{uid}]: NOT FOUND")
        continue
    c = calc_confidence(db, uid)
    print(f"User[{uid}]: mode={c['mode']}, score={c['confidence_score']:.1f}")
    print(f"  heritage={u.preferred_heritage_types}")
    print(f"  scene={u.preferred_scene_types}")
    print(f"  region={u.preferred_regions}")

db.close()
