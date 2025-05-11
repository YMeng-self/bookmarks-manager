# 数据模型
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, HttpUrl, Field, validator
import uuid

# --------------------- #
# 数据库模型 (SQLAlchemy) #
# --------------------- #
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
import json
import uuid
from typing import List

Base = declarative_base()

class BookmarkDB(Base):
    __tablename__ = "bookmarks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    _tags = Column("tags", Text, default="[]")
    description = Column(Text)
    visit_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def tags(self) -> List[str]:
        return json.loads(self._tags)

    @tags.setter
    def tags(self, value: List[str]):
        self._tags = json.dumps(list(set(value)) if value else [])  # 自动去重

    @property
    def categories(self) -> List[str]:
        """提取所有分类标签"""
        return [tag.split(':', 1)[1] for tag in self.tags if tag.startswith('category:')]

    def add_category(self, category: str):
        """添加分类"""
        category_tag = f"category:{category.lower()}"
        if category_tag not in self.tags:
            self.tags = self.tags + [category_tag]

    def remove_category(self, category: str):
        """移除分类"""
        category_tag = f"category:{category.lower()}"
        self.tags = [tag for tag in self.tags if tag != category_tag]

    def has_category(self, category: str) -> bool:
        """检查是否属于某分类"""
        return f"category:{category.lower()}" in self.tags

    def __repr__(self):
        return f"<Bookmark(id={self.id}, title='{self.title}')>"


# --------------------------------------------------#
class Bookmark(BaseModel):
    guid: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Globally unique identifier (UUID)",
        alias="GUID"
    )
    id: int = Field(
        default=None,
        description="Auto-incrementing numeric ID",
        gt=0
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Title of the bookmark"
    )
    url: HttpUrl = Field(
        ...,
        description="URL of the bookmark"
    )
    # type: Literal["article", "video", "tool", "documentation", "other"] = Field(
    #     default="article",
    #     description="Type of the bookmark content"
    # )
    tags: Optional[List[str]] = Field(
        default_factory=list,
        max_items=10,
        description="List of tags for categorization"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Brief description of the bookmark content"
    )
    visit_count: int = Field(
        default=0,
        description="Number of times the bookmark was accessed",
        ge=0
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of creation"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of last update"
    )

    @validator("tags", each_item=True)
    def validate_tags(cls, v):
        if not v.isalnum():
            raise ValueError("Tags should be alphanumeric")
        return v.lower()

    @validator("title")
    def validate_title(cls, v):
        return v.strip()

    # @validator("id", pre=True, always=True)
    # def set_id_if_none(cls, v):
    #     # 注意：实际应用中应该从数据库获取自增ID
    #     # 这里只是演示，实际应该由数据库自动生成
    #     return v if v is not None else 0  # 临时值，实际应由DB生成

    @validator("id", pre=True, always=True)
    def validate_id(cls, v):
        if v is not None:
            raise ValueError("id should be assigned by database")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "guid": "550e8400-e29b-41d4-a716-446655440000",
                "id": 1,
                "title": "Example Bookmark",
                "url": "https://example.com",
                # "type": "article",
                "tags": ["python", "webdev"],
                "description": "An example bookmark",
                "visit_count": 0,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }


class BookmarkCreate(BaseModel):
    title: str
    url: str
    tags: Optional[List[str]] = []
    description: Optional[str] = None


class BookmarkUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    tags: Optional[List[str]] = None
    description: Optional[str] = None

# 验证数据
# data = {
#                 "guid": "550e8400-e29b-41d4-a716-446655440000",
#                 "id": 1,
#                 "title": "Example Bookmark",
#                 "url": "https://example.com",
#                 "tags": ["python", "webdev"],
#                 "description": "An example bookmark",
#                 "visit_count": 0,
#                 "created_at": "2023-01-01T00:00:00",
#                 "updated_at": "2023-01-01T00:00:00"
#             }
# bookmark = Bookmark(**data)  # 自动验证字段类型和约束
# print(bookmark.title)  # 输出: "Python Docs"