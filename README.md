# 票据识别转ICS服务

🎫 将票据截图自动识别并生成ICS日历文件，支持Apple Calendar导入的智能服务。

## ✨ 功能特性

- 🤖 **智能识别** - 支持机票、火车票、演唱会票、剧场票等多种票据类型
- 📅 **ICS生成** - 自动生成Apple Calendar兼容的日历文件
- 🔄 **异步处理** - 后台异步处理，不阻塞用户操作
- 🎨 **Web界面** - 直观的Streamlit前端界面
- ⚙️ **可配置** - 支持OpenAI模型、图片处理等参数配置
- 📊 **任务管理** - 完整的任务历史记录和文件管理
- 🔐 **访问控制** - 支持Streamlit登录与API令牌双重认证
- 🔗 **文件访问** - 支持在线查看图片、JSON结果和下载ICS文件

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <repository>
cd ics_agent

# 创建虚拟环境
python3 -m venv .venv

# 安装依赖
.venv/bin/pip install -r requirements.txt
```

### 2. 配置设置
```bash
# 复制配置文件
cp config/config.sample.json config/config.json

# 编辑配置文件，设置OpenAI API Key
vim config/config.json

# 或者使用环境变量
export OPENAI_API_KEY="your_api_key_here"
```

### 3. 启动服务
```bash
# 一键启动（推荐）
./start.sh

# 调试模式
./start.sh --debug

# 查看帮助
./start.sh --help
```

### 4. 访问服务
- 🌐 **前端界面**: http://localhost:8501
- 📚 **API文档**: http://localhost:8000/docs
- ❤️ **健康检查**: http://localhost:8000/health
- 🔑 **登录认证**: 首次访问前端需使用 `config.json` 或环境变量中配置的凭证登录；调用API需携带令牌

## 🐳 Docker部署

```bash
# 构建镜像
docker build -t ics-agent .

# 运行容器
docker run -d \
  -p 8000:8000 \
  -p 8501:8501 \
  -e OPENAI_API_KEY="your_api_key" \
  -e STREAMLIT_USERNAME="your_username" \
  -e STREAMLIT_PASSWORD="your_password" \
  -e API_AUTH_TOKEN="your_api_token" \
  -v $(pwd)/storage:/app/storage \
  --name ics-agent \
  ics-agent
```

- `storage` 目录挂载到主机以持久化识别结果
- `STREAMLIT_USERNAME` / `STREAMLIT_PASSWORD` 控制前端登录，`API_AUTH_TOKEN` 用于保护API访问
- 可根据需要添加 `OPENAI_BASE_URL` 等额外环境变量

## 🎯 使用方法

### Web界面使用
1. 打开前端界面 http://localhost:8501
2. 上传票据截图（支持JPG、PNG格式）
3. 点击"开始识别"按钮
4. 等待处理完成，查看识别结果
5. 下载生成的ICS文件导入日历

### 配置管理
- 在侧边栏"配置"标签页中修改系统设置
- 支持OpenAI模型选择、图片处理参数等
- 配置修改后需重启服务生效

### 任务管理
- 查看当前处理中的任务
- 浏览历史任务记录
- 在线查看图片、JSON结果
- 下载ICS文件或删除任务

## 🔧 手动启动

如果需要分别启动服务：

```bash
# 启动后端API服务
.venv/bin/python run.py

# 启动前端界面（新终端）
.venv/bin/python app/start_frontend.py
```

## 📡 API接口

> 默认情况下，所有API（含静态文件）均需要携带 `Authorization: Bearer <token>` 头部，
> 或者在URL后追加 `?token=<token>` 进行访问。

### 上传票据
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@ticket.jpg"
```

**响应示例:**
```json
{
  "id": "2025_01_15_14_30_25_ticket_image",
  "status": "processing"
}
```

### 一步同步上传并生成ICS
```bash
curl -X POST "http://localhost:8000/process" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@ticket.jpg"
```

**响应示例:**
```json
{
  "id": "2025_01_15_14_30_25_ticket_image",
  "status": "completed",
  "data": { "... 识别结果 ..." },
  "ics_url": "/ics/2025_01_15_14_30_25_ticket_image"
}
```

### 查询结果
```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/result/{folder_name}"
```

