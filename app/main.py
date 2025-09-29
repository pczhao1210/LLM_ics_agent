from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .api import upload, result, download
from .config import settings

app = FastAPI(
    title="🎫 票据识别转ICS服务",
    description="""
    🤖 智能票据识别服务，支持多种票据类型自动识别并生成ICS日历文件。
    
    ## 功能特性
    - ✈️ 支持机票、火车票、演唱会票等多种票据类型
    - 📅 自动生成Apple Calendar兼容的ICS文件
    - 🔄 异步处理，支持实时状态查询
    - 📊 完整的任务管理和文件存储
    
    ## 使用流程
    1. POST /upload - 上传票据图片
    2. GET /result/{folder_name} - 查询识别结果
    3. GET /ics/{folder_name} - 下载ICS日历文件
    4. GET /storage/{folder_name}/{file} - 访问静态文件
    
    ## Web界面
    访问 http://localhost:8501 使用可视化界面。
    """,
    version="1.0.0",
    contact={
        "name": "ICS Agent",
        "url": "http://localhost:8501",
    },
    license_info={
        "name": "MIT",
    },
)

# 挂载静态文件
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# 注册路由
app.include_router(upload.router, tags=["上传"])
app.include_router(result.router, tags=["结果"])
app.include_router(download.router, tags=["下载"])

@app.get("/", summary="服务信息", description="获取服务基本信息")
async def root():
    return {
        "service": "🎫 票据识别转ICS服务",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "智能票据识别",
            "ICS日历生成",
            "异步任务处理",
            "多类型票据支持"
        ],
        "endpoints": {
            "upload": "/upload",
            "result": "/result/{folder_name}",
            "download": "/ics/{folder_name}",
            "static": "/storage/{folder_name}/{file}",
            "docs": "/docs",
            "health": "/health"
        },
        "web_ui": "http://localhost:8501"
    }

@app.get("/health", summary="健康检查", description="检查服务运行状态")
async def health():
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "票据识别转ICS服务",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)