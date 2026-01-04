# routes/system_settings.py
# 系统设置路由模块（完整最终版 - 2026-01-03）
# 新增：网格分配管理页面及完整后台逻辑

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from permissions import permission_required, DEFAULT_ROLE_PERMISSIONS
from repositories.user_repo import (
    get_all_users,
    toggle_user_active,
    reset_user_password,
    get_user_by_username
)
from repositories.settings_repo import get_setting, update_setting
from repositories.role_repo import get_all_roles, save_role_permissions
from repositories.grid_repo import get_all_grids
from repositories.base import get_db_connection
from werkzeug.security import generate_password_hash
from utils import logger

system_settings_bp = Blueprint('system_settings', __name__, template_folder='templates')

@system_settings_bp.route('/system_settings', methods=['GET', 'POST'])
@login_required
@permission_required('system:view')
def index():
    tab = request.args.get('tab', 'general')
    role_id_param = request.args.get('role_id')

    # 通用设置处理
    if request.method == 'POST' and request.form.get('action') == 'update_general':
        community_name = request.form.get('community_name', '').strip()
        default_page_size = request.form.get('default_page_size', '20').strip()
        show_default_credentials = bool(request.form.get('show_default_credentials'))

        if community_name:
            update_setting('community_name', community_name)
        if default_page_size.isdigit() and 10 <= int(default_page_size) <= 100:
            update_setting('default_page_size', default_page_size)
        update_setting('show_default_credentials', '1' if show_default_credentials else '0')

        flash('通用设置保存成功', 'success')
        return redirect(url_for('system_settings.index', tab='general'))

    # 角色权限保存处理
    if request.method == 'POST' and request.form.get('action') == 'update_permissions':
        role_id = request.form.get('role_id')
        if not role_id or not role_id.isdigit():
            flash('无效的角色ID', 'error')
            return redirect(url_for('system_settings.index', tab='permissions'))

        permissions = request.form.getlist('permissions')
        success = save_role_permissions(int(role_id), permissions)
        if success:
            flash('角色权限保存成功', 'success')
        else:
            flash('权限保存失败，请重试', 'error')
        return redirect(url_for('system_settings.index', tab='permissions', role_id=role_id))

    # 恢复默认权限处理（禁止 super_admin）
    if request.method == 'POST' and request.form.get('restore_default') == 'true':
        role_id = request.form.get('role_id')
        if not role_id or not role_id.isdigit():
            flash('无效的角色ID', 'error')
        else:
            with get_db_connection() as conn:
                role_row = conn.execute('SELECT name FROM role WHERE id = ?', (int(role_id),)).fetchone()
                if role_row and role_row['name'] != 'super_admin':
                    default_perms = DEFAULT_ROLE_PERMISSIONS.get(role_row['name'], [])
                    save_role_permissions(int(role_id), default_perms)
                    flash('已恢复该角色的默认权限', 'success')
                else:
                    flash('不允许操作超级管理员角色', 'error')
        return redirect(url_for('system_settings.index', tab='permissions', role_id=role_id))

    # 数据准备 - 角色列表：强制确保 community_admin 和 grid_user 可编辑
    all_roles = get_all_roles()
    required_names = ['community_admin', 'grid_user']
    existing_names = {r['name'] for r in all_roles if 'name' in r}

    editable_roles = [r for r in all_roles if r.get('name') in required_names]

    with get_db_connection() as conn:
        for name in required_names:
            if name not in existing_names:
                row = conn.execute('SELECT id, name FROM role WHERE name = ?', (name,)).fetchone()
                if row:
                    editable_roles.append({'id': row['id'], 'name': row['name']})

    editable_roles.sort(key=lambda x: 0 if x['name'] == 'community_admin' else 1)

    # 选中角色安全校验
    selected_role_id = None
    selected_role_name = None
    current_role_permissions = []

    if role_id_param and role_id_param.isdigit():
        candidate_id = int(role_id_param)
        with get_db_connection() as conn:
            row = conn.execute(
                'SELECT id, name FROM role WHERE id = ? AND name IN ("community_admin", "grid_user")',
                (candidate_id,)
            ).fetchone()
            if row:
                selected_role_id = row['id']
                selected_role_name = row['name']
                perms = conn.execute(
                    'SELECT permission FROM role_permission WHERE role_id = ?',
                    (selected_role_id,)
                ).fetchall()
                current_role_permissions = [p['permission'] for p in perms]

    users = get_all_users()

    community_name = get_setting('community_name', '阳光社区')
    default_page_size = get_setting('default_page_size', '20')
    show_default_credentials = get_setting('show_default_credentials', '0') == '1'

    return render_template(
        'system_settings.html',
        tab=tab,
        roles=editable_roles,
        selected_role_id=selected_role_id,
        selected_role_name=selected_role_name,
        current_role_permissions=current_role_permissions,
        users=users,
        community_name=community_name,
        default_page_size=default_page_size,
        show_default_credentials=show_default_credentials
    )

