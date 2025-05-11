from database import SessionLocal
from models import BookmarkDB

db = SessionLocal()
bookmarks = db.query(BookmarkDB).limit(10).all()
for bm in bookmarks:
    print(f"{bm.id}. {bm.title}")
    print(f"URL: {bm.url}")
    print(f"分类: {bm.categories}")
    print(f"标签: {bm.tags}")
    print("-" * 50)
db.close()