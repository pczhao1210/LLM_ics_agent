from PIL import Image, ImageOps
import cv2
import numpy as np
from io import BytesIO
from ..config import settings

class ImageProcessor:
    def process_image(self, image_content: bytes) -> bytes:
        """处理图片：调整大小、旋转、去噪等"""
        # 使用PIL打开图片
        image = Image.open(BytesIO(image_content))
        
        # 自动旋转（根据EXIF信息）
        if settings.image_auto_rotate:
            image = ImageOps.exif_transpose(image)
        
        # 转换为RGB模式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 调整尺寸（如果启用resize）
        if settings.image_resize:
            max_width = settings.image_max_width
            max_height = settings.image_max_height
            
            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # 去噪处理（可选）
        if settings.image_denoise:
            image = self._denoise_image(image)
        
        # 保存为字节流
        output = BytesIO()
        image.save(output, format='JPEG', quality=settings.image_quality, optimize=True)
        return output.getvalue()
    
    def _denoise_image(self, pil_image: Image.Image) -> Image.Image:
        """使用OpenCV进行去噪处理"""
        # PIL转OpenCV
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # 高斯模糊去噪
        denoised = cv2.GaussianBlur(cv_image, (3, 3), 0)
        
        # OpenCV转PIL
        rgb_image = cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_image)

image_processor = ImageProcessor()