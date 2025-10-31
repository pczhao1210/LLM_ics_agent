import os
import json
import time
from pathlib import Path
from typing import Any, Dict, Tuple

import requests
import streamlit as st

# 页面配置
st.set_page_config(
    page_title="票据识别转ICS",
    page_icon="🎫",
    layout="wide"
)


@st.cache_data
def load_config() -> Dict[str, Any]:
    config_path = Path("config/config.json")
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config_data: Dict[str, Any]) -> None:
    config_path = Path("config/config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)
    st.cache_data.clear()  # 清除缓存以重新加载


def get_api_base() -> str:
    config = load_config()
    host = config.get("api", {}).get("host", "http://localhost")
    port = config.get("api", {}).get("port", 8000)
    if not host.startswith(("http://", "https://")):
        host = f"http://{host}"
    hostname = host.split("://", 1)[1]
    if ":" in hostname:
        return host.rstrip("/")
    return f"{host.rstrip('/')}:{port}"


def get_streamlit_credentials() -> Tuple[str | None, str | None]:
    config = load_config()
    auth_config = config.get("auth", {}).get("streamlit", {})
    username = auth_config.get("username") or os.getenv("STREAMLIT_USERNAME")
    password = auth_config.get("password") or os.getenv("STREAMLIT_PASSWORD")
    return username, password


def get_api_token() -> str | None:
    config = load_config()
    token = config.get("auth", {}).get("api", {}).get("token")
    return token or os.getenv("API_AUTH_TOKEN")


def add_auth_token(url: str, token: str | None) -> str:
    if not token:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}token={token}"


def ensure_authenticated() -> None:
    username, password = get_streamlit_credentials()
    if not username or not password:
        st.warning("未配置Streamlit登录凭证，认证已暂时关闭。请在config.json或环境变量中设置。")
        return
    
    if st.session_state.get("streamlit_auth"):
        return
    
    st.title("🎫 票据识别转ICS服务")
    st.markdown("请先登录后再使用系统。")
    
    with st.form("login_form"):
        input_user = st.text_input("用户名")
        input_password = st.text_input("密码", type="password")
        submitted = st.form_submit_button("登录")
        if submitted:
            if input_user == username and input_password == password:
                st.session_state["streamlit_auth"] = True
                st.success("登录成功，正在刷新界面...")
                st.experimental_rerun()
            else:
                st.error("用户名或密码错误，请重试。")
    
    st.stop()


# 强制认证
ensure_authenticated()

# 缓存配置相关数据
API_BASE = get_api_base()
API_TOKEN = get_api_token()
API_HEADERS = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}

st.title("🎫 票据识别转ICS服务")
st.markdown("上传票据截图，自动识别并生成ICS日历文件")

if not API_TOKEN:
    st.warning("⚠️ 未配置API认证令牌。若后端已启用认证，请在config.json或环境变量中设置 API_AUTH_TOKEN。")


# 获取任务列表
@st.cache_data(ttl=5)  # 5秒缓存
def get_task_list() -> list[Dict[str, Any]]:
    storage_path = Path("storage")
    tasks = []
    if storage_path.exists():
        for folder in storage_path.iterdir():
            if not folder.is_dir():
                continue
            
            status_file = folder / "status.json"
            status_data: Dict[str, Any] = {}
            if status_file.exists():
                try:
                    with open(status_file, "r", encoding="utf-8") as f:
                        status_data = json.load(f)
                except Exception:
                    status_data = {}
            else:
                if (folder / "calendar.ics").exists():
                    status_data = {"status": "completed"}
            
            folder_parts = folder.name.split("_")
            filename = "_".join(folder_parts[6:]) if len(folder_parts) >= 7 else folder.name
            
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
                    image_url = add_auth_token(f"{API_BASE}/storage/{task['folder']}/original.jpg", API_TOKEN)
                    st.markdown(f"[🖼️ 查看图片]({image_url})")
            with col2:
                st.text(f"状态: {task['status']}")
            with col3:
                st.text(f"时间: {task['timestamp'][:19]}")

# 文件上传
st.subheader("📤 上传新票据")
uploaded_file = st.file_uploader(
    "选择票据图片",
    type=["jpg", "jpeg", "png"],
    help="支持JPG、PNG格式的票据截图"
)

