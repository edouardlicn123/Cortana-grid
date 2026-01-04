# repositories/user_repo.py
# 用户数据访问层 - 所有用户相关 SQL 操作

from repositories.base import get_db_connection
from werkzeug.security import check_password_hash, generate_password_hash
from utils import logger

# 注意：User 类已移到 repositories/user.py，不在这里定义

from repositories.user import User

def get_user_by_username(username: str):
    """根据用户名查询用户（登录用）"""
    with get_db_connection() as conn:
        row = conn.execute(
            'SELECT * FROM user WHERE username = ? AND is_deleted = 0',
            (username,)
        ).fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id: int):
    """根据 ID 查询用户（Flask-Login 用）"""
    with get_db_connection() as conn:
        row = conn.execute(
            'SELECT * FROM user WHERE id = ? AND is_deleted = 0',
            (user_id,)
        ).fetchone()
        return dict(row) if row else None

def authenticate_user(username: str, password: str) -> User | None:
    """验证登录密码，返回 User 对象或 None"""
    user_dict = get_user_by_username(username)
    if user_dict and check_password_hash(user_dict['password_hash'], password):
        return User(user_dict)
    return None

def update_user_password(user_id: int, new_hash: str):
    """更新密码哈希"""
    with get_db_connection() as conn:
        conn.execute(
            'UPDATE user SET password_hash = ?, must_change_password = 0 WHERE id = ?',
            (new_hash, user_id)
        )
        conn.commit()
        logger.info(f"用户 {user_id} 密码已更新")

def update_user_settings(user_id: int, full_name: str, phone: str, page_size: int, preferred_css: str):
    """更新个人设置"""
    with get_db_connection() as conn:
        conn.execute(
            '''UPDATE user 
               SET full_name = ?, phone = ?, page_size = ?, preferred_css = ?
               WHERE id = ?''',
            (full_name, phone, page_size, preferred_css or '', user_id)
        )
        conn.commit()
        logger.info(f"用户 {user_id} 个人设置已更新")

def toggle_user_active(user_id: int, is_active: bool):
    """启用/禁用用户"""
    with get_db_connection() as conn:
        conn.execute(
            'UPDATE user SET is_active = ? WHERE id = ?',
            (1 if is_active else 0, user_id)
        )
        conn.commit()
        logger.info(f"用户 {user_id} 已{'启用' if is_active else '禁用'}")

def reset_user_password(user_id: int, new_password: str = '123456'):
    """重置密码为默认值"""
    with get_db_connection() as conn:
        conn.execute(
            '''UPDATE user 
               SET password_hash = ?, must_change_password = 1 
               WHERE id = ?''',
            (generate_password_hash(new_password), user_id)
        )
        conn.commit()
        logger.info(f"用户 {user_id} 密码已重置")
