# 书签管理器 (Bookmarks Manager)

一个功能强大的跨浏览器书签管理工具，支持书签导入、导出、分类和同步。

## 主要功能

- 支持 Chrome/Edge 浏览器书签导入导出
- 可视化书签管理界面
- 标签系统支持
- 跨浏览器同步
- 桌面应用体验

## 技术栈

- 前端：Html + JS
- 后端：FastAPI
- 数据库：SQLite
- 桌面化：PyWebview

## 开发环境设置

1. 安装 Python 依赖：
```bash
pip install -r requirements.txt
```

2. 启动开发服务器：
```bash
# 后端
uvicorn backend.main:app --reload

# 前端
python main.py
```

## 使用说明

1. 首次运行时，程序会自动检测并导入浏览器书签
2. 支持拖拽操作管理书签
3. 可以为书签添加标签进行分类
4. 支持导出书签到浏览器

## 注意事项

- 操作书签文件前请确保浏览器已关闭
- 建议定期备份书签数据
- 首次使用时会自动创建数据备份 