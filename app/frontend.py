import streamlit as st
import requests
import time
import json
import pandas as pd
from pathlib import Path

# 页面配置
st.set_page_config(
    page_title="票据识别转ICS",
    page_icon="🎫",
    layout="wide"
)

st.title("🎫 票据识别转ICS服务")
st.markdown("上传票据截图，自动识别并生成ICS日历文件")

# 动态获取API端口配置
def get_api_base():
    config = load_config()
    api_port = config.get("api", {}).get("port", 8000)
    return f"http://localhost:{api_port}"

API_BASE = get_api_base()

# 加载配置文件
@st.cache_data
def load_config():
    config_path = Path("config/config.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config_data):
    config_path = Path("config/config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)
    st.cache_data.clear()  # 清除缓存以重新加载

# 获取任务列表
@st.cache_data(ttl=5)  # 5秒缓存
def get_task_list():
    storage_path = Path("storage")
    tasks = []
    if storage_path.exists():
        for folder in storage_path.iterdir():
            if folder.is_dir():
                status_file = folder / "status.json"
                if status_file.exists():
                    try:
                        with open(status_file, 'r', encoding='utf-8') as f:
                            status_data = json.load(f)
                        
                        # 提取文件名（从文件夹名中）
                        folder_parts = folder.name.split('_')
                        if len(folder_parts) >= 6:
                            filename = '_'.join(folder_parts[6:])
                        else:
                            filename = "unknown"
                        
                        task_info = {
                            "folder": folder.name,
                            "filename": filename,
                            "status": status_data.get("status", "unknown"),
                            "timestamp": status_data.get("timestamp", ""),
                            "has_image": (folder / "original.jpg").exists(),
                            "has_result": (folder / "result.json").exists(),
                            "has_ics": (folder / "calendar.ics").exists()
                        }
                        tasks.append(task_info)
                    except:
                        continue
    
    # 按时间戳排序（最新的在前）
    tasks.sort(key=lambda x: x["timestamp"], reverse=True)
    return tasks

tasks = get_task_list()

# 当前处理中的任务
processing_tasks = [t for t in tasks if t["status"] == "processing"]
if processing_tasks:
    st.markdown("### 🔄 处理中的任务")
    for task in processing_tasks:
        with st.expander(f"📄 {task['filename']} - {task['status']}", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                if task["has_image"]:
                    st.markdown(f"[🖼️ 查看图片]({API_BASE}/storage/{task['folder']}/original.jpg)")
            with col2:
                st.text(f"状态: {task['status']}")
            with col3:
                st.text(f"时间: {task['timestamp'][:19]}")

# 文件上传
st.subheader("📤 上传新票据")
uploaded_file = st.file_uploader(
    "选择票据图片",
    type=['jpg', 'jpeg', 'png'],
    help="支持JPG、PNG格式的票据截图"
)

if uploaded_file:
    # 显示上传的图片
    st.image(uploaded_file, caption="上传的票据", width=400)
    
    if st.button("开始识别", type="primary"):
        with st.spinner("正在处理..."):
            # 上传文件
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            response = requests.post(f"{API_BASE}/upload", files=files)
            
            if response.status_code == 200:
                result = response.json()
                folder_name = result["id"]
                st.success(f"上传成功！任务ID: {folder_name}")
                
                # 轮询结果
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(30):  # 最多等待30秒
                    time.sleep(1)
                    progress_bar.progress((i + 1) / 30)
                    
                    # 查询状态
                    status_response = requests.get(f"{API_BASE}/result/{folder_name}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status_text.text(f"状态: {status_data['status']}")
                        
                        if status_data["status"] == "completed":
                            st.success("识别完成！")
                            
                            # 显示识别结果
                            if status_data.get("data"):
                                st.subheader("识别结果")
                                st.json(status_data["data"])
                                
                                # 下载按钮
                                ics_url = f"{API_BASE}/ics/{folder_name}"
                                st.markdown(f"[📅 下载ICS文件]({ics_url})")
                            break
                        elif status_data["status"] == "failed":
                            st.error(f"识别失败: {status_data.get('error', '未知错误')}")
                            break
                else:
                    st.warning("处理超时，请稍后查询结果")
            else:
                st.error("上传失败，请检查服务是否正常运行")

st.markdown("---")

# 历史任务表格
if tasks:
    st.markdown("### 📊 历史任务")
    
    # 表头
    col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 2, 1, 1, 1, 1])
    with col1:
        st.markdown("**文件名**")
    with col2:
        st.markdown("**状态**")
    with col3:
        st.markdown("**时间**")
    with col4:
        st.markdown("**图片**")
    with col5:
        st.markdown("**JSON**")
    with col6:
        st.markdown("**ICS**")
    with col7:
        st.markdown("**操作**")
    
    st.divider()
    
    for i, task in enumerate(tasks):
        with st.container():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 2, 1, 1, 1, 1])
            
            with col1:
                st.text(task["filename"])
            
            with col2:
                status_emoji = {
                    "completed": "✅",
                    "processing": "🔄", 
                    "failed": "❌"
                }.get(task["status"], "❓")
                st.text(f"{status_emoji} {task['status']}")
            
            with col3:
                st.text(task["timestamp"][:19] if task["timestamp"] else "")
            
            with col4:
                if task["has_image"]:
                    st.link_button("🖼️", f"{API_BASE}/storage/{task['folder']}/original.jpg")
            
            with col5:
                if task["has_result"]:
                    st.link_button("📄", f"{API_BASE}/storage/{task['folder']}/result.json")
            
            with col6:
                if task["has_ics"]:
                    st.link_button("📅", f"{API_BASE}/ics/{task['folder']}")
            
            with col7:
                if st.button("🗑️", key=f"delete_{task['folder']}", help="删除任务"):
                    # 删除文件夹
                    import shutil
                    folder_path = Path("storage") / task['folder']
                    if folder_path.exists():
                        shutil.rmtree(folder_path)
                        st.success(f"已删除任务: {task['filename']}")
                        st.cache_data.clear()
                        st.rerun()
            
            if i < len(tasks) - 1:
                st.divider()
