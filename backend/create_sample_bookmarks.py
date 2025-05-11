import random
from datetime import datetime, timedelta
from database import SessionLocal, init_db
from models import BookmarkDB
from faker import Faker

# 初始化
fake = Faker()
init_db()
db = SessionLocal()

# 预定义的分类和标签
CATEGORIES = [
    "documentation",
    "tutorial",
    "reference",
    "blog",
    "news",
    "tool",
    "video",
    "course"
]

COMMON_TAGS = [
    "python",
    "javascript",
    "web",
    "development",
    "programming",
    "database",
    "frontend",
    "backend",
    "devops",
    "ai"
]

# 生成随机书签数据
def generate_sample_bookmarks(num: int = 20):
    for _ in range(num):
        # 随机选择1-3个分类
        categories = random.sample(CATEGORIES, k=random.randint(1, 3))
        category_tags = [f"category:{cat}" for cat in categories]
        
        # 随机选择2-5个普通标签
        regular_tags = random.sample(COMMON_TAGS, k=random.randint(2, 5))
        
        # 随机创建日期（最近3年内）
        created_at = fake.date_time_between(
            start_date="-3y", 
            end_date="now"
        )
        
        bookmark = BookmarkDB(
            title=fake.sentence(nb_words=4).rstrip('.'),
            url=fake.url(),
            tags=category_tags + regular_tags,
            description=fake.paragraph(nb_sentences=2),
            visit_count=random.randint(0, 500),
            created_at=created_at,
            updated_at=created_at + timedelta(days=random.randint(0, 100))
        )
        
        db.add(bookmark)
    
    db.commit()
    print(f"成功创建 {num} 个示例书签")

if __name__ == "__main__":
    try:
        generate_sample_bookmarks(30)  # 创建30个示例书签
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        db.close()