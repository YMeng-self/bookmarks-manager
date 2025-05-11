# FastAPI主应用


from fastapi import FastAPI, HTTPException
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from typing import List, Optional
from .models import Bookmark, BookmarkCreate, BookmarkUpdate
import datetime
import uuid


app = FastAPI(title="Bookmarks Manager API", version="1.0.0")

# 挂载前端静态文件 (PyWebView将使用这些文件)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# 临时数据存储 (实际项目中替换为数据库)
bookmarks_db = []

@app.get("/api/bookmarks", response_model=List[Bookmark], tags=["书签管理"])
async def get_all_bookmarks():
    """获取所有书签列表"""
    return bookmarks_db

@app.post("/api/bookmarks/import", tags=["书签管理"])
async def import_bookmarks(file: UploadFile = File(...)):
    """导入书签（JSON格式文件）"""
    ...

@app.get("/api/bookmarks/export", response_class=FileResponse, tags=["书签管理"])
async def export_bookmarks():
    """导出所有书签（JSON格式文件）"""
    ...

# 新增搜索API
@app.get("/api/bookmarks/search", response_model=List[Bookmark], tags=["书签管理"])
async def search_bookmarks(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    tag: Optional[str] = Query(None, description="按标签过滤"),
    limit: int = Query(10, description="返回结果数量限制")
):
    """
    搜索书签
    - 支持关键词搜索和标签过滤
    - 支持结果数量限制
    """
    ...



# 前端服务路由
from fastapi.responses import FileResponse

@app.get("/", include_in_schema=False)
async def serve_frontend():
    """服务前端主页面"""
    return FileResponse("frontend/templates/index.html")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("frontend/static/favicon.ico")