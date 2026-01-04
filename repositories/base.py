# repositories/base.py
# 数据访问层基础模块：数据库连接管理 + 行转字典工厂函数

import sqlite3
import os
from flask import current_app, g
from utils import logger

# 项目根目录下的 instance 路径（与 app.py 保持一致）
INSTANCE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance')
DATABASE_PATH = os.path.join(INSTANCE_PATH, 'community_system.sqlite')

def dict_row_factory(cursor, row):
    """
    SQLite 行工厂函数：将查询结果的每一行转换为字典
    键为列名，值为对应数据
    """
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

def get_db_connection():
    """
    获取数据库连接（带上下文管理）
    - 自动设置 row_factory 为 dict_row_factory
    - 支持 with 语句自动关闭
    """
    if 'db' not in g:
        try:
            # 确保 instance 目录存在
            os.makedirs(INSTANCE_PATH, exist_ok=True)

            conn = sqlite3.connect(DATABASE_PATH)
            conn.row_factory = dict_row_factory
            conn.execute('PRAGMA foreign_keys = ON')  # 启用外键支持（可选）
            g.db = conn
        except sqlite3.Error as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    return g.db

def close_db(e=None):
    """
    关闭数据库连接（Flask 应用上下文 teardown 用）
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

# 可选：如果您想在 Flask 应用中自动注册 teardown
# 在 app.py 中添加：
# @app.teardown_appcontext
# def teardown_db(exception):
#     close_db(exception)
