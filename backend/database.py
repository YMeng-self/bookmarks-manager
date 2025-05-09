from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from pathlib import Path

# 创建数据库目录
db_dir = Path(__file__).parent / "data"
db_dir.mkdir(exist_ok=True)

# 数据库连接
DATABASE_URL = f"sqlite:///{db_dir}/bookmarks.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    browser_type = Column(String)
    title = Column(String)
    url = Column(String)
    parent_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    tags = Column(String)  # 存储为JSON字符串
    position = Column(Integer)
    guid = Column(String, unique=True)

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    parent_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    # 关系
    bookmarks = relationship("Bookmark", backref="group")
    children = relationship("Group", backref=__tablename__)

# 创建数据库表
def init_db():
    Base.metadata.create_all(bind=engine)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 