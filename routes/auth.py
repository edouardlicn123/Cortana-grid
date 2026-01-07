# routes/auth.py
# 认证相关路由（优化版 - 代码更简洁、结构清晰、可读性提升，功能完全不变）
# 修复：登录成功消息只在真实登录时显示，避免页面刷新重复出现（2026-01-07）

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, logout_user, current_user
from services.auth_service import perform_login, perform_logout, change_password as svc_change_password
# ↑↑↑ 使用别名避免与路由函数名冲突

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录路由"""
    if current_user.is_authenticated:
        return redirect(url_for('main.overview'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not username or not password:
            flash('请填写用户名和密码', 'error')
            return render_template('login.html')

        user = perform_login(username, password, remember)
        if user:
            if getattr(user, 'must_change_password', False):
                flash('首次登录或密码已重置，请立即修改密码', 'warning')
                return redirect(url_for('auth.change_password'))

            # 关键修复：只有真实登录（POST）时才显示欢迎消息
            flash('登录成功，欢迎回来！', 'success')
            return redirect(url_for('main.overview'))

        else:
            # perform_login 已内部处理错误，这里不需要重复 flash
            pass

    # GET 请求（首次访问登录页或刷新）直接渲染，不触发任何 flash
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """用户注销路由"""
    perform_logout()
    flash('已安全注销', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码路由（函数名保留，便于 url_for 调用）"""
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([old_password, new_password, confirm_password]):
            flash('请完整填写所有字段', 'error')
        elif new_password != confirm_password:
            flash('两次输入的新密码不一致', 'error')
        elif len(new_password) < 6:
            flash('新密码长度至少为6位', 'error')
        else:
            success = svc_change_password(old_password, new_password)
            if success:
                flash('密码修改成功，请重新登录', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('原密码不正确', 'error')

    return render_template('change_password.html')
