# services/auth_service.py
# 认证相关业务服务（优化版 - 代码更简洁、可读性提升、健壮性更强，功能完全不变）

from flask import flash
from flask_login import login_user, logout_user, current_user
from repositories.user_repo import (
    authenticate_user,
    update_user_password,
    get_user_by_id
)
from werkzeug.security import check_password_hash
from utils import logger


def perform_login(username: str, password: str, remember: bool = False):
    """执行登录验证并处理登录逻辑"""
    user = authenticate_user(username, password)
    if not user:
        flash('用户名或密码错误', 'error')
        logger.warning(f"登录失败尝试: {username}")
        return None

    if not user.is_active:
        flash('账户已被禁用，请联系管理员', 'error')
        return None

    login_user(user, remember=remember)

    if getattr(user, 'must_change_password', False):
        flash('首次登录或密码已重置，请立即修改密码', 'warning')
    else:
        flash('登录成功，欢迎回来！', 'success')
        logger.info(f"用户 {username} 登录成功")

    return user


def perform_logout():
    """执行用户注销"""
    if current_user.is_authenticated:
        logger.info(f"用户 {current_user.username} 已注销")

    logout_user()
    flash('已安全注销', 'info')


def change_password(old_password: str, new_password: str) -> bool:
    """修改当前用户密码（传入明文，由 repo 层负责哈希）"""
    if not current_user.is_authenticated:
        flash('请先登录', 'error')
        return False

    # 验证原密码
    user_row = get_user_by_id(current_user.id)
    if not user_row or not check_password_hash(user_row['password_hash'], old_password):
        flash('原密码不正确', 'error')
        return False

    # 更新密码（repo 内部会哈希并清除强制改密标志）
    update_user_password(current_user.id, new_password)

    flash('密码修改成功，请重新登录', 'success')
    perform_logout()
    return True
