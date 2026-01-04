#!/usr/bin/env python3
# clear_cache.py
# Cortana Grid 项目缓存清理工具（Python 版）
# 优势：跨平台、更安全、输出更美观、可轻松扩展

import shutil
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).parent.resolve()

# 要清理的模式
CLEAN_PATTERNS = [
    "**/__pycache__",
    "flask_session",
    ".pytest_cache",
    ".vscode",
    "code2ai",
    "**/*.pyc",
    "**/*.pyo",
    "**/*~",
]

# 安全保护：绝不删除的路径（即使匹配也跳过）
PROTECTED_PATHS = [
    PROJECT_ROOT / "instance",
    PROJECT_ROOT / "static" / "uploads",
    PROJECT_ROOT / "downloads",  # 新增：保护导入导出文件
]

def is_protected(path: Path) -> bool:
    """检查是否为受保护路径（数据库、用户照片、导入导出文件等）"""
    return any(path.is_relative_to(protected) for protected in PROTECTED_PATHS if protected.exists())

def clean_cache(dry_run: bool = False, force: bool = False) -> None:
    print("🧹 Cortana Grid 缓存清理工具（Python 版）\n")
    print(f"项目目录: {PROJECT_ROOT}\n")

    to_delete: List[Path] = []
    for pattern in CLEAN_PATTERNS:
        for path in PROJECT_ROOT.glob(pattern):
            if path.is_dir() or path.is_file():
                if not is_protected(path):
                    to_delete.append(path)

    if not to_delete:
        print("✅ 已干净！未发现需要清理的缓存文件。")
        return

    print("即将清理以下项目：")
    for item in to_delete:
        print(f"   • {item.relative_to(PROJECT_ROOT)}")
    print()

    if not force:
        confirm = input("确认清理？(y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ 清理已取消。")
            return

    if dry_run:
        print("🧪 干运行模式：以上文件将被删除（本次未实际操作）。")
        return

    deleted_count = 0
    for path in to_delete:
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"⚠️  删除失败 {path}: {e}")

    print(f"\n✅ 清理完成！共删除 {deleted_count} 个缓存项。")
    print("\n🔒 已安全保留：")
    print("   • 数据库文件 (instance/*.sqlite)")
    print("   • 用户上传照片 (static/uploads/)")
    print("   • 导入导出文件 (downloads/)")
    print("   • 所有源码与配置")
    print("\n💡 建议：清理后可运行 ./run.sh 重新启动项目。")
    print("\nGood job, Chief. 🚀")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cortana Grid 缓存清理工具")
    parser.add_argument("-f", "--force", action="store_true", help="强制清理，不提示确认")
    parser.add_argument("--dry-run", action="store_true", help="仅显示将删除内容，不实际操作")
    args = parser.parse_args()

    clean_cache(dry_run=args.dry_run, force=args.force)
