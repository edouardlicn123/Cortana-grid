#!/usr/bin/env bash
# Cortana Grid 启动脚本（升级版 - 2026-02-09）
# 功能：
#   1. 先激活虚拟环境
#   2. 菜单：
#      1. 启动系统 (运行 app.py)
#      2. 生成代码包 (运行 code2ai.py)
#      3. 清理缓存 (clear_cache.py --force)
#      4. 安装/更新依赖
#      5. 初始化数据库（清空数据 + 双重确认 + 自动备份）
#      0. 退出
#   3. 所有操作必须输入数字并按回车确认，无超时自动执行

set -e

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

# ==================== 虚拟环境处理 ====================
VENV_DIR="$PROJECT_DIR/venv"
PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

NEEDS_REINSTALL=0
FORCE_REINSTALL=0

# 处理命令行参数
for arg in "$@"; do
    case "$arg" in
        --force-reinstall|-f)
            FORCE_REINSTALL=1
            ;;
    esac
done

# 创建或修复虚拟环境
if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/pip" ]; then
    echo -e "${YELLOW}正在创建/修复虚拟环境...${NC}"
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR" || {
        echo -e "${RED}创建虚拟环境失败！请确保已安装 python3-venv${NC}"
        exit 1
    }
    NEEDS_REINSTALL=1
fi

# 激活虚拟环境（最先执行）
echo -e "${YELLOW}激活虚拟环境...${NC}"
source "$VENV_DIR/bin/activate" 2>/dev/null || {
    echo -e "${RED}虚拟环境激活失败！${NC}"
    exit 1
}
echo -e "${GREEN}虚拟环境已激活（$(python --version)）${NC}"

# ==================== SECRET_KEY 处理 ====================
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))' 2>/dev/null || echo "fallback_key_very_insecure")
    export SECRET_KEY
    echo -e "${CYAN}已生成 SECRET_KEY：${SECRET_KEY}${NC}"
fi

# ==================== 依赖安装函数 ====================
install_dependencies() {
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}错误：缺少 requirements.txt 文件！${NC}"
        return 1
    fi

    echo -e "${YELLOW}正在安装/更新依赖...${NC}"
    echo -e "${YELLOW}→ 升级 pip ...${NC}"
    "$PIP" install --upgrade pip || {
        echo -e "${YELLOW}pip 升级失败，继续尝试安装依赖${NC}"
    }

    echo -e "${YELLOW}→ 安装 requirements.txt 中的包 ...${NC}"
    "$PIP" install -r requirements.txt || {
        echo -e "${RED}依赖安装失败！请检查网络或 requirements.txt 内容${NC}"
        return 1
    }

    touch .last_install
    echo -e "${GREEN}依赖安装/更新完成${NC}"
    return 0
}

# 启动时自动检查并安装依赖（可通过菜单选项4再次手动执行）
if [ "$FORCE_REINSTALL" = "1" ] || [ "$NEEDS_REINSTALL" = "1" ] || [ ! -f ".last_install" ] || [ "requirements.txt" -nt ".last_install" ]; then
    install_dependencies
else
    echo -e "${GREEN}依赖已是最新，跳过自动安装${NC}"
fi

# ==================== 清理缓存函数 ====================
run_clear_cache() {
    if [ -f "clear_cache.py" ]; then
        echo -e "${GREEN}执行缓存清理（强制模式）...${NC}"
        "$PYTHON" clear_cache.py --force
        echo -e "${GREEN}清理完成${NC}"
    else
        echo -e "${RED}错误：未找到 clear_cache.py 文件！${NC}"
    fi
}

# ==================== 初始化数据库函数 ====================
init_database() {
    local db_file="$PROJECT_DIR/instance/community_system.sqlite"
    local backup_file="$PROJECT_DIR/instance/community_system.sqlite.bak.$(date +%Y%m%d_%H%M%S)"

    # 第一重确认
    echo -e "${YELLOW}警告：初始化数据库将清空现有数据！${NC}"
    if [ -f "$db_file" ]; then
        echo -e "${YELLOW}检测到已存在的数据库文件：$db_file${NC}"
        echo -e "${YELLOW}是否继续初始化？（输入 yes 并按回车确认，否则输入任意内容取消）${NC}"
        read -r confirm1
        if [ "$confirm1" != "yes" ]; then
            echo -e "${CYAN}操作已取消。${NC}"
            return 0
        fi
    else
        echo -e "${YELLOW}未找到数据库文件，将创建新数据库。${NC}"
        echo -e "${YELLOW}是否继续？（输入 yes 并按回车确认）${NC}"
        read -r confirm1
        if [ "$confirm1" != "yes" ]; then
            echo -e "${CYAN}操作已取消。${NC}"
            return 0
        fi
    fi

    # 第二重确认
    echo ""
    echo -e "${RED}再次确认：初始化操作不可逆！${NC}"
    echo -e "${RED}输入 yes 并按回车将执行初始化（现有数据库将被备份并覆盖）${NC}"
    read -r confirm2
    if [ "$confirm2" != "yes" ]; then
        echo -e "${CYAN}操作已取消。${NC}"
        return 0
    fi

    # 执行备份（如果文件存在）
    if [ -f "$db_file" ]; then
        echo -e "${YELLOW}正在备份现有数据库 → $backup_file${NC}"
        mv "$db_file" "$backup_file" || {
            echo -e "${RED}备份失败！操作中止。${NC}"
            return 1
        }
        echo -e "${GREEN}备份完成${NC}"
    fi

    # 执行初始化（关键修复：添加 app.app_context()）
    echo -e "${YELLOW}正在初始化数据库...${NC}"
    "$PYTHON" -c "
from app import app
from utils import init_db

with app.app_context():
    init_db()
print('数据库初始化完成')
" || {
        echo -e "${RED}数据库初始化失败！请检查 app.py 或 utils.py 中的 init_db 函数${NC}"
        return 1
    }

    echo -e "${GREEN}数据库初始化成功完成！${NC}"
    return 0
}

