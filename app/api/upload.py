from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.async_processor import async_processor
from ..models.response import UploadResponse

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_ticket(file: UploadFile = File(...)):
    """上传票据图片进行识别"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只支持图片文件")
    
    content = await file.read()
    folder_name = await async_processor.submit_task(file.filename, content)
    
    return UploadResponse(id=folder_name, status="processing")