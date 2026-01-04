#!/bin/bash
# Cortana Grid 启动脚本（最终优化版 - 完美支持含空格目录 + 双引号保护变量 + 调试日志）

set -e  # 脚本出错立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目根目录 - 修复含空格路径问题
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" || { echo -e "${RED}无法进入项目目录${NC}"; exit 1; }
cd "$SCRIPT_DIR" || exit 1
PROJECT_DIR="$(pwd)"
echo -e "${GREEN}=== Cortana Grid 启动中 ===${NC}"
echo "当前工作目录: $PROJECT_DIR"
echo "Python 版本: $(python3 --version 2>&1 || echo '未找到 python3')"

# ==================== 数据库类型选择 ====================
echo -e "${YELLOW}请选择数据库类型：${NC}"
echo "1. SQLite (默认，适合开发/测试)"
echo "2. MySQL (适合生产环境)"
read -p "请输入选择 (1 或 2, 回车默认1): " db_choice

db_choice=${db_choice:-1}

if [ "$db_choice" = "2" ]; then
    export DATABASE_TYPE=mysql
    echo -e "${GREEN}已选择 MySQL${NC}"
    
    read -p "MySQL 主机 (默认 localhost): " mysql_host
    export MYSQL_HOST="${mysql_host:-localhost}"
    
    read -p "MySQL 端口 (默认 3306): " mysql_port
    export MYSQL_PORT="${mysql_port:-3306}"
    
    read -p "MySQL 用户名 (默认 root): " mysql_user
    export MYSQL_USER="${mysql_user:-root}"
    
    read -s -p "MySQL 密码: " mysql_password
    echo ""
    export MYSQL_PASSWORD="$mysql_password"
    
    read -p "MySQL 数据库名 (默认 community_system): " mysql_db
    export MYSQL_DATABASE="${mysql_db:-community_system}"
else
    export DATABASE_TYPE=sqlite
    echo -e "${GREEN}已选择 SQLite${NC}"
fi

# ==================== 虚拟环境处理 ====================
VENV_DIR="$PROJECT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}未检测到虚拟环境，正在创建...${NC}"
    python3 -m venv "$VENV_DIR" || { echo -e "${RED}创建虚拟环境失败${NC}"; exit 1; }
    echo -e "${GREEN}虚拟环境创建成功${NC}"
fi

# 激活虚拟环境
echo -e "${YELLOW}正在激活虚拟环境...${NC}"
source "$VENV_DIR/bin/activate" || { echo -e "${RED}虚拟环境激活失败${NC}"; exit 1; }
echo -e "${GREEN}虚拟环境激活成功（$(python --version)）${NC}"

# 强制使用虚拟环境中的 python 和 pip（双引号保护空格）
PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

# ==================== 依赖安装 ====================
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}错误：未找到 requirements.txt 文件！${NC}"
    exit 1
fi

if [ "$FORCE_REINSTALL" = "1" ]; then
    echo -e "${YELLOW}强制重新安装依赖...${NC}"
    "$PIP" install --upgrade pip
    "$PIP" install -r requirements.txt
    touch .last_install 2>/dev/null || true
else
    # 检查是否已安装 Flask（代表性依赖）
    if "$PIP" show flask > /dev/null 2>&1 && [ ! requirements.txt -nt .last_install ]; then
        echo -e "${GREEN}依赖已安装且无更新，跳过安装${NC}"
    else
        echo -e "${YELLOW}正在安装/更新依赖...${NC}"
        "$PIP" install --upgrade pip
        "$PIP" install -r requirements.txt
        touch .last_install 2>/dev/null || true
    fi
fi

# ==================== MySQL 专用依赖 ====================
if [ "$DATABASE_TYPE" = "mysql" ]; then
    if ! "$PYTHON" -c "import mysql.connector" &> /dev/null; then
        echo -e "${YELLOW}安装 MySQL 驱动...${NC}"
        "$PIP" install mysql-connector-python
    fi
fi

# ==================== 启动应用 ====================
echo -e "${GREEN}正在启动 Cortana Grid...${NC}"
echo -e "${GREEN}访问地址：http://127.0.0.1:5000${NC}"
echo -e "${GREEN}按 Ctrl+C 停止服务${NC}"
echo "========================================"

# 使用虚拟环境中的 python 启动（双引号保护）
"$PYTHON" "$PROJECT_DIR/app.py" &

APP_PID=$!

# 等待启动
echo -e "${YELLOW}等待服务启动...${NC}"
for i in {1..15}; do
    if curl -s http://127.0.0.1:5000 > /dev/null 2>&1; then
        echo -e "${GREEN}服务已就绪！${NC}"
        break
    fi
    sleep 1
done

# ==================== 打开浏览器 ====================
if [ "$NO_BROWSER" != "1" ]; then
    URL="http://127.0.0.1:5000"
    echo -e "${CYAN}正在打开浏览器访问 Cortana Grid...${NC}"

    if command -v xdg-open > /dev/null; then
        xdg-open "$URL"
    elif command -v gnome-open > /dev/null; then
        gnome-open "$URL"
    elif command -v open > /dev/null; then
        open "$URL"
    elif command -v start > /dev/null; then
        start "" "$URL"
    else
        echo -e "${YELLOW}未检测到支持的浏览器打开命令，请手动访问：$URL${NC}"
    fi
else
    echo -e "${YELLOW}已跳过自动打开浏览器，请手动访问：http://127.0.0.1:5000${NC}"
fi

# 等待用户 Ctrl+C
wait $APP_PID

echo ""
echo -e "${CYAN}Cortana Grid 已停止，Good job, Chief。${NC}"
deactivate 2>/dev/null || true
