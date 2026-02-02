# repositories/base.py
# 数据访问层基础模块：数据库连接管理 + 行转字典工厂函数（优化版）
#
# 核心职责：
#   - 提供全局统一的 SQLite 数据库连接（Flask 上下文单例模式）
#   - 自动创建 instance 目录（如果不存在）
#   - 强制启用外键约束（PRAGMA foreign_keys = ON）
#   - 使用字典行工厂（row_factory），让 fetchone()/fetchall() 返回 dict 而非 tuple
#   - 支持 with 语句自动关闭连接（通过 Flask teardown_appcontext）
#
# 关键特性：
#   - 单例模式：每个请求只建立一次连接，请求结束自动关闭
#   - 字典行工厂：查询结果直接返回 dict，方便使用 row['column'] 取值
#   - 异常安全：连接失败会记录详细日志并抛出异常
#   - 跨平台路径兼容：使用 os.path.abspath + os.path.join 计算路径
#
# 注意事项：
#   - 所有数据库操作必须通过 get_db_connection() 获取连接，不要直接 sqlite3.connect()
#   - 如果 row_factory 未生效（查询返回 tuple 而非 dict），请检查：
#     1. dict_row_factory 函数是否正确定义
#     2. get_db_connection() 是否真的执行了 conn.row_factory = dict_row_factory
#     3. 是否有其他代码在连接后覆盖了 row_factory
#
# 版本：v2.3（仪表盘增强版）
# 更新历史：
#   - 2026-02-02：优化路径计算，增加超时参数（timeout=10.0）
#   - 2026-02-02：强制在连接后立即设置 row_factory，并添加调试日志
#   - 2026-02-02：完善异常处理，记录完整堆栈（exc_info=True）
#   - 2026-02-02：补充详细注释，便于排查 row_factory 未生效问题

import sqlite3
import os
from flask import current_app, g
from utils import logger


# ==================== 配置常量 ====================
# 项目根目录下的 instance 路径（与 app.py 保持一致）
# 使用可靠的路径计算方式，确保跨平台兼容
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
    - 自动创建 instance 目录（如果不存在）
    - 强制设置字典行工厂（row_factory），确保 fetchone/fetchall 返回 dict
    - 自动启用外键约束（PRAGMA foreign_keys = ON）
    - 支持 with 语句自动关闭（通过 Flask teardown_appcontext）
    - 增加连接超时（timeout=10.0），防止锁冲突
    
    Returns:
        sqlite3.Connection: 已配置好的数据库连接对象
    
    Raises:
        sqlite3.Error: 数据库连接失败时抛出
    """
    if not hasattr(g, 'db') or g.db is None:
        try:
            # 确保 instance 目录存在
            os.makedirs(INSTANCE_PATH, exist_ok=True)

            # 建立连接
            conn = sqlite3.connect(
                DATABASE_PATH,
                detect_types=sqlite3.PARSE_DECLTYPES,
                timeout=10.0  # 增加超时，防止数据库锁冲突
            )

            # 关键步骤：必须在这里设置 row_factory
            conn.row_factory = dict_row_factory

            # 启用外键约束
            conn.execute('PRAGMA foreign_keys = ON')

            # 调试确认（上线后可删除或改为 logger.debug）
            print("数据库连接建立成功，已设置 row_factory 为 dict_row_factory")
            logger.info(f"数据库连接建立成功：{DATABASE_PATH}")

            g.db = conn

        except sqlite3.Error as e:
            logger.error(f"数据库连接失败: {DATABASE_PATH} - {e}", exc_info=True)
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
# 在主应用 app.py 中注册 teardown（必须有，否则连接不会自动关闭）：
#
# from repositories.base import close_db
#
# @app.teardown_appcontext
# def teardown_db(exception):
#     close_db(exception)
#
# 推荐在所有 repo 函数中使用：
# with get_db_connection() as conn:
#     row = conn.execute(...).fetchone()
#     value = row['column_name']   # 现在可以直接用键访问
