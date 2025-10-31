from fastapi import APIRouter, HTTPException, Depends
from ..services.async_processor import async_processor
from ..models.response import ResultResponse
from .dependencies import verify_api_token

router = APIRouter(dependencies=[Depends(verify_api_token)])

@router.get("/result/{folder_name}", response_model=ResultResponse)
async def get_result(folder_name: str):
    """获取识别结果"""
    result = await async_processor.get_task_result(folder_name)
    
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="任务不存在")
    
    response = ResultResponse(
        id=folder_name,
        status=result["status"]
    )
    
    if result["status"] == "completed" and result.get("data"):
        response.data = result["data"]
        response.ics_url = f"/ics/{folder_name}"
    elif result["status"] == "failed":
        response.error = result.get("data", {}).get("error", "处理失败")
    
    return response
