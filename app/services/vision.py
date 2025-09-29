import base64
from openai import OpenAI
from ..config import settings

class VisionService:
    def __init__(self):
        self.client = None
    
    def _get_client(self):
        if self.client is None:
            try:
                self.client = OpenAI(
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url
                )
            except TypeError:
                # 兼容旧版本OpenAI客户端
                import openai
                openai.api_key = settings.openai_api_key
                openai.api_base = settings.openai_base_url
                self.client = openai
        return self.client
    
    def encode_image(self, image_content: bytes) -> str:
        """将图片编码为base64"""
        return base64.b64encode(image_content).decode('utf-8')
    
    async def extract_ticket_info(self, image_content: bytes) -> dict:
        """从票据图片中提取信息"""
        base64_image = self.encode_image(image_content)
        
        prompt = """
        请分析这张票据图片，提取以下信息并以JSON格式返回：
        
        {
          "type": "flight|train|concert|theater|generic",
          "title": "事件标题",
          "start": {
            "datetime": "2025-01-01T10:00:00",
            "timezone": "Asia/Shanghai"
          },
          "end": {
            "datetime": "2025-01-01T12:00:00",
            "timezone": "Asia/Shanghai"
          },
          "location": {
            "name": "场馆名称",
            "address": "详细地址"
          },
          "details": {
            "seat": "座位信息",
            "gate": "登机口/入口",
            "reference": "订单号/PNR"
          },
          "confidence": 0.9
        }
        
        注意：
        1. 根据票据类型识别type字段
        2. 时间格式必须是ISO 8601格式
        3. 时区根据地点推断，中国使用Asia/Shanghai
        4. 如果信息不明确，对应字段设为null
        5. confidence表示识别置信度(0-1)
        6. 只返回JSON，不要其他文字
        """
        
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            result = response.choices[0].message.content
            # 尝试解析JSON
            import json
            return json.loads(result)
            
        except Exception as e:
            return {
                "error": str(e),
                "confidence": 0.0
            }

vision_service = VisionService()