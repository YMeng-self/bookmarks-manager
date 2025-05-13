# 数据库操作

# 导入数据库操作模块
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base

import os
from pathlib import Path


# 创建数据库目录
db_dir = Path(__file__).parent / "data"
db_dir.mkdir(exist_ok=True)

# 初始化 SQLite 数据库
SQLITE_URL = f"sqlite:///{db_dir}/bookmarks.db"
engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    echo=False  # 可选：显示SQL日志
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库，创建表"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()