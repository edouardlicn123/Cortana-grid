# repositories/user_repo.py
# 用户数据访问层（优化终极版 - 功能完全不变，代码更健壮、可读、专业）

from repositories.base import get_db_connection
from werkzeug.security import check_password_hash, generate_password_hash
from utils import logger
from repositories.user import User
from typing import List, Dict, Optional, Tuple, Any


def get_user_by_username(username: str) -> Optional[Dict]:
    """
    根据用户名查询用户（用于登录验证）

    Args:
        username: 用户名

    Returns:
        Optional[Dict]: 用户字典（含所有字段），不存在或已软删除返回 None
    """
    query = "SELECT * FROM user WHERE username = ? AND is_deleted = 0"

    try:
        with get_db_connection() as conn:
            row = conn.execute(query, (username.strip(),)).fetchone()

        return dict(row) if row else None

    except Exception as e:
        logger.error(f"根据用户名查询用户失败 (username={username}): {e}")
        return None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    根据 ID 查询用户（Flask-Login load_user 用）

    Args:
        user_id: 用户 ID

    Returns:
        Optional[Dict]: 用户字典，不存在或已软删除返回 None
    """
    query = "SELECT * FROM user WHERE id = ? AND is_deleted = 0"

    try:
        with get_db_connection() as conn:
            row = conn.execute(query, (user_id,)).fetchone()

        return dict(row) if row else None

    except Exception as e:
        logger.error(f"根据ID查询用户失败 (user_id={user_id}): {e}")
        return None


def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    验证用户名和密码是否正确

    Args:
        username: 用户名
        password: 明文密码

    Returns:
        Optional[User]: 验证成功返回 User 对象，否则返回 None
    """
    user_dict = get_user_by_username(username)
    if user_dict and check_password_hash(user_dict['password_hash'], password):
        logger.info(f"用户登录验证成功: {username}")
        return User(user_dict)

    logger.warning(f"用户登录验证失败: {username} (密码错误或用户不存在)")
    return None


def update_user_password(user_id: int, new_password: str) -> bool:
    """
    更新用户密码（同时清除强制改密标记）

    Args:
        user_id: 用户 ID
        new_password: 明文新密码（将自动哈希）

    Returns:
        bool: 更新是否成功
    """
    new_hash = generate_password_hash(new_password)

    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE user SET password_hash = ?, must_change_password = 0 WHERE id = ?",
                (new_hash, user_id)
            )
            conn.commit()

        logger.info(f"用户密码更新成功 (user_id={user_id})")
        return True

    except Exception as e:
        logger.error(f"更新用户密码失败 (user_id={user_id}): {e}")
        return False


def update_user_settings(
    user_id: int,
    full_name: str | None = None,
    phone: str | None = None,
    page_size: int | None = None,
    preferred_css: str | None = None
) -> bool:
    """
    更新用户个人设置（仅更新提供的字段）

    Args:
        user_id: 用户 ID
        full_name: 显示姓名
        phone: 联系电话
        page_size: 个人偏好分页大小
        preferred_css: 偏好主题（若支持）

    Returns:
        bool: 更新是否成功
    """
    updates: list[str] = []
    values: list = []

    field_map = {
        'full_name': full_name,
        'phone': phone,
        'page_size': page_size,
        'preferred_css': preferred_css or ''
    }

    for field, value in field_map.items():
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value.strip() if isinstance(value, str) else value)

    if not updates:
        return True  # 无需更新

    set_clause = ', '.join(updates)
    values.append(user_id)
    update_sql = f"UPDATE user SET {set_clause} WHERE id = ?"

    try:
        with get_db_connection() as conn:
            conn.execute(update_sql, values)
            conn.commit()

        logger.info(f"用户个人设置更新成功 (user_id={user_id})")
        return True

    except Exception as e:
        logger.error(f"更新用户个人设置失败 (user_id={user_id}): {e}")
        return False


def toggle_user_active(user_id: int, is_active: bool) -> bool:
    """
    启用/禁用用户账户

    Args:
        user_id: 用户 ID
        is_active: True=启用, False=禁用

    Returns:
        bool: 操作是否成功
    """
    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE user SET is_active = ? WHERE id = ?",
                (1 if is_active else 0, user_id)
            )
            conn.commit()

        status = '启用' if is_active else '禁用'
        logger.info(f"用户账户状态变更成功 (user_id={user_id} → {status})")
        return True

    except Exception as e:
        logger.error(f"切换用户账户状态失败 (user_id={user_id}): {e}")
        return False


def reset_user_password(user_id: int, new_password: str = '123456') -> bool:
    """
    重置用户密码为默认值，并标记为下次登录必须修改

    Args:
        user_id: 用户 ID
        new_password: 重置后的明文密码（默认 '123456'）

    Returns:
        bool: 重置是否成功
    """
    new_hash = generate_password_hash(new_password)

    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE user SET password_hash = ?, must_change_password = 1 WHERE id = ?",
                (new_hash, user_id)
            )
            conn.commit()

        logger.info(f"用户密码重置成功 (user_id={user_id}) → 默认密码: {new_password}")
        return True

    except Exception as e:
        logger.error(f"重置用户密码失败 (user_id={user_id}): {e}")
        return False
