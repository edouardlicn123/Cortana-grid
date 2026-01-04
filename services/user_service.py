# services/user_service.py
# 系统用户管理业务（启用/禁用、重置密码等）

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

def generate_random_password(length: int = 10) -> str:
    """生成随机默认密码"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def toggle_user_active_status(user_id: int) -> tuple[bool, str]:
    """启用/禁用用户"""
    try:
        user = get_user_by_id(user_id)
        if not user:
            return False, '用户不存在'

        if user_id == current_user.id:
            return False, '不能禁用自己的账户'

        toggle_user_active(user_id)

        new_status = '启用' if user.get('is_active', True) == 0 else '禁用'
        logger.info(f"用户 {current_user.username} 将用户 {user['username']} {new_status}")

        return True, f'用户已{new_status}'

    except Exception as e:
        logger.error(f"切换用户状态失败 (ID: {user_id}): {e}")
        return False, '操作失败'

def reset_user_password(user_id: int) -> tuple[bool, str]:
    """重置用户密码为随机默认密码，并要求下次登录修改"""
    try:
        user = get_user_by_id(user_id)
        if not user:
            return False, '用户不存在'

        new_password = generate_random_password()
        hashed = generate_password_hash(new_password)

        update_user_password_hash(user_id, hashed)
        set_must_change_password_flag(user_id, True)

        logger.info(f"用户 {current_user.username} 重置了用户 {user['username']} 的密码")

        return True, f'密码已重置为：{new_password}（请妥善告知用户，并要求立即修改）'

    except Exception as e:
        logger.error(f"重置密码失败 (ID: {user_id}): {e}")
        return False, '重置失败'