else:
    st.info("暂无任务记录")

# 侧边栏 - 配置信息
with st.sidebar:
    tab1, tab2 = st.tabs(["状态", "配置"])
    
    with tab1:
        st.header("⚙️ 服务状态")
        
        # 健康检查
        try:
            health_response = requests.get(f"{API_BASE}/health", timeout=2)
            if health_response.status_code == 200:
                st.success("✅ 服务正常")
            else:
                st.error("❌ 服务异常")
        except:
            st.error("❌ 无法连接服务")
        
        st.markdown("---")
        st.markdown("### 支持的票据类型")
        st.markdown("- 🛫 机票")
        st.markdown("- 🚄 火车票")
        st.markdown("- 🎵 演唱会票")
        st.markdown("- 🎭 剧场票")
        st.markdown("- 📋 其他票据")
        
        st.markdown("---")
        st.markdown("### API文档")
        st.markdown(f"[📖 查看API文档]({API_BASE}/docs)")
    
    with tab2:
        st.header("🔧 系统配置")
        
        config = load_config()
        
        # OpenAI配置
        st.subheader("OpenAI设置")
        openai_config = config.get("openai", {})
        
        api_key = st.text_input(
            "API Key", 
            value=openai_config.get("api_key", ""),
            type="password",
            help="OpenAI API密钥"
        )
        
        base_url = st.text_input(
            "Base URL", 
            value=openai_config.get("base_url", "https://api.openai.com/v1"),
            help="API基础URL"
        )
        
        available_models = openai_config.get("available_models", ["gpt-4-vision-preview", "gpt-4o", "gpt-4o-mini"])
        current_model = openai_config.get("model", "gpt-4-vision-preview")
        model_index = available_models.index(current_model) if current_model in available_models else 0
        
        model = st.selectbox(
            "模型",
            available_models,
            index=model_index
        )
        
        # 图片处理配置
        st.subheader("图片处理")
        img_config = config.get("image_processing", {})
        
        resize = st.checkbox(
            "启用图片缩放", 
            value=img_config.get("resize", True),
            help="是否将图片缩放到指定尺寸"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            max_width = st.number_input(
                "最大宽度", 
                min_value=512, max_value=2048, 
                value=img_config.get("max_width", 1024),
                disabled=not resize
            )
        with col2:
            max_height = st.number_input(
                "最大高度", 
                min_value=512, max_value=2048, 
                value=img_config.get("max_height", 1024),
                disabled=not resize
            )
        
        quality = st.slider(
            "JPEG质量", 
            min_value=50, max_value=100, 
            value=img_config.get("quality", 85),
            help="图片压缩质量，越高质量越好但文件越大"
        )
        
        auto_rotate = st.checkbox(
            "自动旋转", 
            value=img_config.get("auto_rotate", True),
            help="根据EXIF信息自动纠正图片方向"
        )
        
        # ICS提醒配置
        st.subheader("提醒设置")
        ics_config = config.get("ics", {}).get("reminder_hours", {})
        
        flight_hours = st.number_input(
            "航班提醒(小时)", 
            min_value=0, max_value=24, 
            value=ics_config.get("flight", 2)
        )
        
        train_hours = st.number_input(
            "火车提醒(小时)", 
            min_value=0, max_value=24, 
            value=ics_config.get("train", 1)
        )
        
        concert_hours = st.number_input(
            "演出提醒(小时)", 
            min_value=0, max_value=24, 
            value=ics_config.get("concert", 1)
        )
        
        # 保存按钮
        if st.button("💾 保存配置", type="primary"):
            # 更新配置
            new_config = config.copy()
            
            new_config["openai"] = {
                "api_key": api_key,
                "base_url": base_url,
                "model": model,
                "max_tokens": openai_config.get("max_tokens", 1000),
                "available_models": openai_config.get("available_models", ["gpt-4-vision-preview", "gpt-4o", "gpt-4o-mini"])
            }
            
            new_config["image_processing"] = {
                "resize": resize,
                "max_width": max_width,
                "max_height": max_height,
                "quality": quality,
                "format": "JPEG",
                "auto_rotate": auto_rotate,
                "denoise": img_config.get("denoise", False)
            }
            
            new_config["ics"] = {
                "reminder_hours": {
                    "flight": flight_hours,
                    "train": train_hours,
                    "concert": concert_hours,
                    "theater": ics_config.get("theater", 1),
                    "generic": ics_config.get("generic", 1)
                }
            }
            
            try:
                save_config(new_config)
                st.success("✅ 配置已保存！")
                st.info("⚠️ 修改config.json中的api.port后重启服务生效")
            except Exception as e:
                st.error(f"❌ 保存失败: {str(e)}")

# 页脚
st.markdown("---")
st.markdown("💡 **使用提示**: 上传清晰的票据截图，系统会自动识别时间、地点等信息并生成ICS日历文件")