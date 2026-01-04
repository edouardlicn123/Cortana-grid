# code2ai.py
# 项目代码打包工具 - 最新进度版（2026-01-04）
# 根据当前重构完成状态更新：
# - 三大核心模块已完全独立（grid/person/building）
# - management.py 已删除或仅剩非核心功能
# - 路由结构规范：独立蓝图 + 复数路径
# - 模板已统一为 people.html / buildings.html 等
# - 保持排除 Bootstrap，包含所有文档和组件

import os
import datetime
import glob

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'code2ai')
os.makedirs(OUTPUT_DIR, exist_ok=True)

FILES_TO_INCLUDE = {
    "项目说明文档": [
        "*.html",                        # 根目录下的 progress.html, ARCHITECTURE_v2.html 等
        "docs/*.html",                   # docs 目录下所有说明文档
        "docs/*.md",                     # Markdown 文档（如有）
    ],
    "核心文件": [
        "app.py",
        "utils.py",
        "permissions.py",
        "schema.sql",
        "run.sh",
        "code2ai.py",
        "clear_cache.py",
        "requirements.txt",
    ],
    "路由模块 (routes/)": [
        "routes/__init__.py",
        "routes/main.py",
        "routes/grid.py",                # 网格管理独立模块
        "routes/person.py",              # 人员管理独立模块
        "routes/building.py",            # 建筑管理独立模块
        "routes/import_export.py",
        "routes/system_settings.py",
        "routes/*.py",                   # 其他路由文件（防止遗漏）
    ],
    "数据访问层 (repositories/)": [
        "repositories/__init__.py",
        "repositories/base.py",
        "repositories/*.py",             # 所有 repo 文件
    ],
    "业务事务层 (services/)": [
        "services/__init__.py",
        "services/*.py",                 # 所有 service 文件
    ],
    "模板文件 (templates/)": [
        "templates/*.html",              # 所有主模板（people.html, buildings.html, grids.html 等）
        "templates/errors/*.html",       # 错误页面
    ],
    "模板组件 (templates/includes/)": [
        "templates/includes/*.html",     # 所有组件（如 _navbar.html, _styles.html 等）
    ],
    "自定义样式 (static/css/)": [
        "static/css/style.css",          # 仅自定义样式
    ],
    "主题样式 (static/themes/)": [
        "static/themes/*.css",           # default.css + 所有用户主题
    ],
    "静态脚本 (static/js/)": [
        "static/js/*.js",                # 所有自定义脚本
    ],
    "其他静态资源": [
        "static/favicon.ico",
        "static/uploads/",               # 目录结构参考（空目录也保留）
    ]
}

# ==================== 排除规则 ====================
EXCLUDE_PATTERNS = {
    '__pycache__', '.git', '.venv', 'venv', 'instance', 'node_modules',
    'log', 'downloads', 'code2ai', 'dist', 'build', '.pytest_cache',
    '.DS_Store', '.idea', '.vscode'
}

# 明确排除所有 Bootstrap 文件
BOOTSTRAP_EXCLUDES = {
    'bootstrap.min.css',
    'bootstrap-icons.css',
    'bootstrap.bundle.min.js',
    'bootstrap.bundle.js',
    'bootstrap.js',
    'bootstrap.css',
    'bootstrap-icons.woff2',
}

def should_include(filepath):
    rel_path = os.path.relpath(filepath, PROJECT_ROOT)
    filename = os.path.basename(filepath)

    for pattern in EXCLUDE_PATTERNS:
        if pattern in rel_path.split(os.sep):
            return False

    if filename in BOOTSTRAP_EXCLUDES:
        return False

    if 'instance' in rel_path and rel_path.endswith('.sqlite'):
        return False

    # 排除旧的 persons.html（已迁移为 people.html）
    if rel_path == 'templates/persons.html':
        return False

    return True

def collect_files():
    collected = {}
    for category, patterns in FILES_TO_INCLUDE.items():
        collected[category] = []
        for pattern in patterns:
            full_path = os.path.join(PROJECT_ROOT, pattern)
            matches = glob.glob(full_path, recursive=True)
            for match in matches:
                if os.path.isfile(match) and should_include(match):
                    collected[category].append(match)
    return collected

def generate_output():
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(OUTPUT_DIR, f'project_code_{timestamp}.txt')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# 项目全量代码包 - 社区网格化人口管理系统（Cortana Grid）\n")
        f.write(f"# 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 项目路径: {PROJECT_ROOT}\n")
        f.write(f"# ====================================================================\n\n")
        f.write(f"当前项目状态：重构完成，三大核心模块（网格、人员、建筑）完全独立\n")
        f.write(f"主要特性：\n")
        f.write(f"- 规范独立蓝图结构：grid/person/building 三大模块独立路由\n")
        f.write(f"- 路径统一复数形式：/grids /persons /buildings\n")
        f.write(f"- 权限系统完整：角色 + 通配符 + 网格数据隔离\n")
        f.write(f"- 个人设置完整：姓名、分页、主题切换\n")
        f.write(f"- 所有核心功能稳定运行\n")
        f.write(f"- 已打包所有项目说明文档（根目录及 docs/ 目录）\n")
        f.write(f"- 已彻底排除所有 Bootstrap 文件（仅保留自定义样式）\n")
        f.write(f"# ====================================================================\n\n")

        collected = collect_files()

        total_files = 0
        for category, files in collected.items():
            file_count = len(files)
            total_files += file_count
            f.write(f"### CATEGORY: {category} ({file_count} 文件)\n")
            f.write(f"# {'=' * 80}\n\n")
            for file_path in sorted(files):
                rel_path = os.path.relpath(file_path, PROJECT_ROOT)
                f.write(f"### FILE: {rel_path}\n")
                f.write(f"# {'-' * 80}\n")
                try:
                    with open(file_path, 'r', encoding='utf-8') as code_file:
                        content = code_file.read()
                        f.write(content.rstrip() + '\n')
                except UnicodeDecodeError:
                    f.write("# BINARY FILE - SKIPPED CONTENT\n")
                except Exception as e:
                    f.write(f"# ERROR READING FILE: {e}\n")
                f.write("\n\n")
            f.write(f"# ====================================================================\n\n")

        f.write(f"# 打包摘要：共打包 {total_files} 个文件\n")
        f.write(f"# 已包含：所有代码、模板、文档、自定义资源\n")
        f.write(f"# 已排除：Bootstrap 文件、数据库、临时缓存、旧模板（如 persons.html）\n")

    print(f"代码包已生成：{output_file}")
    print(f"共打包 {total_files} 个文件")
    print("打包完成，已完全匹配当前重构进度，可直接用于 AI 分析！")
    print("Well done, Chief. 项目已达到生产级水准！🚀")

if __name__ == '__main__':
    generate_output()
