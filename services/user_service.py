# services/user_service.py
# 系统用户管理业务逻辑（优化版 - 安全、健壮、可维护）

import secrets
import string
from flask_login import current_user
from werkzeug.security import generate_password_hash
from repositories.user_repo import (
    get_user_by_id,
    toggle_user_active,
    update_user_password_hash,
    set_must_change_password_flag
)
from utils import logger


def generate_random_password(length: int = 12) -> str:
    """
    生成强随机默认密码
    包含大小写字母 + 数字，至少12位（更安全）
    """
    alphabet = string.ascii_letters + string.digits
    # 确保至少包含一个大写、小写和数字（可选增强）
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def toggle_user_active_status(user_id: int) -> tuple[bool, str]:
    """启用/禁用用户账户"""
    try:
        user = get_user_by_id(user_id)
        if not user:
            return False, '用户不存在'

        if user_id == current_user.id:
            return False, '不能禁用或启用自己的账户'

        # 当前状态取反
        current_active = bool(user.get('is_active', True))
        toggle_user_active(user_id, not current_active)

        new_status = '启用' if not current_active else '禁用'
        logger.info(f"管理员 {current_user.username} 将用户 {user['username']} (ID: {user_id}) {new_status}")

        return True, f'用户 "{user['username']}" 已{new_status}'

    except Exception as e:
        logger.error(f"切换用户状态失败 (ID: {user_id}): {e}")
        return False, '操作失败，请重试'


def reset_user_password(user_id: int) -> tuple[bool, str]:
    """重置用户密码为随机值，并强制下次登录修改"""
    try:
        user = get_user_by_id(user_id)
        if not user:
            return False, '用户不存在'

        if user_id == current_user.id:
            return False, '请通过“修改密码”功能更改自己的密码'

        new_password = generate_random_password(12)
        hashed = generate_password_hash(new_password)

        update_user_password_hash(user_id, hashed)
        set_must_change_password_flag(user_id, True)

        logger.info(f"管理员 {current_user.username} 重置了用户 {user['username']} (ID: {user_id}) 的密码")

        return True, f'密码已重置为：<strong>{new_password}</strong><br>请立即安全告知用户，并要求其登录后<strong>必须修改密码</strong>'

    except Exception as e:
        logger.error(f"重置用户密码失败 (ID: {user_id}): {e}")
        return False, '重置失败，请重试'