# 启用/禁用用户
@system_settings_bp.route('/system_settings/toggle_user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('system:view')
def toggle_user(user_id):
    with get_db_connection() as conn:
        row = conn.execute('SELECT is_active FROM user WHERE id = ?', (user_id,)).fetchone()
        if row:
            new_status = 0 if row['is_active'] else 1
            toggle_user_active(user_id, new_status)
            flash(f'用户已{"启用" if new_status else "禁用"}', 'success')
    return redirect(url_for('system_settings.index', tab='users'))

# 重置用户密码
@system_settings_bp.route('/system_settings/reset_password/<int:user_id>', methods=['POST'])
@login_required
@permission_required('system:view')
def reset_password(user_id):
    reset_user_password(user_id)
    flash('用户密码已重置为默认值，将在下次登录时强制修改', 'success')
    return redirect(url_for('system_settings.index', tab='users'))

# 添加新用户
@system_settings_bp.route('/system_settings/add_user', methods=['POST'])
@login_required
@permission_required('system:view')
def add_user():
    username = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    phone = request.form.get('phone', '').strip()
    role_id = request.form.get('role_id')

    if not username or not role_id:
        flash('用户名和角色为必填项', 'error')
        return redirect(url_for('system_settings.index', tab='users'))

    if get_user_by_username(username):
        flash('用户名已存在，请选择其他用户名', 'error')
        return redirect(url_for('system_settings.index', tab='users'))

    default_password = 'a12345678'
    password_hash = generate_password_hash(default_password)

    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                '''INSERT INTO user 
                   (username, password_hash, full_name, phone, is_active, must_change_password, page_size, preferred_css)
                   VALUES (?, ?, ?, ?, 1, 1, 20, '')''',
                (username, password_hash, full_name or None, phone or None)
            )
            user_id = cursor.lastrowid

            role_row = conn.execute('SELECT name FROM role WHERE id = ?', (int(role_id),)).fetchone()
            if role_row and role_row['name'] == 'super_admin':
                flash('不允许通过此界面分配超级管理员角色', 'error')
            else:
                conn.execute(
                    'INSERT OR IGNORE INTO user_role (user_id, role_id) VALUES (?, ?)',
                    (user_id, int(role_id))
                )

            conn.commit()

        flash(f'用户 "{username}" 添加成功！默认密码：{default_password}（请尽快告知用户修改）', 'success')
        logger.info(f"管理员 {current_user.username} 添加新用户: {username}")
    except Exception as e:
        logger.error(f"添加用户失败: {e}")
        flash('添加用户失败，请检查数据后重试', 'error')

    return redirect(url_for('system_settings.index', tab='users'))

# 新增：网格分配管理页面
@system_settings_bp.route('/grid_assignment', methods=['GET', 'POST'])
@login_required
@permission_required('system:view')
def grid_assignment():
    user_id_param = request.args.get('user_id')

    # 保存网格分配
    if request.method == 'POST' and request.form.get('action') == 'update_user_grids':
        user_id = request.form.get('user_id')
        selected_grid_ids = request.form.getlist('grid_ids')

        if not user_id or not user_id.isdigit():
            flash('无效的用户ID', 'error')
            return redirect(url_for('system_settings.grid_assignment'))

        try:
            user_id = int(user_id)
            grid_ids = [int(gid) for gid in selected_grid_ids if gid.isdigit()]

            with get_db_connection() as conn:
                conn.execute('DELETE FROM user_grid WHERE user_id = ?', (user_id,))
                if grid_ids:
                    conn.executemany(
                        'INSERT OR IGNORE INTO user_grid (user_id, grid_id) VALUES (?, ?)',
                        [(user_id, gid) for gid in grid_ids]
                    )
                conn.commit()

            flash('网格分配保存成功', 'success')
            logger.info(f"管理员 {current_user.username} 更新用户 {user_id} 的网格分配")
        except Exception as e:
            logger.error(f"保存网格分配失败: {e}")
            flash('保存失败，请重试', 'error')

        return redirect(url_for('system_settings.grid_assignment', user_id=user_id))

    # 获取数据
    users = get_all_users()
    all_grids = get_all_grids()

    selected_user_id = int(user_id_param) if user_id_param and user_id_param.isdigit() else None
    selected_user = None
    assigned_grid_ids = []

    if selected_user_id:
        with get_db_connection() as conn:
            user_row = conn.execute('SELECT id, username, full_name FROM user WHERE id = ?', (selected_user_id,)).fetchone()
            if user_row:
                selected_user = {
                    'id': user_row['id'],
                    'username': user_row['username'],
                    'full_name': user_row['full_name']
                }

                assigned = conn.execute('SELECT grid_id FROM user_grid WHERE user_id = ?', (selected_user_id,)).fetchall()
                assigned_grid_ids = [row['grid_id'] for row in assigned]

    return render_template(
        'grid_assignment.html',
        users=users,
        all_grids=all_grids,
        selected_user_id=selected_user_id,
        selected_user=selected_user,
        assigned_grid_ids=assigned_grid_ids
    )
