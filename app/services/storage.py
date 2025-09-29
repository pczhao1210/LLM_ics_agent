import os
import json
import aiofiles
from pathlib import Path
from datetime import datetime
from ..config import settings

class StorageService:
    def __init__(self):
        self.base_path = Path(settings.storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _create_task_folder(self, filename: str) -> str:
        """创建任务文件夹：yyyy_mm_dd_hh_mm_ss_filename"""
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        # 清理文件名，移除扩展名和特殊字符
        clean_name = Path(filename).stem.replace(" ", "_").replace("-", "_")
        folder_name = f"{timestamp}_{clean_name}"
        folder_path = self.base_path / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_name
    
    async def save_image(self, task_id: str, filename: str, file_content: bytes) -> str:
        """保存上传的图片"""
        folder_name = self._create_task_folder(filename)
        file_path = self.base_path / folder_name / "original.jpg"
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        return folder_name
    
    async def save_result(self, folder_name: str, data: dict) -> str:
        """保存识别结果JSON"""
        file_path = self.base_path / folder_name / "result.json"
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
        return str(file_path)
    
    async def load_result(self, folder_name: str) -> dict:
        """加载识别结果"""
        file_path = self.base_path / folder_name / "result.json"
        if not file_path.exists():
            return None
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content)
    
    async def save_task_status(self, folder_name: str, status: str, data: dict = None) -> str:
        """保存任务状态"""
        task_data = {
            "folder": folder_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        file_path = self.base_path / folder_name / "status.json"
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(task_data, ensure_ascii=False, indent=2))
        return str(file_path)
    
    async def get_task_status(self, folder_name: str) -> dict:
        """获取任务状态"""
        file_path = self.base_path / folder_name / "status.json"
        if not file_path.exists():
            return {"status": "not_found"}
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            return json.loads(content)
    
    async def save_ics(self, folder_name: str, ics_content: bytes) -> str:
        """保存ICS文件"""
        file_path = self.base_path / folder_name / "calendar.ics"
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(ics_content)
        return str(file_path)
    
    def get_ics_path(self, folder_name: str) -> Path:
        """获取ICS文件路径"""
        return self.base_path / folder_name / "calendar.ics"

storage_service = StorageService()