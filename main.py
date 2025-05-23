# PyWebView入口点
import webview
import uvicorn
import threading
from backend.api import app


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)

def create_window():
    # 创建PyWebView窗口
    window = webview.create_window(
        title='',
        url='http://127.0.0.1:8000/',
        width=900,
        height=600,
        resizable=True,
        fullscreen=False,
        # local_api=True,
    )
    return window


if __name__ == '__main__':
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    # 调用函数创建窗口，而不是直接调用 webview.start() 函数
    window = create_window()  
    webview.start(window, http_server=True, http_port=8080)