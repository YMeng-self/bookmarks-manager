from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, HttpUrl, Field, validator

class BookmarkCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl
    tags: Optional[List[str]] = Field(default_factory=list)
    description: Optional[str] = Field(default=None, max_length=500)

    @validator('tags', each_item=True)
    def validate_tags(cls, v):
        if ':' in v and not (v.startswith('category:') or v.startswith('system:')):
            raise ValueError('包含冒号的标签必须以"category:"或"system:"开头')
        return v.lower()  # 统一转为小写

class BookmarkResponse(BookmarkCreate):
    id: int
    guid: str
    visit_count: int
    created_at: datetime
    updated_at: datetime
    categories: List[str]  # 单独暴露分类

    class Config:
        orm_mode = True