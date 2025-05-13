# FastAPI主应用
from fastapi import FastAPI, UploadFile
from fastapi import File, Query, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from typing import List, Optional, Dict, Any
import json
from pathlib import Path
from .models import BookmarkDB
from .database import get_db, SessionLocal
from sqlalchemy.orm import Session
from datetime import datetime

# 创建FastAPI应用
app = FastAPI(title="Bookmarks Manager API", version="1.0.0")

# 挂载前端静态文件 (PyWebView将使用这些文件)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


# 工具函数
def parse_chrome_bookmarks(chrome_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """解析Chrome书签导出文件格式"""
    bookmarks = []
    
    def process_node(node: Dict[str, Any]):
        if node.get("type") == "url":
            bookmark = {
                "title": node.get("name", ""),
                "url": node.get("url", ""),
                "tags": ["category:" + node.get("category", "")] if node.get("category") else []
            }
            bookmarks.append(bookmark)
        elif node.get("children"):
            for child in node["children"]:
                process_node(child)
    
    if "roots" in chrome_data:
        for root in chrome_data["roots"].values():
            process_node(root)
    
    return bookmarks


def parse_edge_bookmarks(edge_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """解析Edge书签导出文件格式"""
    bookmarks = []
    
    def process_node(node: Dict[str, Any]):
        if node.get("type") == "url":
            bookmark = {
                "title": node.get("name", ""),
                "url": node.get("url", ""),
                "tags": ["category:" + node.get("category", "")] if node.get("category") else []
            }
            bookmarks.append(bookmark)
        elif node.get("children"):
            for child in node["children"]:
                process_node(child)
    
    if "roots" in edge_data:
        for root in edge_data["roots"].values():
            process_node(root)
    
    return bookmarks


@app.post("/api/bookmarks", tags=["书签管理"])
async def create_bookmark(
    bookmark_data: dict,
    db: Session = Depends(get_db)
):
    """创建新书签"""
    new_bookmark = BookmarkDB(**bookmark_data)
    db.add(new_bookmark)
    db.commit()
    db.refresh(new_bookmark)
    return new_bookmark

@app.get("/api/bookmarks", tags=["书签管理"])
async def get_all_bookmarks(
    db: Session = Depends(get_db),
    folder: Optional[str] = Query(None, description="按分类过滤书签")
):
    """获取所有书签列表，支持按分类过滤"""
    query = db.query(BookmarkDB)
    if folder:
        # 由于部不是数组，所以不能直接使用contains方法，而是使用like方法
        # query = query.filter(BookmarkDB.tags.contains(f"category:{folder}"))
        query = query.filter(BookmarkDB._tags.like(f'%"category:{folder}"%'))
    return query.all()

@app.get("/api/bookmarks/{id:int}", tags=["书签管理"])
async def get_bookmark(
    id: int,
    db: Session = Depends(get_db)
):
    """根据ID获取单个书签"""
    bookmark = db.query(BookmarkDB).filter(BookmarkDB.id == id).first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return bookmark


@app.put("/api/bookmarks/{id:int}", tags=["书签管理"])
async def update_bookmark(
    id: int,
    bookmark_data: dict,
    db: Session = Depends(get_db)
):
    """更新书签信息(当前这个更新的函数有问题)"""
    # 特殊处理 tags 字段，转换为 JSON 字符串
    print(bookmark_data)  # 打印接收到的数据，用于调试
    print(bookmark_data.get('_tags'))  # 打印 tags 字段的值，用于调试
    print(isinstance(bookmark_data.get('_tags'), list))  # 打印 tags 字段的类型，用于调试
    bookmark = db.query(BookmarkDB).filter(BookmarkDB.id == id).first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
   
    if '_tags' in bookmark_data:
        if isinstance(bookmark_data['_tags'], list):
            bookmark_data.tags = json.dumps(bookmark_data['_tags'])
            del bookmark_data['_tags']
    
    print(bookmark_data)  # 打印接收到的数据，用于调试
    print(bookmark_data.get('_tags'))  # 打印 tags 字段的值，用于调试
    print(isinstance(bookmark_data.get('_tags'), list))  # 打印 tags 字段的类型，用于调试
    # 更新其他字段
    for key, value in bookmark_data.items():
        print(key, value)  # 打印每个字段的键和值，用于调试
        setattr(bookmark, key, value)
    
    # 自动更新修改时间
    bookmark.updated_at = datetime.now()

    print(bookmark._tags)  # 打印接收到的数据，用于调试
    
    db.commit()
    db.refresh(bookmark)
    return bookmark

@app.delete("/api/bookmarks/{id:int}", tags=["书签管理"])
async def delete_bookmark(
    id: int,
    db: Session = Depends(get_db)
):
    """删除书签"""
    bookmark = db.query(BookmarkDB).filter(BookmarkDB.id == id).first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    db.delete(bookmark)
    db.commit()
    return {"message": "Bookmark deleted successfully"}

# @app.post("/api/bookmarks/{id}/categories/{category}", tags=["书签管理"])
# async def add_bookmark_category(
#     id: int, 
#     category: str,
#     db: Session = Depends(get_db)
# ):
#     """为书签添加分类"""
#     bookmark = db.query(BookmarkDB).filter(BookmarkDB.id == id).first()
#     if not bookmark:
#         raise HTTPException(status_code=404, detail="Bookmark not found")
    
#     bookmark.add_category(category)
#     db.commit()
#     db.refresh(bookmark)
#     return {"message": f"Category '{category}' added successfully"}

@app.delete("/api/bookmarks/{id}/categories/{category}", tags=["书签管理"])
async def remove_bookmark_category(
    id: int, 
    category: str,
    db: Session = Depends(get_db)
):
    """从书签移除分类"""
    bookmark = db.query(BookmarkDB).filter(BookmarkDB.id == id).first()
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    bookmark.remove_category(category)
    db.commit()
    db.refresh(bookmark)
    return {"message": f"Category '{category}' removed successfully"}

@app.get("/api/bookmarks/stats", tags=["书签管理"])
async def get_bookmark_stats(db: Session = Depends(get_db)):
    # 获取所有书签，并按照分类统计书签数量
    bookmarks = db.query(BookmarkDB).all()
    
    stats = {
        "categories": {},
        "_uncategorized": 0,
        "_totalbookmarks": len(bookmarks)
    }

    for bookmark in bookmarks:
        if not bookmark.tags or len(bookmark.tags) == 0:
            stats["_uncategorized"] += 1
            continue
            
        # 统计分类
        for tag in bookmark.tags:
            if tag.startswith("category:"):
                category = tag.replace("category:", "")
                stats["categories"][category] = stats["categories"].get(category, 0) + 1
                
    return stats

# @app.post("/api/bookmarks/import", tags=["书签管理"])
# async def import_bookmarks(
#     file: UploadFile = File(...),
#     source: str = Query("local", description="导入来源: local/chrome/edge")
# ):
#     """
#     导入书签
#     - 支持从本地文件、Chrome和Edge浏览器导入
#     - 参数:
#         file: 上传的文件
#         source: 导入来源 (local/chrome/edge)
#     """
#     content = await file.read()
    
#     if source == "local":
#         # 处理本地JSON文件
#         try:
#             bookmarks = json.loads(content)
#         except json.JSONDecodeError:
#             raise HTTPException(status_code=400, detail="Invalid JSON format")
#     elif source == "chrome":
#         # 处理Chrome书签导出文件
#         try:
#             chrome_data = json.loads(content)
#             bookmarks = parse_chrome_bookmarks(chrome_data)
#         except Exception as e:
#             raise HTTPException(status_code=400, detail=f"Failed to parse Chrome bookmarks: {str(e)}")
#     elif source == "edge":
#         # 处理Edge书签导出文件
#         try:
#             edge_data = json.loads(content)
#             bookmarks = parse_edge_bookmarks(edge_data)
#         except Exception as e:
#             raise HTTPException(status_code=400, detail=f"Failed to parse Edge bookmarks: {str(e)}")
#     else:
#         raise HTTPException(status_code=400, detail="Invalid source specified")
    
#     # 保存书签到数据库
#     db = SessionLocal()
#     try:
#         for bookmark in bookmarks:
#             db_bookmark = BookmarkDB(**bookmark)
#             db.add(db_bookmark)
#         db.commit()
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to save bookmarks: {str(e)}")
#     finally:
#         db.close()
    
#     return {"message": f"Successfully imported {len(bookmarks)} bookmarks from {source}"}

@app.get("/api/bookmarks/export", response_class=FileResponse, tags=["书签管理"])
async def export_bookmarks(
    format: str = Query("local", description="导出格式: local/chrome/edge"),
    db: Session = Depends(get_db)
):
    """
    导出书签
    - 支持导出到本地JSON、Chrome和Edge格式
    - 参数:
        format: 导出格式 (local/chrome/edge)
    """
    bookmarks = db.query(BookmarkDB).all()
    
    # 转换为基本格式
    base_bookmarks = [
        {
            "title": b.title,
            "url": b.url,
            "tags": b.tags
        }
        for b in bookmarks
    ]
    
    if format == "local":
        # 本地JSON格式
        export_data = base_bookmarks
    elif format == "chrome":
        # Chrome书签格式
        export_data = {
            "roots": {
                "bookmark_bar": {
                    "children": [
                        {
                            "name": b["title"],
                            "type": "url",
                            "url": b["url"],
                            "category": next((t.replace("category:", "") for t in b["tags"] if t.startswith("category:")), "")
                        }
                        for b in base_bookmarks
                    ]
                }
            }
        }
    elif format == "edge":
        # Edge书签格式
        export_data = {
            "roots": {
                "bookmark_bar": {
                    "children": [
                        {
                            "name": b["title"],
                            "type": "url",
                            "url": b["url"],
                            "category": next((t.replace("category:", "") for t in b["tags"] if t.startswith("category:")), "")
                        }
                        for b in base_bookmarks
                    ]
                }
            }
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid format specified")
    
    # 创建临时文件
    temp_file = Path("temp_bookmarks.json")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    return FileResponse(
        temp_file,
        media_type="application/json",
        filename=f"bookmarks_{format}.json"
    )


import os
import json
from datetime import datetime
from fastapi import UploadFile, HTTPException
from bs4 import BeautifulSoup
from fastapi import Form, UploadFile, File

@app.post("/api/bookmarks/import", tags=["书签管理"])
async def import_bookmarks(
    file: UploadFile = File(None),
    browser_type: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    导入书签
    - file: 上传的HTML文件
    - browser_type: 浏览器类型 (chrome/edge)
    """

    print(f"Received - file: {file}, browser_type: {browser_type}")

    
    try:
        # 1. 获取书签数据
        if file:
            bookmarks_data = parse_html_bookmarks(await file.read())
        elif browser_type in ["chrome", "edge"]:
            bookmarks_data = get_browser_bookmarks(browser_type)
        else:
            raise HTTPException(status_code=400, detail="必须提供文件或浏览器类型")
        
        # 2. 处理书签数据
        processed = process_bookmarks(bookmarks_data, db)
        
        # 3. 保存到数据库
        for bookmark in processed["new_bookmarks"]:
            db_bookmark = BookmarkDB(
                title=bookmark["title"],
                url=bookmark["url"],
                _tags=json.dumps(bookmark["tags"]),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(db_bookmark)
        
        db.commit()
        
        return {
            "total": len(bookmarks_data),
            "imported": len(processed["new_bookmarks"]),
            "duplicates": len(processed["duplicates"]),
            "tags_added": processed["tags_added"]
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

def parse_html_bookmarks(file_content):
    """解析HTML格式的书签文件"""
    soup = BeautifulSoup(file_content, "html.parser")
    bookmarks = []
    
    for a in soup.find_all("a"):
        bookmarks.append({
            "title": a.string or "",
            "url": a.get("href", ""),
            "tags": extract_tags_from_folder(a.find_parents("dl"))
        })
    
    return bookmarks

def get_browser_bookmarks(browser_type):
    """获取浏览器书签"""
    # 这里需要根据操作系统和浏览器类型获取书签文件路径
    # Windows示例:
    if os.name == "nt":
        if browser_type == "chrome":
            path = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Bookmarks")
        elif browser_type == "edge":
            path = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Bookmarks")
        else:
            return []
        
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                bookmarks_json = json.load(f)
                return parse_browser_json(bookmarks_json)
    
    return []

def parse_browser_json(bookmarks_json):
    """解析浏览器书签JSON文件"""
    def traverse(node, folder_path=""):
        items = []
        if "children" in node:
            current_folder = node.get("name", "")
            new_path = f"{folder_path}/{current_folder}" if folder_path else current_folder
            for child in node["children"]:
                items.extend(traverse(child, new_path))
        elif "url" in node:
            tags = []
            if folder_path:
                tags.extend(folder_path.split("/"))
            if "tags" in node:
                tags.extend(node["tags"])
            items.append({
                "title": node.get("name", ""),
                "url": node["url"],
                "tags": list(set(tags))  # 去重
            })
        return items
    
    return traverse(bookmarks_json["roots"]["bookmark_bar"])

def extract_tags_from_folder(folder_elements):
    """从文件夹结构中提取标签"""
    tags = []
    for dl in folder_elements:
        h3 = dl.find_previous_sibling("h3")
        if h3:
            tags.append(h3.string)
    return list(set(tags))

def process_bookmarks(bookmarks, db):
    """处理书签数据，自动打标签和去重"""
    existing_urls = {b.url for b in db.query(BookmarkDB.url).all()}
    new_bookmarks = []
    duplicates = []
    all_tags = set()
    
    for bookmark in bookmarks:
        # 去重检查
        if bookmark["url"] in existing_urls:
            duplicates.append(bookmark)
            continue
        
        # 自动标签处理
        if not bookmark.get("tags"):
            bookmark["tags"] = []
        
        # 从URL提取标签
        domain = get_domain(bookmark["url"])
        if domain:
            bookmark["tags"].append(domain)
        
        # 从标题提取标签
        title_tags = extract_tags_from_text(bookmark["title"])
        bookmark["tags"].extend(title_tags)
        
        # 去重和清理标签
        bookmark["tags"] = list(set(tag.lower().strip() for tag in bookmark["tags"] if tag.strip()))
        
        all_tags.update(bookmark["tags"])
        new_bookmarks.append(bookmark)
    
    return {
        "new_bookmarks": new_bookmarks,
        "duplicates": duplicates,
        "tags_added": list(all_tags)
    }

def get_domain(url):
    """从URL提取域名作为标签"""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.split(".")[0]
    except:
        return None

def extract_tags_from_text(text):
    """从文本中提取可能的标签"""
    # 这里可以添加更复杂的自然语言处理逻辑
    common_tags = ["blog", "tutorial", "docs", "article", "news"]
    return [tag for tag in common_tags if tag in text.lower()]


# 前端服务路由
from fastapi.responses import FileResponse

@app.get("/", include_in_schema=False)
async def serve_frontend():
    """服务前端主页面"""
    return FileResponse("frontend/templates/index.html")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("frontend/static/favicon.ico")