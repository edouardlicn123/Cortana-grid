# repositories/base.py
# 数据访问层基础模块：数据库连接管理 + 行转字典工厂函数（优化版）

import sqlite3
import os
from flask import current_app, g
from utils import logger


# ==================== 配置常量 ====================
# 项目根目录下的 instance 路径（与 app.py 保持一致）
# 使用更可靠的路径计算方式，确保跨平台兼容
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INSTANCE_PATH = os.path.join(BASE_DIR, 'instance')
DATABASE_PATH = os.path.join(INSTANCE_PATH, 'community_system.sqlite')


# ==================== 行转字典工厂函数 ====================
def dict_row_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
    """
    SQLite 行工厂函数：将查询结果的每一行转换为字典。

    Args:
        cursor: SQLite 游标对象，用于获取列描述信息
        row: 原始行数据（tuple）

    Returns:
        dict: 键为列名，值为对应数据的字典
    """
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


# ==================== 数据库连接管理 ====================
def get_db_connection() -> sqlite3.Connection:
    """
    获取当前应用上下文中的数据库连接（单例模式）。

    特性：
    - 自动创建 instance 目录（如不存在）
    - 自动启用外键约束
    - 使用字典行工厂返回结果
    - 支持 with 语句自动关闭（通过 Flask 上下文管理）

    Returns:
        sqlite3.Connection: 已配置好的数据库连接对象

    Raises:
        sqlite3.Error: 数据库连接失败时抛出
    """
    if not hasattr(g, 'db') or g.db is None:
        try:
            # 确保 instance 目录存在
            os.makedirs(INSTANCE_PATH, exist_ok=True)

            conn = sqlite3.connect(
                DATABASE_PATH,
                detect_types=sqlite3.PARSE_DECLTYPES,
                timeout=10.0  # 增加超时防止锁冲突
            )
            conn.row_factory = dict_row_factory
            conn.execute('PRAGMA foreign_keys = ON')  # 启用外键支持
            g.db = conn

            logger.debug(f"数据库连接建立成功：{DATABASE_PATH}")
        except sqlite3.Error as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    return g.db


def close_db(exception=None) -> None:
    """
    关闭当前应用上下文中的数据库连接（Flask teardown 用）。

    Args:
        exception: Flask 传递的异常对象（未使用，仅保持签名兼容）
    """
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
            logger.debug("数据库连接已关闭")
        except sqlite3.Error as e:
            logger.error(f"关闭数据库连接时出错: {e}")


# ==================== 使用建议（注释保留，便于开发者参考） ====================
# 在主应用 app.py 中注册 teardown：
#
# from repositories.base import close_db
#
# @app.teardown_appcontext
# def teardown_db(exception):
#     close_db(exception)
