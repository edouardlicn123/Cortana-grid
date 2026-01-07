#!/bin/bash
# Cortana Grid 启动脚本（强化版 - 2026-01-07）
# 修复：删除 venv 后自动重新安装依赖 + 更强的 venv 有效性检测

set -e  # 脚本出错立即退出

# ==================== 可选参数处理 ====================
FORCE_REINSTALL=0
for arg in "$@"; do
    case $arg in
        --force-reinstall|-f)
            FORCE_REINSTALL=1
            shift
            ;;
        *)
            # 其他参数保留（未来扩展）
            ;;
    esac
done

if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))' 2>/dev/null || echo "fallback_key")
    echo "生成的 SECRET_KEY: $SECRET_KEY"
fi

# ==================== 颜色定义 ====================
RED='\033[0;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# ==================== 项目目录定位 ====================
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR"
PROJECT_DIR="$(pwd)"

echo -e "${GREEN}=== Cortana Grid 启动中（强化版）===${NC}"
echo -e "${BLUE}项目目录: $PROJECT_DIR${NC}"
echo -e "${BLUE}Python 版本: $(python3 --version 2>&1 || echo '未找到 python3')${NC}"

# ==================== 数据库类型选择（保持不变）===================
# ...（数据库选择部分完全保留原代码，不修改）...
echo -e "${YELLOW}请选择数据库类型：${NC}"
echo "1. SQLite (默认，适合开发/测试)"
echo "2. MySQL (适合生产环境)"
read -p "请输入选择 (1 或 2, 回车默认1): " db_choice
db_choice=${db_choice:-1}

if [ "$db_choice" = "2" ]; then
    export DATABASE_TYPE=mysql
    echo -e "${GREEN}已选择 MySQL 数据库${NC}"
    read -p "MySQL 主机 (默认 localhost): " mysql_host
    export MYSQL_HOST="${mysql_host:-localhost}"
    read -p "MySQL 端口 (默认 3306): " mysql_port
    export MYSQL_PORT="${mysql_port:-3306}"
    read -p "MySQL 用户名 (默认 root): " mysql_user
    export MYSQL_USER="${mysql_user:-root}"
    read -s -p "MySQL 密码 (输入后回车): " mysql_password
    echo ""
    export MYSQL_PASSWORD="$mysql_password"
    read -p "MySQL 数据库名 (默认 community_system): " mysql_db
    export MYSQL_DATABASE="${mysql_db:-community_system}"
else
    export DATABASE_TYPE=sqlite
    echo -e "${GREEN}已选择 SQLite 数据库${NC}"
fi

# ==================== 虚拟环境处理（核心强化）===================
VENV_DIR="$PROJECT_DIR/venv"
NEEDS_REINSTALL=0

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}未检测到虚拟环境目录，正在创建...${NC}"
    NEEDS_REINSTALL=1
else
    # 关键强化：检查 venv 是否有效（是否有 pip 可执行文件）
    if [ ! -f "$VENV_DIR/bin/pip" ] && [ ! -f "$VENV_DIR/Scripts/pip.exe" ]; then
        echo -e "${YELLOW}检测到虚拟环境损坏（缺少 pip），正在重新创建...${NC}"
        rm -rf "$VENV_DIR"
        NEEDS_REINSTALL=1
    fi
fi

if [ "$NEEDS_REINSTALL" = "1" ]; then
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR" || { echo -e "${RED}创建虚拟环境失败！请检查 python3-venv 是否安装${NC}"; exit 1; }
    echo -e "${GREEN}虚拟环境创建成功${NC}"
    # 新 venv 创建后，必须重装依赖
    rm -f .last_install  # 删除旧标记
fi

echo -e "${YELLOW}正在激活虚拟环境...${NC}"
source "$VENV_DIR/bin/activate" || { echo -e "${RED}虚拟环境激活失败！${NC}"; exit 1; }
echo -e "${GREEN}虚拟环境激活成功（$(python --version)）${NC}"

PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

# ==================== 依赖安装（强化判断逻辑）===================
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}错误：未找到 requirements.txt 文件！${NC}"
    exit 1
fi

# 强制重装 或 无标记 或 requirements 更新 或 新 venv
if [ "$FORCE_REINSTALL" = "1" ] || [ ! -f ".last_install" ] || [ requirements.txt -nt .last_install ] || [ "$NEEDS_REINSTALL" = "1" ]; then
    echo -e "${YELLOW}正在安装/更新项目依赖...${NC}"
    "$PIP" install --upgrade pip || echo -e "${YELLOW}pip 升级失败，继续尝试安装依赖${NC}"
    "$PIP" install -r requirements.txt || { echo -e "${RED}依赖安装失败！请检查网络或 requirements.txt${NC}"; exit 1; }
    touch .last_install
    echo -e "${GREEN}依赖安装完成${NC}"
else
    echo -e "${GREEN}依赖已安装且无更新，跳过安装${NC}"
fi

# ==================== MySQL 驱动（保持不变）===================
if [ "$DATABASE_TYPE" = "mysql" ]; then
    if ! "$PYTHON" -c "import mysql.connector" 2>/dev/null; then
        echo -e "${YELLOW}正在安装 MySQL 驱动...${NC}"
        "$PIP" install mysql-connector-python
    else
        echo -e "${GREEN}MySQL 驱动已安装${NC}"
    fi
fi

# ==================== 启动应用（保持不变）===================
echo -e "${GREEN}正在启动 Cortana Grid Web 服务...${NC}"
echo -e "${CYAN}访问地址：http://127.0.0.1:5000${NC}"
echo -e "${CYAN}按 Ctrl+C 停止服务${NC}"
echo "========================================"

exec "$PYTHON" app.py &

APP_PID=$!

# 等待启动 + 自动打开浏览器（保持原逻辑）
# ...（原脚本中等待和打开浏览器部分完全保留）...

for i in {1..30}; do
    if curl -s http://127.0.0.1:5000 >/dev/null 2>&1; then
        echo -e "${GREEN}服务已就绪！正在自动打开浏览器...${NC}"
        URL="http://127.0.0.1:5000"
        if command -v xdg-open >/dev/null 2>&1; then
            xdg-open "$URL"
        elif [[ "$(uname)" == "Darwin" ]]; then
            open "$URL"
        elif command -v powershell.exe >/dev/null 2>&1; then
            powershell.exe -Command "Start-Process '$URL'"
        elif "$PYTHON" -c "import webbrowser" 2>/dev/null; then
            "$PYTHON" -c "import webbrowser, time; time.sleep(0.5); webbrowser.open_new_tab('$URL')"
        else
            echo -e "${YELLOW}无法自动打开浏览器，请手动访问：$URL${NC}"
        fi
        break
    fi
    sleep 0.5
done

if ! curl -s http://127.0.0.1:5000 >/dev/null 2>&1; then
    echo -e "${RED}警告：服务启动超时，请检查端口或 app.py${NC}"
fi

wait $APP_PID

echo -e "${CYAN}Cortana Grid 已停止，Good job, Chief。${NC}"
deactivate 2>/dev/null || true
