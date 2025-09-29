from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from ..services.storage import storage_service

router = APIRouter()

@router.get("/ics/{folder_name}")
async def download_ics(folder_name: str):
    """下载ICS文件"""
    ics_path = storage_service.get_ics_path(folder_name)
    
    if not ics_path.exists():
        raise HTTPException(status_code=404, detail="ICS文件不存在")
    
    return FileResponse(
        path=str(ics_path),
        filename="calendar.ics",
        media_type="text/calendar"
    )