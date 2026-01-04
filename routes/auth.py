# routes/auth.py
# 认证相关路由（最终修复版 - 避免函数名冲突）

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, logout_user, current_user
from services.auth_service import perform_login, perform_logout, change_password as svc_change_password
# ↑↑↑ 关键：使用别名避免冲突

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
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

            return redirect(url_for('main.overview'))

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    perform_logout()
    return redirect(url_for('auth.login'))

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():  # 路由函数名保持，便于 url_for
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
            # 使用别名调用 service 层的函数
            success = svc_change_password(old_password, new_password)
            if success:
                flash('密码修改成功，请重新登录', 'success')
                return redirect(url_for('auth.login'))

    return render_template('change_password.html')
