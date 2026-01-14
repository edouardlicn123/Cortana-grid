#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
code2ai.py - Cortana Grid 项目核心源码汇总工具（增强版 - 带文件列表 + 多层分割线）
功能：
  - 读取项目根目录下的 code2ai_config.toml 配置
  - 生成带完整文件索引 + 清晰多层分割线的审查文件
  - 文件列表放在最前面，每个文件前后有明确开始/结束标记
"""

import os
import argparse
import tomllib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# ====================== 分割线样式（多层次，便于视觉区分） ======================
HEAVY_LINE = "═" * 90                  # 最粗，用于大章节分隔
MEDIUM_LINE = "─" * 70                 # 中等，用于文件头尾
LIGHT_LINE  = "─" * 50                 # 细线，用于文件内部小分隔
SECTION_TITLE = "═" * 25 + " {title} " + "═" * 25


def load_config(root: Path) -> Dict[str, Any]:
    config_path = root / "code2ai_config.toml"
    if not config_path.is_file():
        print(f"错误：未找到配置文件 {config_path}")
        print("请在项目根目录创建 code2ai_config.toml")
        exit(1)

    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        print(f"[OK] 已加载配置: {config_path}")
        return config
    except Exception as e:
        print(f"配置文件解析失败: {e}")
        exit(1)


def is_excluded(path: Path, config: Dict) -> bool:
    exclude = config.get("exclude", {})
    
    # 目录排除
    for part in path.parts:
        if part in exclude.get("dirs", []):
            return True
    
    # 文件名精确排除
    if path.name in exclude.get("files", []):
        return True
    
    # 扩展名排除
    if path.suffix.lower() in exclude.get("extensions", []):
        return True
    
    # 新增：文件名包含模式排除（不区分大小写，例如 bootstrap）
    patterns = exclude.get("filename_patterns", [])
    filename_lower = path.name.lower()
    for pattern in patterns:
        if pattern.lower() in filename_lower:
            return True
    
    return False


def is_included(path: Path, config: Dict) -> bool:
    include = config.get("include", {})
    special = config.get("special_include", {})

    # 扩展名白名单
    if path.suffix.lower() in include.get("extensions", []):
        return True

    # 路径关键词强制包含
    for pattern in special.get("force_include_patterns", []):
        if pattern in str(path):
            return True

    # 特定文件强制包含（相对路径匹配）
    rel_str = str(path.relative_to(path.parent.parent)) if path.parent.parent else str(path)
    if rel_str in special.get("force_include_files", []):
        return True

    return False


def collect_files(root: Path, config: Dict) -> List[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        # 原地修改，排除不需要递归的目录
        dirnames[:] = [d for d in dirnames if not is_excluded(current / d, config)]

        for filename in filenames:
            file_path = current / filename
            if is_excluded(file_path, config):
                continue
            if is_included(file_path, config):
                files.append(file_path)

    return sorted(files)


def main():
    parser = argparse.ArgumentParser(description="Cortana Grid 核心源码汇总工具（带文件列表+多层分割线）")
    parser.add_argument("-o", "--output", default="code2ai/",
                        help="输出目录（默认：项目根/code2ai/）")
    args = parser.parse_args()

    root = Path.cwd().resolve()
    config = load_config(root)

    print(f"项目根目录: {root}")
    print(f"正在扫描符合规则的文件...")

    files = collect_files(root, config)

    if not files:
        print("未找到任何符合规则的核心文件，请检查配置")
        return

    # 输出路径处理
    output_dir = Path(args.output).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = config.get("output", {}).get("filename_prefix", "cortana_grid_code_")
    output_file = output_dir / f"{prefix}{timestamp}.txt"

    max_size_kb = config.get("output", {}).get("max_file_size_kb", 1200)
    max_size = max_size_kb * 1024

    # 收集文件信息（用于生成清单）
    file_list_info = []
    skipped = 0

    for file_path in files:
        rel = file_path.relative_to(root)
        try:
            size = file_path.stat().st_size
            if size > max_size:
                print(f"跳过超大文件：{rel} ({size//1024:,} KB)")
                skipped += 1
                continue
            file_list_info.append((str(rel), size))
        except Exception as e:
            print(f"无法处理文件 {rel}: {e}")
            skipped += 1

    # 开始写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        # 头部信息
        f.write(f"""# Cortana Grid 全量核心代码包（供 AI 审查/分析/备份使用）
# 项目名称：{config.get("project", {}).get("name", "Cortana Grid")}
# 版本：{config.get("project", {}).get("version", "未知")}
# 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 配置文件：code2ai_config.toml
# 总扫描文件数：{len(files)}
# 实际包含文件数：{len(file_list_info)}
# 跳过文件数：{skipped}（超大/异常/被排除文件）
# 单个文件大小限制：≤ {max_size_kb} KB

{HEAVY_LINE}

{SECTION_TITLE.format(title="完整文件列表（快速定位用）")}
{HEAVY_LINE}

""")

        # 文件列表 - 美观对齐
        for i, (rel_path, size) in enumerate(file_list_info, 1):
            size_str = f"{size:,} 字节"
            f.write(f"  {i:3d} │ {rel_path:<68} │ {size_str:>12}\n")

        f.write(f"\n  共 {len(file_list_info)} 个文件（已跳过 {skipped} 个）\n\n")
        f.write(f"{HEAVY_LINE}\n\n")

        # 内容开始提示
        f.write(f"{SECTION_TITLE.format(title='文件内容开始')}\n")
        f.write(f"{HEAVY_LINE}\n\n")

        # 逐个文件内容
        for i, (rel_path_str, _) in enumerate(file_list_info, 1):
            file_path = root / rel_path_str

            f.write(f"{HEAVY_LINE}\n")
            f.write(f"文件 {i:03d} / {len(file_list_info)}    |   路径: {rel_path_str}\n")
            f.write(f"{MEDIUM_LINE}\n")
            f.write(f"开始 → {rel_path_str}\n")
            f.write(f"{LIGHT_LINE}\n\n")

            f.write("```text\n")
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                f.write(content.rstrip() + "\n")
            except Exception as e:
                f.write(f"# 读取文件内容失败：{e}\n")
            f.write("```\n\n")

            f.write(f"{LIGHT_LINE}\n")
            f.write(f"结束 ← {rel_path_str}\n")
            f.write(f"{MEDIUM_LINE}\n")
            f.write(f"{HEAVY_LINE}\n\n")

        # 文件尾部总结
        f.write(f"{HEAVY_LINE}\n")
        f.write(f"文件汇总结束 | 共包含 {len(file_list_info)} 个核心文件\n")
        f.write(f"生成工具：code2ai.py (2026增强版 - 带文件列表+多层分割线)\n")

    total_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"\n生成完成！")
    print(f"  输出文件：{output_file}")
    print(f"  包含核心文件：{len(file_list_info)} 个")
    print(f"  文件总大小：{total_mb:.2f} MB")
    if skipped:
        print(f"  已跳过：{skipped} 个文件（超大或异常）")


if __name__ == "__main__":
    main()
