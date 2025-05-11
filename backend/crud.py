from sqlalchemy.orm import Session
from models import BookmarkDB
from typing import List, Optional


class BookmarkRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, bookmark_data: dict) -> BookmarkDB:
        bookmark = BookmarkDB(**bookmark_data)
        self.db.add(bookmark)
        self.db.commit()
        self.db.refresh(bookmark)
        return bookmark

    def get_by_id(self, id: int) -> Optional[BookmarkDB]:
        return self.db.query(BookmarkDB).filter(BookmarkDB.id == id).first()

    def get_by_category(self, category: str) -> List[BookmarkDB]:
        category_tag = f"category:{category.lower()}"
        return self.db.query(BookmarkDB).filter(
            BookmarkDB._tags.contains(f'"{category_tag}"')
        ).all()

    def update_tags(self, id: int, tags: List[str]) -> Optional[BookmarkDB]:
        bookmark = self.get_by_id(id)
        if bookmark:
            bookmark.tags = tags
            self.db.commit()
            self.db.refresh(bookmark)
        return bookmark

    def add_category(self, id: int, category: str) -> Optional[BookmarkDB]:
        bookmark = self.get_by_id(id)
        if bookmark:
            bookmark.add_category(category)
            self.db.commit()
            self.db.refresh(bookmark)
        return bookmark

    def remove_category(self, id: int, category: str) -> Optional[BookmarkDB]:
        bookmark = self.get_by_id(id)
        if bookmark:
            bookmark.remove_category(category)
            self.db.commit()
            self.db.refresh(bookmark)
        return bookmark