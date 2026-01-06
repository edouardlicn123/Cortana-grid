# code2ai.py

import os
import datetime
import glob

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, '../code2ai')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================== 要包含的文件分类（2026-01-05 最新版） ====================
FILES_TO_INCLUDE = {
    "项目说明文档": [
        "*.html",                        # 根目录下的 progress.html, ARCHITECTURE_v2.html 等
        "docs/*.html",
        "docs/*.md",
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
        "routes/*.py",
    ],
    "数据访问层 (repositories/)": [
        "repositories/__init__.py",
        "repositories/*.py",
    ],
    "业务服务层 (services/)": [
        "services/__init__.py",
        "services/*.py",
    ],
    "主模板文件 (templates/)": [
        "templates/*.html",
    ],
    "错误页面 (templates/errors/)": [
        "templates/errors/*.html",
    ],
    "模板组件 (templates/includes/)": [
        "templates/includes/*.html",         # _navbar.html, _styles.html 等
    ],
    "自定义样式 (static/css/)": [
        "static/css/style.css",
    ],
    "主题样式 (static/themes/)": [
        "static/themes/*.css",
    ],
    "自定义脚本 (static/js/)": [
        "static/js/*.js",                    # idcard_parser.js, watermark.js 等
    ],
    "静态图标等": [
        "static/favicon.ico",
    ],
    "上传目录结构参考": [
        "static/uploads/",                   # 仅目录结构，不包含实际文件
    ]
}

# ==================== 排除规则 ====================
EXCLUDE_PATTERNS = {
    '__pycache__', '.git', '.venv', 'venv', 'instance', 'node_modules',
    'log', 'downloads', 'code2ai', 'dist', 'build', '.pytest_cache',
    '.DS_Store', '.idea', '.vscode'
}

# 明确排除的旧/废弃文件
EXCLUDE_FILES = {
    'templates/people.html',             # 旧版，已替换为 people_list.html
    'templates/persons.html',
    'templates/person.html',
    'templates/management.html',
    'routes/management.py',              # 已删除
}

# Bootstrap 等第三方文件（不打包）
BOOTSTRAP_EXCLUDES = {
    'bootstrap.min.css', 'bootstrap.css', 'bootstrap.bundle.min.js',
    'bootstrap.bundle.js', 'bootstrap.js', 'bootstrap-icons.css',
    'bootstrap-icons.woff', 'bootstrap-icons.woff2'
}

def should_include(filepath):
    """判断文件是否应被打包"""
    rel_path = os.path.relpath(filepath, PROJECT_ROOT)
    filename = os.path.basename(filepath)

    # 排除目录
    for pattern in EXCLUDE_PATTERNS:
        if pattern in rel_path.split(os.sep):
            return False

    # 明确排除旧文件
    if rel_path in EXCLUDE_FILES:
        return False

    # 排除 Bootstrap 文件
    if filename in BOOTSTRAP_EXCLUDES:
        return False
    if 'bootstrap' in filename.lower() and filename.endswith(('.css', '.js')):
        return False

    # 排除数据库文件
    if 'instance' in rel_path and rel_path.endswith('.sqlite'):
        return False

    # uploads/ 只保留目录结构，不打包实际图片
    if rel_path.startswith('static/uploads/') and os.path.isfile(filepath):
        return False

    return True


def collect_files():
    """收集所有需要打包的文件"""
    collected = {}
    for category, patterns in FILES_TO_INCLUDE.items():
        collected[category] = []
        for pattern in patterns:
            full_path = os.path.join(PROJECT_ROOT, pattern)
            matches = glob.glob(full_path, recursive=True)
            for match in matches:
                if os.path.isfile(match) and should_include(match):
                    collected[category].append(match)
                elif os.path.isdir(match) and 'uploads' in match:
                    collected[category].append(match + os.sep)  # 目录标记
    return collected


def generate_output():
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(OUTPUT_DIR, f'cortana_grid_code_{timestamp}.txt')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Cortana Grid 全量代码包 - 社区网格化人口管理系统\n")
        f.write(f"# 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 项目状态: 生产级稳定版（2026-01-05）\n")
        f.write(f"# URL 规范: /people/ | /buildings/ | /grids/\n")
        f.write(f"# ====================================================================\n\n")

        collected = collect_files()

        total_files = sum(len([f for f in files if not str(f).endswith(os.sep)]) for files in collected.values())
        f.write(f"# 打包摘要：共打包 {total_files} 个文件\n\n")

        for category, files in collected.items():
            file_count = len([f for f in files if not str(f).endswith(os.sep)])
            f.write(f"### CATEGORY: {category} ({file_count} 文件)\n")
            f.write(f"# {'=' * 80}\n\n")

            for file_path in sorted(files):
                if str(file_path).endswith(os.sep):
                    rel_path = os.path.relpath(file_path[:-1], PROJECT_ROOT)
                    f.write(f"### DIRECTORY: {rel_path}/\n\n")
                    continue

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

        f.write(f"# 打包完成 - 共 {total_files} 个文件\n")
        f.write(f"# 项目已完全就绪，可直接用于 AI 分析、备份、交付或开源\n")

    print(f"最新代码包已生成：{output_file}")
    print(f"共打包 {total_files} 个文件")
    print("Cortana Grid 生产级代码包生成成功！🚀")


if __name__ == '__main__':
    generate_output()
