# repositories/settings_repo.py
# 系统设置数据访问层（社区名称、分页大小等全局设置）

from repositories.base import get_db_connection
from utils import logger

def get_setting(key: str, default: str = '') -> str:
    """获取系统设置值，不存在则返回默认值"""
    with get_db_connection() as conn:
        row = conn.execute(
            'SELECT value FROM settings WHERE key = ?',
            (key,)
        ).fetchone()
        return row['value'] if row else default

def update_setting(key: str, value: str):
    """更新或插入系统设置值"""
    with get_db_connection() as conn:
        # 先尝试更新
        result = conn.execute(
            'UPDATE settings SET value = ? WHERE key = ?',
            (value, key)
        )
        if result.rowcount == 0:
            # 不存在则插入
            conn.execute(
                'INSERT INTO settings (key, value) VALUES (?, ?)',
                (key, value)
            )
        conn.commit()
        logger.info(f"系统设置更新: {key} = {value}")

# 可选：批量获取所有设置（未来扩展用）
def get_all_settings() -> dict:
    with get_db_connection() as conn:
        rows = conn.execute('SELECT key, value FROM settings').fetchall()
        return {row['key']: row['value'] for row in rows}
