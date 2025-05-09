import json
import os
from pathlib import Path
import uuid
from typing import Dict, List, Optional

class BookmarkParser:
    def __init__(self):
        self.browser_paths = {
            "chrome": Path(os.getenv('LOCALAPPDATA')) / 'Google/Chrome/User Data/Default/Bookmarks',
            "edge": Path(os.getenv('LOCALAPPDATA')) / 'Microsoft/Edge/User Data/Default/Bookmarks'
        }

    def get_browser_bookmarks(self, browser_type: str) -> Dict:
        """获取指定浏览器的书签数据"""
        if browser_type not in self.browser_paths:
            raise ValueError(f"不支持的浏览器类型: {browser_type}")
        
        path = self.browser_paths[browser_type]
        if not path.exists():
            raise FileNotFoundError(f"未找到{browser_type}的书签文件")
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def parse_bookmarks(self, bookmark_data: Dict, browser_type: str, parent_id: Optional[int] = None) -> List[Dict]:
        """递归解析书签树形结构"""
        results = []
        
        def process_node(node: Dict, parent: Optional[int] = None):
            if node['type'] == 'folder':
                # 处理文件夹
                folder = {
                    'id': str(uuid.uuid4()),
                    'type': 'folder',
                    'name': node['name'],
                    'browser_type': browser_type,
                    'parent_id': parent,
                    'children': []
                }
                
                # 递归处理子节点
                for child in node.get('children', []):
                    child_result = process_node(child, folder['id'])
                    if isinstance(child_result, dict):
                        folder['children'].append(child_result)
                    else:
                        results.append(child_result)
                
                return folder
            else:
                # 处理书签
                bookmark = {
                    'id': str(uuid.uuid4()),
                    'type': 'url',
                    'title': node['name'],
                    'url': node['url'],
                    'browser_type': browser_type,
                    'parent_id': parent,
                    'tags': [],
                    'position': len(results)
                }
                results.append(bookmark)
                return bookmark

        # 处理根节点
        for node in bookmark_data['roots']['bookmark_bar']['children']:
            result = process_node(node, parent_id)
            if result:
                results.append(result)

        return results

    def export_to_browser(self, browser_type: str, bookmarks: List[Dict]) -> None:
        """将书签数据导出到浏览器"""
        if browser_type not in self.browser_paths:
            raise ValueError(f"不支持的浏览器类型: {browser_type}")
        
        path = self.browser_paths[browser_type]
        
        def reconstruct_tree(bookmarks: List[Dict]) -> Dict:
            """重建书签树结构"""
            tree = {
                "roots": {
                    "bookmark_bar": {
                        "children": [],
                        "name": "书签栏",
                        "type": "folder"
                    },
                    "other": {
                        "children": [],
                        "name": "其他书签",
                        "type": "folder"
                    },
                    "synced": {
                        "children": [],
                        "name": "移动设备书签",
                        "type": "folder"
                    }
                },
                "version": 1
            }
            
            # 重建书签树
            for bookmark in bookmarks:
                if bookmark['type'] == 'folder':
                    node = {
                        "name": bookmark['name'],
                        "type": "folder",
                        "children": []
                    }
                    # 处理子节点
                    for child in bookmark.get('children', []):
                        if child['type'] == 'folder':
                            node['children'].append(reconstruct_tree([child])['roots']['bookmark_bar']['children'][0])
                        else:
                            node['children'].append({
                                "name": child['title'],
                                "type": "url",
                                "url": child['url']
                            })
                    tree['roots']['bookmark_bar']['children'].append(node)
                else:
                    tree['roots']['bookmark_bar']['children'].append({
                        "name": bookmark['title'],
                        "type": "url",
                        "url": bookmark['url']
                    })
            
            return tree

        # 导出书签文件
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(reconstruct_tree(bookmarks), f, indent=4, ensure_ascii=False) 