**响应示例:**
```json
{
  "id": "2025_01_15_14_30_25_ticket_image",
  "status": "completed",
  "data": {
    "type": "flight",
    "title": "CZ6798 重庆江北(T3) → 南宁吴圩(T2)",
    "start": {
      "datetime": "2025-06-10T21:46:00",
      "timezone": "Asia/Shanghai"
    },
    "end": {
      "datetime": "2025-06-10T23:04:00",
      "timezone": "Asia/Shanghai"
    },
    "location": {
      "name": "重庆江北国际机场 (T3)",
      "address": null
    },
    "details": {
      "seat": null,
      "gate": "G12",
      "reference": null
    },
    "confidence": 0.88
  },
  "ics_url": "/ics/2025_01_15_14_30_25_ticket_image"
}
```

### 下载ICS文件
```bash
curl -H "Authorization: Bearer <token>" "http://localhost:8000/ics/{folder_name}" -o calendar.ics
```

### 访问静态文件
```bash
# 查看原始图片
curl -H "Authorization: Bearer <token>" "http://localhost:8000/storage/{folder_name}/original.jpg"

# 查看JSON结果
curl -H "Authorization: Bearer <token>" "http://localhost:8000/storage/{folder_name}/result.json"
```

## 📁 存储结构
```
storage/
└── 2025_01_15_14_30_25_ticket_image/
    ├── original.jpg      # 原始上传图片
    ├── status.json       # 任务处理状态
    ├── result.json       # 识别结果数据
    └── calendar.ics      # 生成的ICS日历文件
```

## ⚙️ 配置说明

配置文件位于 `config/config.json`，可从 `config/config.sample.json` 复制并修改。支持以下配置项：

### OpenAI设置
```json
{
  "openai": {
    "api_key": "your_api_key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4-vision-preview",
    "max_tokens": 1000,
    "available_models": ["gpt-4o", "gpt-4o-mini"]
  }
}
```

### 图片处理
```json
{
  "image_processing": {
    "resize": true,
    "max_width": 1024,
    "max_height": 1024,
    "quality": 85,
    "auto_rotate": true
  }
}
```

### 提醒设置
```json
{
  "ics": {
    "reminder_hours": {
      "flight": 2,
      "train": 1,
      "concert": 1
    }
  }
}
```

## 🔐 安全与认证

- **Streamlit前端登录**
  - 配置项：`config.auth.streamlit.username` / `password`
  - 环境变量：`STREAMLIT_USERNAME` / `STREAMLIT_PASSWORD`（当配置文件未设置时使用）
  - 未配置凭证时，前端会提示认证已关闭
- **API令牌认证**
  - 配置项：`config.auth.api.token`
  - 环境变量：`API_AUTH_TOKEN`（当配置文件未设置时使用）
  - 可通过 `Authorization: Bearer <token>` 或 `?token=<token>` 访问受保护接口
- 建议在公网部署时始终设置上述凭证，并使用HTTPS或反向代理进一步保护流量

## 🎫 支持的票据类型

- ✈️ **机票** - 自动识别航班信息、起降时间、座位号等
- 🚄 **火车票** - 识别车次、出发到达时间、座位信息
- 🎵 **演唱会票** - 提取演出信息、时间、场馆地址
- 🎭 **剧场票** - 识别演出剧目、时间、剧场信息
- 📋 **其他票据** - 通用票据信息提取

## 🛠️ 开发说明

### 项目结构
```
ics_agent/
├── app/                  # 应用主目录
│   ├── api/             # API路由
│   ├── models/          # 数据模型
│   ├── services/        # 核心服务
│   ├── config.py        # 配置管理
│   ├── frontend.py      # Streamlit前端
│   ├── main.py          # FastAPI应用
│   └── start_frontend.py # 前端启动脚本
├── config/              # 配置文件
│   ├── config.json      # 主配置文件
│   └── config.sample.json # 配置示例
├── storage/             # 数据存储(自动创建)
├── start.sh             # 一键启动脚本
├── run.py               # 后端启动脚本
└── requirements.txt     # 依赖包
```

### 技术栈
- **后端**: FastAPI + Python 3.11
- **前端**: Streamlit
- **AI模型**: OpenAI GPT-4 Vision
- **图片处理**: Pillow + OpenCV
- **日历生成**: icalendar
- **异步处理**: asyncio + ThreadPoolExecutor

## 🔍 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 检查端口占用
   lsof -i :8000
   lsof -i :8501
   
   # 清理进程
   ./start.sh  # 脚本会自动清理
   ```

2. **识别失败**
   - 检查OpenAI API Key是否正确
   - 确认网络连接正常
   - 查看调试日志：`./start.sh --debug`

3. **文件无法访问**
   - 确认storage目录权限
   - 检查静态文件服务是否正常

### 日志查看
```bash
# 调试模式启动
./start.sh --debug

# 查看任务状态
cat storage/{folder_name}/status.json
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！
