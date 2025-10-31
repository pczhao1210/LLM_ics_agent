from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from .api import upload, result, download
from .config import settings
from .api.dependencies import verify_api_token

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
    1. POST /process - 一步上传并获取ICS下载链接
    2. POST /upload - 上传票据图片开启异步识别
    3. GET /result/{folder_name} - 查询异步识别结果
    4. GET /ics/{folder_name} - 下载ICS日历文件
    5. GET /storage/{folder_name}/{file} - 访问静态文件
    
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

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """保护静态文件等需要认证的路径。"""
    protected_prefixes = ("/storage",)
    if settings.api_token and request.url.path.startswith(protected_prefixes):
        try:
            await verify_api_token(
                authorization=request.headers.get("Authorization"),
                token=request.query_params.get("token")
            )
        except Exception as exc:  # 捕获HTTPException等
            if hasattr(exc, "status_code"):
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": getattr(exc, "detail", "Unauthorized")},
                    headers=getattr(exc, "headers", None) or {}
                )
            raise
    return await call_next(request)

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
            "process": "/process",
            "upload": "/upload",
            "result": "/result/{folder_name}",
            "download": "/ics/{folder_name}",
            "static": "/storage/{folder_name}/{file}",
            "docs": "/docs",
            "health": "/health"
        },
        "auth": {
            "streamlit": bool(settings.streamlit_credentials.get("username")),
            "api_token_required": bool(settings.api_token)
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
