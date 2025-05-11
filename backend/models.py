# 数据模型
from pydantic import BaseModel
from typing import List, Optional


class Bookmark(BaseModel):
    id: str
    title: str
    url: str
    tags: Optional[List[str]] = []
    description: Optional[str] = None
    created_at: str
    updated_at: str

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