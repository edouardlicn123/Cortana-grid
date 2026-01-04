# services/auth_service.py
# 认证相关业务服务（最终稳定版 - 修复 check_password_hash 未定义）

from flask import flash
from flask_login import login_user, logout_user, current_user
from repositories.user_repo import authenticate_user, update_user_password, update_user_settings, get_user_by_id
from werkzeug.security import check_password_hash  # ← 添加导入
from utils import logger

def perform_login(username: str, password: str, remember: bool = False):
    """执行登录验证"""
    user = authenticate_user(username, password)
    if user:
        if not user.is_active:
            flash('账户已被禁用，请联系管理员', 'error')
            return None

        if getattr(user, 'must_change_password', False):
            flash('首次登录或密码已重置，请立即修改密码', 'warning')
            login_user(user, remember=remember)
            return user

        login_user(user, remember=remember)
        logger.info(f"用户 {username} 登录成功")
        flash('登录成功，欢迎回来！', 'success')
        return user
    else:
        flash('用户名或密码错误', 'error')
        logger.warning(f"登录失败尝试: {username}")
        return None

def perform_logout():
    """执行注销"""
    if current_user.is_authenticated:
        logger.info(f"用户 {current_user.username} 已注销")
    logout_user()
    flash('已安全注销', 'info')

def change_password(old_password: str, new_password: str) -> bool:
    """修改当前用户密码（传明文密码，让 repo 内部哈希）"""
    if not current_user.is_authenticated:
        flash('请先登录', 'error')
        return False

    # 验证旧密码
    user_row = get_user_by_id(current_user.id)
    if not user_row or not check_password_hash(user_row['password_hash'], old_password):
        flash('原密码不正确', 'error')
        return False

    # 直接传明文新密码，让 repo 内部哈希
    update_user_password(current_user.id, new_password)

    flash('密码修改成功，请重新登录', 'success')
    perform_logout()
    return True

def save_personal_settings(full_name: str, phone: str, page_size: int, preferred_css: str) -> bool:
    """保存个人设置"""
    if not current_user.is_authenticated:
        return False

    try:
        page_size = int(page_size)
        if page_size not in [10, 20, 30, 50, 100]:
            page_size = 20
    except:
        page_size = 20

    update_user_settings(
        user_id=current_user.id,
        full_name=full_name.strip(),
        phone=phone.strip(),
        page_size=page_size,
        preferred_css=preferred_css or ''
    )

    flash('个人设置保存成功', 'success')
    logger.info(f"用户 {current_user.username} 更新了个人设置")
    return True
