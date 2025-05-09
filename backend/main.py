import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import webview
import os
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import time
from pydantic import BaseModel

from database import get_db, init_db, Bookmark, Group
from bookmark_parser import BookmarkParser

app = FastAPI(title="书签管理器")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
init_db()

# 创建书签解析器实例
bookmark_parser = BookmarkParser()

# 数据模型
class BookmarkUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    tags: Optional[List[str]] = None
    parent_id: Optional[int] = None
    position: Optional[int] = None

class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

@app.get("/")
async def root():
    return {"message": "书签管理器API服务已启动"}

@app.get("/api/bookmarks/{browser_type}")
async def get_bookmarks(browser_type: str, db: Session = Depends(get_db)):
    """获取指定浏览器的书签"""
    try:
        # 从浏览器获取书签数据
        bookmark_data = bookmark_parser.get_browser_bookmarks(browser_type)
        # 解析书签数据
        bookmarks = bookmark_parser.parse_bookmarks(bookmark_data, browser_type)
        
        # 保存到数据库
        for bookmark in bookmarks:
            if bookmark['type'] == 'url':
                existing = db.query(Bookmark).filter(Bookmark.url == bookmark['url']).first()
                if existing:
                    # 更新现有书签
                    existing.tags = json.dumps(list(set(json.loads(existing.tags or '[]') + [browser_type])))
                else:
                    # 创建新书签
                    new_bookmark = Bookmark(
                        title=bookmark['title'],
                        url=bookmark['url'],
                        browser_type=browser_type,
                        tags=json.dumps([browser_type]),
                        position=bookmark['position'],
                        guid=bookmark['id']
                    )
                    db.add(new_bookmark)
        
        db.commit()
        return bookmarks
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/bookmarks/export")
async def export_bookmarks(db: Session = Depends(get_db)):
    """导出书签到浏览器"""
    try:
        # 从数据库获取所有书签
        bookmarks = db.query(Bookmark).all()
        # 转换为导出格式
        export_data = []
        for bookmark in bookmarks:
            export_data.append({
                'id': bookmark.guid,
                'type': 'url',
                'title': bookmark.title,
                'url': bookmark.url,
                'browser_type': bookmark.browser_type,
                'parent_id': bookmark.parent_id,
                'tags': json.loads(bookmark.tags) if bookmark.tags else [],
                'position': bookmark.position
            })
        
        # 导出到浏览器
        bookmark_parser.export_to_browser('chrome', export_data)
        return {"message": "书签导出成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/bookmarks/{bookmark_id}")
async def update_bookmark(
    bookmark_id: str,
    bookmark_update: BookmarkUpdate,
    db: Session = Depends(get_db)
):
    """更新书签信息"""
    try:
        bookmark = db.query(Bookmark).filter(Bookmark.guid == bookmark_id).first()
        if not bookmark:
            raise HTTPException(status_code=404, detail="未找到书签")
        
        if bookmark_update.title is not None:
            bookmark.title = bookmark_update.title
        if bookmark_update.url is not None:
            bookmark.url = bookmark_update.url
        if bookmark_update.tags is not None:
            bookmark.tags = json.dumps(bookmark_update.tags)
        if bookmark_update.parent_id is not None:
            bookmark.parent_id = bookmark_update.parent_id
        if bookmark_update.position is not None:
            bookmark.position = bookmark_update.position
        
        db.commit()
        return {"message": "书签更新成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: str, db: Session = Depends(get_db)):
    """删除书签"""
    try:
        bookmark = db.query(Bookmark).filter(Bookmark.guid == bookmark_id).first()
        if not bookmark:
            raise HTTPException(status_code=404, detail="未找到书签")
        
        db.delete(bookmark)
        db.commit()
        return {"message": "书签删除成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/bookmarks/folder")
async def create_folder(folder: FolderCreate, db: Session = Depends(get_db)):
    """创建新文件夹"""
    try:
        new_folder = Group(
            name=folder.name,
            parent_id=folder.parent_id
        )
        db.add(new_folder)
        db.commit()
        db.refresh(new_folder)
        
        return {
            'id': str(new_folder.id),
            'type': 'folder',
            'name': new_folder.name,
            'parent_id': new_folder.parent_id,
            'children': []
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/bookmarks/reorder")
async def reorder_bookmarks(
    dragging_id: str,
    drop_id: str,
    drop_type: str,
    db: Session = Depends(get_db)
):
    """重新排序书签"""
    try:
        # 获取拖拽的书签
        dragging_bookmark = db.query(Bookmark).filter(Bookmark.guid == dragging_id).first()
        if not dragging_bookmark:
            raise HTTPException(status_code=404, detail="未找到拖拽的书签")
        
        # 获取目标位置的书签
        drop_bookmark = db.query(Bookmark).filter(Bookmark.guid == drop_id).first()
        if not drop_bookmark:
            raise HTTPException(status_code=404, detail="未找到目标位置的书签")
        
        # 更新位置
        if drop_type == 'before':
            dragging_bookmark.position = drop_bookmark.position
            # 更新其他书签的位置
            db.query(Bookmark).filter(
                Bookmark.position >= drop_bookmark.position,
                Bookmark.guid != dragging_bookmark.guid
            ).update({Bookmark.position: Bookmark.position + 1})
        elif drop_type == 'after':
            dragging_bookmark.position = drop_bookmark.position + 1
            # 更新其他书签的位置
            db.query(Bookmark).filter(
                Bookmark.position > drop_bookmark.position,
                Bookmark.guid != dragging_bookmark.guid
            ).update({Bookmark.position: Bookmark.position + 1})
        
        db.commit()
        return {"message": "书签位置更新成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

def start_api():
    """启动FastAPI服务"""
    uvicorn.run(app, host="127.0.0.1", port=8000)

def start_desktop():
    """启动桌面应用"""
    # 获取前端构建文件的路径
    frontend_path = Path(__file__).parent.parent / "frontend" / "dist"
    if not frontend_path.exists():
        print("请先构建前端项目")
        return
    
    # 创建桌面窗口
    window = webview.create_window(
        '书签管理器',
        url=f'http://localhost:3000',  # 更新为新的端口号
        width=1200,
        height=800
    )
    webview.start()

if __name__ == "__main__":
    import threading
    
    # 在新线程中启动API服务
    api_thread = threading.Thread(target=start_api)
    api_thread.daemon = True
    api_thread.start()
    
    # 等待API服务启动
    time.sleep(1)
    
    # 启动桌面应用
    start_desktop() 