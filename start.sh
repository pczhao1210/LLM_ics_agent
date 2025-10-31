#!/bin/bash

# 票据识别转ICS服务启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$SCRIPT_DIR/.venv/bin/python"
PID_FILE="$SCRIPT_DIR/.pids"

# 默认参数
DEBUG=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            DEBUG=true
            shift
            ;;
        -h|--help)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --debug    启用调试模式，显示详细日志"
            echo "  -h, --help 显示此帮助信息"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 -h 或 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 检查Python虚拟环境
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ 错误: 未找到Python虚拟环境 ($PYTHON_PATH)"
    echo "请先运行: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# 检查OpenAI API Key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  警告: 未设置OPENAI_API_KEY环境变量"
    echo "请运行: export OPENAI_API_KEY='your_api_key_here'"
fi

# 检查端口占用
check_port() {
    local port=$1
    local pids
    pids=$(lsof -Pi :$port -sTCP:LISTEN -t 2>/dev/null)
    if [ -n "$pids" ]; then
        echo "⚠️  端口 $port 当前有进程占用: $pids"
        echo "   如非本脚本启动的服务，请手动处理后再运行。"
    fi
}

# 清理残留进程
cleanup_processes() {
    echo "🧹 检查并清理残留进程..."
    
    # 获取端口配置
    local api_port=8000
    local frontend_port=8501
    if [ -f "config/config.json" ]; then
        api_port=$(python3 -c "import json; print(json.load(open('config/config.json')).get('api', {}).get('port', 8000))" 2>/dev/null || echo 8000)
        frontend_port=$(python3 -c "import json; print(json.load(open('config/config.json')).get('frontend', {}).get('port', 8501))" 2>/dev/null || echo 8501)
    fi
    
    # 根据PID文件优雅终止进程
    for pid_file in "$PID_FILE" "$SCRIPT_DIR/backend.pid" "$SCRIPT_DIR/frontend.pid"; do
        if [ -f "$pid_file" ]; then
            while read -r pid; do
                if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                    kill "$pid" 2>/dev/null
                    sleep 1
                    if kill -0 "$pid" 2>/dev/null; then
                        kill -9 "$pid" 2>/dev/null
                    fi
                    echo "  已终止进程: $pid"
                fi
            done < "$pid_file"
            rm -f "$pid_file"
        fi
    done
    
    # 最终提示端口状态
    check_port $api_port
    check_port $frontend_port
    
    sleep 1
}

# 退出时清理
trap 'echo ""; echo "🛑 正在关闭服务..."; cleanup_processes; echo "✅ 服务已关闭"; exit 0' INT TERM

# 启动前清理
cleanup_processes

echo "🚀 启动票据识别转ICS服务..."
echo "📁 工作目录: $SCRIPT_DIR"

# 设置日志级别
if [ "$DEBUG" = true ]; then
    LOG_LEVEL="--log-level debug"
    STREAMLIT_LOG="--logger.level debug"
    echo "🐛 调试模式已启用"
else
    LOG_LEVEL="--log-level info"
    STREAMLIT_LOG="--logger.level info"
fi

# 加载端口配置
API_PORT=8000
FRONTEND_PORT=8501
if [ -f "config/config.json" ]; then
    API_PORT=$(python3 -c "import json; print(json.load(open('config/config.json')).get('api', {}).get('port', 8000))" 2>/dev/null || echo 8000)
    FRONTEND_PORT=$(python3 -c "import json; print(json.load(open('config/config.json')).get('frontend', {}).get('port', 8501))" 2>/dev/null || echo 8501)
fi

# 启动后端服务
echo "🔧 启动后端服务 (端口 $API_PORT)..."
if [ "$DEBUG" = true ]; then
    "$PYTHON_PATH" run.py &
else
    "$PYTHON_PATH" run.py > /dev/null 2>&1 &
fi
BACKEND_PID=$!
echo $BACKEND_PID >> "$PID_FILE"
echo $BACKEND_PID > "$SCRIPT_DIR/backend.pid"

# 等待后端启动
echo "  等待后端服务启动..."
for i in {1..10}; do
    if kill -0 $BACKEND_PID 2>/dev/null && lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  ✅ 后端服务启动成功 (PID: $BACKEND_PID)"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ 后端服务启动失败或端口未监听"
        if [ "$DEBUG" = true ]; then
            echo "调试信息: 进程状态和端口检查"
            ps aux | grep run.py | grep -v grep || echo "未找到run.py进程"
            lsof -Pi :$API_PORT || echo "端口$API_PORT未被监听"
        fi
        cleanup_processes
        exit 1
    fi
    sleep 1
done

# 启动前端服务
echo "🎨 启动前端界面 (端口 $FRONTEND_PORT)..."
if [ "$DEBUG" = true ]; then
    "$PYTHON_PATH" -m streamlit run app/frontend.py --server.port $FRONTEND_PORT --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false $STREAMLIT_LOG &
else
    "$PYTHON_PATH" -m streamlit run app/frontend.py --server.port $FRONTEND_PORT --server.address 0.0.0.0 --server.headless true --browser.gatherUsageStats false $STREAMLIT_LOG > /dev/null 2>&1 &
fi
FRONTEND_PID=$!
echo $FRONTEND_PID >> "$PID_FILE"
echo $FRONTEND_PID > "$SCRIPT_DIR/frontend.pid"

# 等待前端启动
echo "  等待前端服务启动..."
for i in {1..10}; do
    if kill -0 $FRONTEND_PID 2>/dev/null && lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  ✅ 前端服务启动成功 (PID: $FRONTEND_PID)"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ 前端服务启动失败或端口未监听"
        if [ "$DEBUG" = true ]; then
            echo "调试信息: 进程状态和端口检查"
            ps aux | grep streamlit | grep -v grep || echo "未找到streamlit进程"
            lsof -Pi :$FRONTEND_PORT || echo "端口$FRONTEND_PORT未被监听"
        fi
        cleanup_processes
        exit 1
    fi
    sleep 1
done

echo ""
echo "✅ 服务启动成功!"
echo "🌐 前端界面: http://localhost:$FRONTEND_PORT"
echo "📚 API文档:  http://localhost:$API_PORT/docs"
echo ""
echo "按 Ctrl+C 退出服务"

# 保持脚本运行
wait
