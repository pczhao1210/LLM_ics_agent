import airportsdata
from timezonefinder import TimezoneFinder

class TimezoneService:
    def __init__(self):
        self.airports = airportsdata.load('IATA')
        self.tf = TimezoneFinder()
    
    def get_timezone_by_airport(self, iata_code: str) -> str:
        """根据机场IATA代码获取时区"""
        airport = self.airports.get(iata_code.upper())
        if airport:
            lat, lon = airport['lat'], airport['lon']
            return self.tf.timezone_at(lat=lat, lng=lon)
        return None
    
    def get_timezone_by_city(self, city_name: str, country: str = None) -> str:
        """根据城市名获取时区（需要地理编码，这里简化处理）"""
        # 简化的城市时区映射
        city_timezone_map = {
            '北京': 'Asia/Shanghai',
            '上海': 'Asia/Shanghai',
            '广州': 'Asia/Shanghai',
            '深圳': 'Asia/Shanghai',
            '香港': 'Asia/Hong_Kong',
            '台北': 'Asia/Taipei',
            '东京': 'Asia/Tokyo',
            '首尔': 'Asia/Seoul',
            '新加坡': 'Asia/Singapore',
            '纽约': 'America/New_York',
            '洛杉矶': 'America/Los_Angeles',
            '伦敦': 'Europe/London',
            '巴黎': 'Europe/Paris',
            '悉尼': 'Australia/Sydney',
        }
        
        return city_timezone_map.get(city_name, 'Asia/Shanghai')

timezone_service = TimezoneService()