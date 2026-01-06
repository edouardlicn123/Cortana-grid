# repositories/settings_repo.py
# 系统设置数据访问层（优化终极版 - 功能完全不变，代码更健壮、可读、专业）

from repositories.base import get_db_connection
from utils import logger
from typing import Dict


def get_setting(key: str, default: str = '') -> str:
    """
    获取指定的系统设置值

    Args:
        key: 设置键名（如 'community_name', 'default_page_size'）
        default: 当键不存在时的默认返回值

    Returns:
        str: 设置值，若不存在返回 default
    """
    query = "SELECT value FROM settings WHERE key = ?"

    try:
        with get_db_connection() as conn:
            row = conn.execute(query, (key,)).fetchone()

        value = row['value'] if row else default
        logger.debug(f"读取系统设置: {key} = {value}")
        return value

    except Exception as e:
        logger.error(f"获取系统设置失败 (key={key}): {e}")
        return default


def update_setting(key: str, value: str) -> None:
    """
    更新或插入系统设置值（UPSERT 操作）

    Args:
        key: 设置键名
        value: 要保存的设置值
    """
    # 使用 SQLite 的 UPSERT 语法（SQLite 3.24.0+ 支持），更简洁高效
    upsert_sql = """
        INSERT INTO settings (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """

    try:
        with get_db_connection() as conn:
            conn.execute(upsert_sql, (key.strip(), str(value).strip()))
            conn.commit()

        logger.info(f"系统设置已更新: {key} = {value}")
    except Exception as e:
        logger.error(f"更新系统设置失败 (key={key}, value={value}): {e}")
        raise


def get_all_settings() -> Dict[str, str]:
    """
    获取所有系统设置键值对（用于初始化或调试）

    Returns:
        Dict[str, str]: 所有设置的字典映射 {key: value}
    """
    query = "SELECT key, value FROM settings"

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        settings = {row['key']: row['value'] for row in rows}

        logger.debug(f"加载全部系统设置：共 {len(settings)} 项")
        return settings

    except Exception as e:
        logger.error(f"获取全部系统设置失败: {e}")
        return {}