if uploaded_file:
    st.image(uploaded_file, caption="上传的票据", width=400)
    
    if st.button("开始识别", type="primary"):
        with st.spinner("正在处理..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            response = requests.post(f"{API_BASE}/upload", files=files, headers=API_HEADERS)
            
            if response.status_code == 401:
                st.error("认证失败：请检查API认证令牌配置。")
            elif response.status_code != 200:
                st.error(f"上传失败: {response.text}")
            else:
                result = response.json()
                folder_name = result["id"]
                st.success(f"上传成功！任务ID: {folder_name}")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(30):
                    time.sleep(1)
                    progress_bar.progress((i + 1) / 30)
                    
                    status_response = requests.get(
                        f"{API_BASE}/result/{folder_name}",
                        headers=API_HEADERS
                    )
                    if status_response.status_code == 401:
                        st.error("认证失败：请检查API认证令牌配置。")
                        break
                    if status_response.status_code != 200:
                        status_text.text(f"状态查询失败: {status_response.text}")
                        continue
                    
                    status_data = status_response.json()
                    status_text.text(f"状态: {status_data['status']}")
                    
                    if status_data["status"] == "completed":
                        st.success("识别完成！")
                        if status_data.get("data"):
                            st.subheader("识别结果")
                            st.json(status_data["data"])
                            
                            ics_url = add_auth_token(f"{API_BASE}/ics/{folder_name}", API_TOKEN)
                            st.markdown(f"[📅 下载ICS文件]({ics_url})")
                        break
                    if status_data["status"] == "failed":
                        st.error(f"识别失败: {status_data.get('error', '未知错误')}")
                        break
                else:
                    st.warning("处理超时，请稍后在历史任务中查看结果。")

st.markdown("---")

# 历史任务表格
if tasks:
    st.markdown("### 📊 历史任务")
    
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
                    image_url = add_auth_token(f"{API_BASE}/storage/{task['folder']}/original.jpg", API_TOKEN)
                    st.link_button("🖼️", image_url)
            
            with col5:
                if task["has_result"]:
                    json_url = add_auth_token(f"{API_BASE}/storage/{task['folder']}/result.json", API_TOKEN)
                    st.link_button("📄", json_url)
            
            with col6:
                if task["has_ics"]:
                    ics_url = add_auth_token(f"{API_BASE}/ics/{task['folder']}", API_TOKEN)
                    st.link_button("📅", ics_url)
            
            with col7:
                if st.button("🗑️", key=f"delete_{task['folder']}", help="删除任务"):
                    import shutil
                    folder_path = Path("storage") / task["folder"]
                    if folder_path.exists():
                        shutil.rmtree(folder_path)
                        st.success(f"已删除任务: {task['filename']}")
                        st.cache_data.clear()
                        st.experimental_rerun()
            
            if i < len(tasks) - 1:
                st.divider()
else:
    st.info("暂无任务记录")

# 侧边栏 - 配置信息
with st.sidebar:
    tab1, tab2 = st.tabs(["状态", "配置"])
    
    with tab1:
        st.header("⚙️ 服务状态")
        
        try:
            health_response = requests.get(f"{API_BASE}/health", headers=API_HEADERS, timeout=2)
            if health_response.status_code == 200:
                st.success("✅ 服务正常")
            elif health_response.status_code == 401:
                st.error("❌ 认证失败，无法访问健康检查")
            else:
                st.error("❌ 服务异常")
        except Exception:
            st.error("❌ 无法连接服务")
        
        st.markdown("---")
        st.markdown("### 当前认证状态")
        if st.session_state.get("streamlit_auth"):
            if st.button("退出登录"):
                st.session_state["streamlit_auth"] = False
                st.experimental_rerun()
        st.markdown(f"- Streamlit 登录: {'已启用' if get_streamlit_credentials()[0] else '未启用'}")
        st.markdown(f"- API Token: {'已配置' if API_TOKEN else '未配置'}")
        
        st.markdown("---")
        st.markdown("### 支持的票据类型")
        st.markdown("- 🛫 机票")
        st.markdown("- 🚄 火车票")
        st.markdown("- 🎵 演唱会票")
        st.markdown("- 🎭 剧场票")
        st.markdown("- 📋 其他票据")
        
        st.markdown("---")
        st.markdown("### API文档")
        docs_url = add_auth_token(f"{API_BASE}/docs", API_TOKEN)
        st.markdown(f"[📖 查看API文档]({docs_url})")
    
    with tab2:
        st.header("🔧 系统配置")
        
        config = load_config()
        
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
        
        st.subheader("认证配置")
        auth_config = config.get("auth", {})
        streamlit_auth = auth_config.get("streamlit", {})
        api_auth = auth_config.get("api", {})
        
        streamlit_username = st.text_input(
            "Streamlit用户名",
            value=streamlit_auth.get("username", ""),
            help="可通过环境变量 STREAMLIT_USERNAME 覆盖"
        )
        streamlit_password = st.text_input(
            "Streamlit密码",
            value=streamlit_auth.get("password", ""),
            type="password",
            help="可通过环境变量 STREAMLIT_PASSWORD 覆盖"
        )
        api_token_value = st.text_input(
            "API Token",
            value=api_auth.get("token", ""),
            type="password",
            help="访问受保护API时使用，可通过环境变量 API_AUTH_TOKEN 覆盖"
        )
        
        st.caption("提示：使用环境变量设置凭证时，界面中的值仅用于占位显示。")
        
        if st.button("💾 保存配置", type="primary"):
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
            
            new_config["auth"] = {
                "streamlit": {
                    "username": streamlit_username,
                    "password": streamlit_password
                },
                "api": {
                    "token": api_token_value
                }
            }
            
            try:
                save_config(new_config)
                st.success("✅ 配置已保存！")
                st.info("⚠️ 修改端口或认证信息后请重启服务以生效。")
            except Exception as e:
                st.error(f"❌ 保存失败: {str(e)}")

st.markdown("---")
st.markdown("💡 **使用提示**: 上传清晰的票据截图，系统会自动识别时间、地点等信息并生成ICS日历文件。")
