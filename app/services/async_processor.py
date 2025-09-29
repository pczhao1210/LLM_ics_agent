import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any
from datetime import datetime

from .vision import vision_service
from .ics import ics_service
from .storage import storage_service
from .image_processor import image_processor
from ..config import settings

class AsyncProcessor:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=settings.max_workers)
        self.tasks: Dict[str, Any] = {}
    
    async def process_ticket(self, folder_name: str, image_content: bytes) -> None:
        """异步处理票据识别"""
        try:
            # 更新状态为处理中
            await storage_service.save_task_status(folder_name, "processing")
            
            # 图片预处理
            processed_image = image_processor.process_image(image_content)
            
            # 执行视觉识别
            result = await vision_service.extract_ticket_info(processed_image)
            
            if "error" in result:
                await storage_service.save_task_status(folder_name, "failed", {"error": result["error"]})
                return
            
            # 添加ID
            result["id"] = folder_name
            
            # 保存识别结果
            await storage_service.save_result(folder_name, result)
            
            # 生成ICS文件
            ics_content = ics_service.generate_ics(result)
            await storage_service.save_ics(folder_name, ics_content)
            
            # 更新状态为完成
            await storage_service.save_task_status(folder_name, "completed", result)
            
        except Exception as e:
            await storage_service.save_task_status(folder_name, "failed", {"error": str(e)})
    
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