# ==================== 菜单显示 ====================
show_menu() {
    clear
    echo -e "${GREEN}=== Cortana Grid 管理菜单 ===${NC}"
    echo "项目目录: $PROJECT_DIR"
    echo "Python:     $(python --version 2>/dev/null || echo '未知')"
    echo "----------------------------------------"
    echo "  1. 启动系统 (运行 app.py)"
    echo "  2. 生成代码包 (运行 code2ai.py)"
    echo "  3. 清理缓存 (clear_cache.py --force)"
    echo "  4. 安装/更新依赖"
    echo "  5. 初始化数据库（清空数据 + 双重确认）"
    echo "  0. 退出"
    echo "----------------------------------------"
    echo -e "${YELLOW}请输入选项数字（0-5）后按回车确认${NC}"
    echo -n "您的选择："
}

# ==================== 主循环 ====================
while true; do
    show_menu

    # 一直等待用户输入数字并按回车（无超时）
    read choice

    # 清理可能的残留输入缓冲
    read -t 0.1 -n 1000 discard 2>/dev/null || true

    case "$choice" in
        1)
            echo -e "${GREEN}启动 Cortana Grid Web 服务...${NC}"
            echo -e "${CYAN}访问地址：http://127.0.0.1:5000${NC}"
            echo -e "${CYAN}按 Ctrl+C 停止服务并返回菜单${NC}"
            echo "========================================"

            "$PYTHON" app.py &
            APP_PID=$!

            # 尝试等待服务启动并打开浏览器
            for i in {1..30}; do
                if curl -s http://127.0.0.1:5000 >/dev/null 2>&1; then
                    echo -e "${GREEN}服务已启动！尝试打开浏览器...${NC}"
                    URL="http://127.0.0.1:5000"
                    if command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" 2>/dev/null || true
                    elif [[ "$(uname)" == "Darwin" ]]; then open "$URL" 2>/dev/null || true
                    elif command -v powershell.exe >/dev/null 2>&1; then powershell.exe -Command "Start-Process '$URL'" 2>/dev/null || true
                    elif "$PYTHON" -c "import webbrowser" 2>/dev/null; then
                        "$PYTHON" -c "import webbrowser, time; time.sleep(0.5); webbrowser.open_new_tab('$URL')" 2>/dev/null || true
                    else
                        echo -e "${YELLOW}无法自动打开浏览器，请手动访问 $URL${NC}"
                    fi
                    break
                fi
                sleep 0.5
            done

            trap "kill $APP_PID 2>/dev/null; echo -e '${CYAN}服务已停止，返回菜单...${NC}'; sleep 1" INT
            wait $APP_PID 2>/dev/null || true
            trap - INT
            ;;

        2)
            if [ -f "code2ai.py" ]; then
                echo -e "${GREEN}执行 code2ai.py ...${NC}"
                "$PYTHON" code2ai.py
                echo -e "${GREEN}代码包生成完成${NC}"
            else
                echo -e "${RED}未找到 code2ai.py${NC}"
            fi
            read -p "按回车返回菜单..."
            ;;

        3)
            run_clear_cache
            read -p "按回车返回菜单..."
            ;;

        4)
            install_dependencies
            read -p "按回车返回菜单..."
            ;;

        5)
            init_database
            read -p "按回车返回菜单..."
            ;;

        0)
            echo -e "${GREEN}退出脚本，Good job, Chief.${NC}"
            deactivate 2>/dev/null || true
            exit 0
            ;;

        *)
            echo -e "${RED}无效选项，请输入 0-5 并按回车确认${NC}"
            sleep 1
            ;;
    esac
done
