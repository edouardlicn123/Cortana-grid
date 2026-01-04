#!/bin/bash
# Cortana Grid 启动脚本（最终完美版 - 支持含空格路径 + 健壮错误处理 + 生产就绪）

set -e  # 脚本出错立即退出（关键安全）

# ==================== 颜色定义 ====================
RED='\033[0;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# ==================== 项目目录定位（完美支持含空格路径） ====================
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR"
PROJECT_DIR="$(pwd)"

echo -e "${GREEN}=== Cortana Grid 启动中 ===${NC}"
echo -e "${BLUE}项目目录: $PROJECT_DIR${NC}"
echo -e "${BLUE}Python 版本: $(python3 --version 2>&1 || echo '未找到 python3')${NC}"

# ==================== 数据库类型选择 ====================
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
    echo ""  # 换行
    export MYSQL_PASSWORD="$mysql_password"
    
    read -p "MySQL 数据库名 (默认 community_system): " mysql_db
    export MYSQL_DATABASE="${mysql_db:-community_system}"
else
    export DATABASE_TYPE=sqlite
    echo -e "${GREEN}已选择 SQLite 数据库${NC}"
fi

# ==================== 虚拟环境处理 ====================
VENV_DIR="$PROJECT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}未检测到虚拟环境，正在创建...${NC}"
    python3 -m venv "$VENV_DIR" || { echo -e "${RED}创建虚拟环境失败！${NC}"; exit 1; }
    echo -e "${GREEN}虚拟环境创建成功${NC}"
fi

echo -e "${YELLOW}正在激活虚拟环境...${NC}"
source "$VENV_DIR/bin/activate" || { echo -e "${RED}虚拟环境激活失败！${NC}"; exit 1; }
echo -e "${GREEN}虚拟环境激活成功（$(python --version)）${NC}"

PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

# ==================== 依赖安装 ====================
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}错误：未找到 requirements.txt 文件！${NC}"
    exit 1
fi

# 检查是否需要重新安装依赖（requirements.txt 更新了 或 强制标志）
if [ "$FORCE_REINSTALL" = "1" ] || [ ! -f ".last_install" ] || [ requirements.txt -nt .last_install ]; then
    echo -e "${YELLOW}正在安装/更新项目依赖...${NC}"
    "$PIP" install --upgrade pip
    "$PIP" install -r requirements.txt
    touch .last_install
else
    echo -e "${GREEN}依赖已安装且无更新，跳过安装${NC}"
fi

# ==================== MySQL 专用驱动 ====================
if [ "$DATABASE_TYPE" = "mysql" ]; then
    if ! "$PYTHON" -c "import mysql.connector" 2>/dev/null; then
        echo -e "${YELLOW}正在安装 MySQL 驱动...${NC}"
        "$PIP" install mysql-connector-python
    else
        echo -e "${GREEN}MySQL 驱动已安装${NC}"
    fi
fi

# ==================== 清理缓存 ====================
echo -e "${YELLOW}正在清理缓存...${NC}"
"$PYTHON" clear_cache.py -f || echo -e "${YELLOW}警告：clear_cache.py 执行失败（可能不存在）${NC}"

# ==================== 启动应用 ====================
echo -e "${GREEN}正在启动 Cortana Grid Web 服务...${NC}"
echo -e "${CYAN}访问地址：http://127.0.0.1:5000${NC}"
echo -e "${CYAN}按 Ctrl+C 停止服务${NC}"
echo "========================================"

# 前台运行（推荐开发模式，便于看到日志和 Ctrl+C 停止）
exec "$PYTHON" app.py
