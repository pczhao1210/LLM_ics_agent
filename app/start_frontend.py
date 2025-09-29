#!/usr/bin/env python3
import subprocess
import sys
import json
from pathlib import Path

def load_config():
    config_path = Path("config/config.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

if __name__ == "__main__":
    config = load_config()
    
    # 从配置文件获取前端设置
    frontend_config = config.get("frontend", {})
    port = str(frontend_config.get("port", 8501))
    host = frontend_config.get("host", "0.0.0.0")
    
    # 启动Streamlit前端
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "app/frontend.py",
        "--server.port", port,
        "--server.address", host,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ])