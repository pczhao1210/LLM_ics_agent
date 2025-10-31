import asyncio
import uuid
from typing import Dict, Any

from .vision import vision_service
from .ics import ics_service
from .storage import storage_service
from .image_processor import image_processor

class AsyncProcessor:
    def __init__(self):
        pass
    
    async def _run_pipeline(self, folder_name: str, image_content: bytes, persist_status: bool) -> Dict[str, Any]:
        """执行票据识别流水线，可选持久化状态"""
        if persist_status:
            await storage_service.save_task_status(folder_name, "processing")
        
        try:
            processed_image = image_processor.process_image(image_content)
            result = await vision_service.extract_ticket_info(processed_image)
            
            if "error" in result:
                error_msg = result["error"]
                if persist_status:
                    await storage_service.save_task_status(folder_name, "failed", {"error": error_msg})
                return {
                    "id": folder_name,
                    "status": "failed",
                    "error": error_msg
                }
            
            result["id"] = folder_name
            
            if persist_status:
                await storage_service.save_result(folder_name, result)
            
            ics_content = ics_service.generate_ics(result)
            await storage_service.save_ics(folder_name, ics_content)
            
            if persist_status:
                await storage_service.save_task_status(folder_name, "completed", result)
            
            return {
                "id": folder_name,
                "status": "completed",
                "data": result,
                "ics_url": f"/ics/{folder_name}"
            }
        
        except Exception as e:
            error_msg = str(e)
            if persist_status:
                await storage_service.save_task_status(folder_name, "failed", {"error": error_msg})
            return {
                "id": folder_name,
                "status": "failed",
                "error": error_msg
            }
    
    async def process_ticket(self, folder_name: str, image_content: bytes) -> None:
        """异步处理票据识别"""
        await self._run_pipeline(folder_name, image_content, persist_status=True)
    
    async def process_ticket_sync(self, filename: str, image_content: bytes) -> Dict[str, Any]:
        """同步处理票据识别并返回最终结果"""
        folder_name = await storage_service.save_image(str(uuid.uuid4()), filename, image_content)
        return await self._run_pipeline(folder_name, image_content, persist_status=False)
    
    async def submit_task(self, filename: str, image_content: bytes) -> str:
        """提交处理任务"""
        task_id = str(uuid.uuid4())
        
        # 保存图片并创建文件夹
        folder_name = await storage_service.save_image(task_id, filename, image_content)
        
        # 创建异步任务
        asyncio.create_task(self.process_ticket(folder_name, image_content))
        
        return folder_name
    
    async def get_task_result(self, folder_name: str) -> Dict[str, Any]:
        """获取任务结果"""
        return await storage_service.get_task_status(folder_name)

async_processor = AsyncProcessor()
