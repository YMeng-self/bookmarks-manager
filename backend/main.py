# FastAPI主应用


from fastapi import FastAPI, HTTPException
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


# 前端服务路由
from fastapi.responses import FileResponse

@app.get("/", include_in_schema=False)
async def serve_frontend():
    """服务前端主页面"""
    return FileResponse("frontend/templates/index.html")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("frontend/static/favicon.ico")