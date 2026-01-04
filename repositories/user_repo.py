# repositories/user_repo.py
# 用户数据访问层 - 所有用户相关的 SQL 操作（最终稳定版）

from repositories.base import get_db_connection
from werkzeug.security import check_password_hash, generate_password_hash
from utils import logger
from repositories.user_model import User

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

def update_user_password(user_id: int, new_password: str):
    """更新用户密码（接受明文密码，内部自动哈希）"""
    hashed = generate_password_hash(new_password)
    with get_db_connection() as conn:
        conn.execute(
            'UPDATE user SET password_hash = ?, must_change_password = 0 WHERE id = ?',
            (hashed, user_id)
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

def reset_user_password(user_id: int, new_password: str = 'a12345678'):
    """重置密码为默认值，并标记需改密"""
    hashed = generate_password_hash(new_password)
    with get_db_connection() as conn:
        conn.execute(
            '''UPDATE user 
               SET password_hash = ?, must_change_password = 1 
               WHERE id = ?''',
            (hashed, user_id)
        )
        conn.commit()
        logger.info(f"用户 {user_id} 密码已重置")

def get_all_users():
    """获取所有用户列表（系统设置页面用）"""
    with get_db_connection() as conn:
        rows = conn.execute('''
            SELECT 
                u.id, 
                u.username, 
                u.full_name, 
                u.phone, 
                u.is_active, 
                u.must_change_password,
                GROUP_CONCAT(r.name) AS roles_str
            FROM user u
            LEFT JOIN user_role ur ON u.id = ur.user_id
            LEFT JOIN role r ON ur.role_id = r.id
            WHERE u.is_deleted = 0
            GROUP BY u.id
            ORDER BY u.id
        ''').fetchall()

        users = []
        for row in rows:
            user_dict = dict(row)
            roles_str = row['roles_str']
            user_dict['roles'] = roles_str.split(',') if roles_str else []
            users.append(user_dict)
        
        return users

__all__ = [
    'get_user_by_username',
    'get_user_by_id',
    'authenticate_user',
    'update_user_password',
    'update_user_settings',
    'toggle_user_active',
    'reset_user_password',
    'get_all_users',
]
