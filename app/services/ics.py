from icalendar import Calendar, Event, Alarm
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import uuid

class ICSService:
    def generate_ics(self, data: dict) -> bytes:
        """生成ICS文件内容"""
        cal = Calendar()
        cal.add('prodid', '-//Ticket2Calendar//EN')
        cal.add('version', '2.0')
        
        event = Event()
        event.add('uid', data.get('id', str(uuid.uuid4())))
        event.add('dtstamp', datetime.now(timezone.utc))
        event.add('summary', data['title'])
        
        # 处理开始时间
        start_dt = datetime.fromisoformat(data['start']['datetime']).replace(
            tzinfo=ZoneInfo(data['start']['timezone'])
        )
        event.add('dtstart', start_dt)
        
        # 处理结束时间
        if data.get('end'):
            end_dt = datetime.fromisoformat(data['end']['datetime']).replace(
                tzinfo=ZoneInfo(data['end']['timezone'])
            )
            event.add('dtend', end_dt)
        
        # 添加地点
        location_name = data['location']['name']
        if data['location'].get('address'):
            location_name += f", {data['location']['address']}"
        event.add('location', location_name)
        
        # 添加描述
        desc_parts = []
        details = data.get('details', {})
        for key, value in details.items():
            if value:
                desc_parts.append(f"{key}: {value}")
        
        if desc_parts:
            event.add('description', "\n".join(desc_parts))
        
        # 添加提醒
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', f"提醒: {data['title']}")
        
        # 根据配置设置提醒时间
        from ..config import settings
        reminder_hours = settings.get_reminder_hours(data['type'])
        trigger_time = timedelta(hours=-reminder_hours)
        
        alarm.add('trigger', trigger_time)
        event.add_component(alarm)
        
        cal.add_component(event)
        return cal.to_ical()

ics_service = ICSService()