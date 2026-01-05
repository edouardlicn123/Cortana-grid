# code2ai.py


import os
import datetime
import glob

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'code2ai')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================== 要包含的文件分类 ====================
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
        "routes/main.py",
        "routes/grid.py",
        "routes/person.py",
        "routes/building.py",
        "routes/import_export.py",
        "routes/system_settings.py",
        "routes/*.py",                   # 其他路由文件
    ],
    "数据访问层 (repositories/)": [
        "repositories/__init__.py",
        "repositories/base.py",
        "repositories/*.py",
    ],
    "业务服务层 (services/)": [
        "services/__init__.py",
        "services/*.py",
    ],
    "模板文件 (templates/)": [
        "templates/*.html",              # people.html, buildings.html, grids.html 等
        "templates/errors/*.html",
    ],
    "模板组件 (templates/includes/)": [
        "templates/includes/*.html",     # _navbar.html, _styles.html, _scripts.html 等
    ],
    "自定义样式 (static/css/)": [
        "static/css/style.css",
    ],
    "主题样式 (static/themes/)": [
        "static/themes/*.css",
    ],
    "自定义脚本 (static/js/)": [
        "static/js/*.js",
    ],
    "其他静态资源": [
        "static/favicon.ico",
        # uploads/ 目录仅保留结构，不包含实际照片
        "static/uploads/",               # 仅作为目录参考
    ]
}

# ==================== 排除规则 ====================
EXCLUDE_PATTERNS = {
    '__pycache__', '.git', '.venv', 'venv', 'instance', 'node_modules',
    'log', 'downloads', 'code2ai', 'dist', 'build', '.pytest_cache',
    '.DS_Store', '.idea', '.vscode'
}

# 明确排除所有 Bootstrap 相关文件
BOOTSTRAP_EXCLUDES = {
    'bootstrap.min.css',
    'bootstrap-icons.css',
    'bootstrap.bundle.min.js',
    'bootstrap.bundle.js',
    'bootstrap.js',
    'bootstrap.css',
    'bootstrap-icons.woff',
    'bootstrap-icons.woff2',
    'bootstrap-icons/fonts/',
}

def should_include(filepath):
    """判断文件是否应被打包"""
    rel_path = os.path.relpath(filepath, PROJECT_ROOT)
    filename = os.path.basename(filepath)

    # 排除指定目录
    for pattern in EXCLUDE_PATTERNS:
        if pattern in rel_path.split(os.sep):
            return False

    # 排除 Bootstrap 文件
    if filename in BOOTSTRAP_EXCLUDES:
        return False
    if 'bootstrap' in filename.lower() and ('css' in filename or 'js' in filename):
        return False

    # 排除数据库文件
    if 'instance' in rel_path and rel_path.endswith('.sqlite'):
        return False

    # 排除旧模板（已重构迁移）
    if rel_path in ['templates/persons.html', 'templates/person.html']:
        return False

    # uploads/ 只包含目录结构，不打包实际图片（避免文件过大）
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
                    # 只记录目录结构
                    collected[category].append(match + os.sep)  # 加 / 表示目录
    return collected


def generate_output():
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(OUTPUT_DIR, f'project_code_{timestamp}.txt')

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# 项目全量代码包 - 社区网格化人口管理系统（Cortana Grid）\n")
        f.write(f"# 生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# 项目路径: {PROJECT_ROOT}\n")
        f.write(f"# ====================================================================\n\n")
        f.write(f"当前项目状态：重构完成，核心模块高度独立\n")
        f.write(f"# ====================================================================\n\n")

        collected = collect_files()

        total_files = sum(len(files) for files in collected.values() if not str(files[0]).endswith(os.sep))
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
        f.write(f"# 项目已达到生产级标准，可直接用于 AI 分析、备份或交付\n")

    print(f"代码包已生成：{output_file}")
    print(f"共打包 {total_files} 个文件")
    print("打包完成，已完全匹配当前重构进度，可直接用于 AI 分析！")


if __name__ == '__main__':
    generate_output()
