from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from ..services.async_processor import async_processor
from ..models.response import UploadResponse, ProcessResponse
from .dependencies import verify_api_token

router = APIRouter(dependencies=[Depends(verify_api_token)])

@router.post("/upload", response_model=UploadResponse)
async def upload_ticket(file: UploadFile = File(...)):
    """上传票据图片进行识别"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只支持图片文件")
    
    content = await file.read()
    folder_name = await async_processor.submit_task(file.filename, content)
    
    return UploadResponse(id=folder_name, status="processing")

@router.post("/process", response_model=ProcessResponse)
async def process_ticket(file: UploadFile = File(...)):
    """上传票据图片并同步返回识别结果"""
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只支持图片文件")
    
    content = await file.read()
    result = await async_processor.process_ticket_sync(file.filename, content)
    
    if result["status"] == "completed":
        return ProcessResponse(
            id=result["id"],
            status=result["status"],
            data=result.get("data"),
            ics_url=result.get("ics_url")
        )
    
    if result["status"] == "failed":
        return ProcessResponse(
            id=result["id"],
            status=result["status"],
            error=result.get("error", "处理失败")
        )
    
    # 默认返回当前状态（例如处理超时仍处于processing）
    return ProcessResponse(
        id=result["id"],
        status=result["status"]
    )
