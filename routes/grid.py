# routes/grid.py
# 网格管理专用蓝图（最新版 - 仅 super_admin 和 community_admin 可访问和操作）

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from repositories.grid_repo import (
    get_all_grids_with_managers_and_ids,
    get_grid_basic,
    create_grid,
    update_grid,
    toggle_grid_deleted
)
from repositories.base import get_db_connection
from utils import logger

# 新增：仅管理员（super_admin / community_admin）可访问的装饰器
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if 'super_admin' not in current_user.roles and 'community_admin' not in current_user.roles:
            flash('权限不足，仅社区管理员和超级管理员可访问网格管理功能', 'error')
            return redirect(url_for('main.overview'))
        return f(*args, **kwargs)
    return decorated_function

grid_bp = Blueprint('grid', __name__, url_prefix='/grids', template_folder='../templates')

@grid_bp.route('/', methods=['GET'])
@login_required
@admin_only
def index():
    logger.info(f"用户 {current_user.username} 进入网格管理页面 (/grids)")
    grids = get_all_grids_with_managers_and_ids()

    # 加载活跃用户用于负责人授权
    all_users = []
    try:
        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT id, username, full_name
                FROM user
                WHERE is_active = 1 AND is_deleted = 0
                ORDER BY username ASC
            """).fetchall()
            all_users = [dict(row) for row in rows]
            for u in all_users:
                u['full_name'] = u['full_name'] or u['username']
        logger.info(f"加载活跃用户数: {len(all_users)}")
    except Exception as e:
        logger.error(f"加载用户失败: {e}")
        all_users = []

    return render_template('grids.html', grids=grids, all_users=all_users)

@grid_bp.route('/add', methods=['POST'])
@login_required
@admin_only
def add():
    name = request.form.get('name', '').strip()
    if not name:
        flash('网格名称不能为空', 'error')
    elif len(name) > 50:
        flash('网格名称不能超过50个字符', 'error')
    else:
        try:
            create_grid(name=name)
            flash(f'网格 "{name}" 添加成功', 'success')
            logger.info(f"用户 {current_user.username} 新增网格: {name}")
        except Exception as e:
            logger.error(f"新增网格失败: {e}")
            flash('添加失败，请重试', 'error')
    return redirect(url_for('grid.index'))

@grid_bp.route('/edit/<int:grid_id>', methods=['POST'])
@login_required
@admin_only
def edit(grid_id):
    grid = get_grid_basic(grid_id)
    if not grid:
        flash('网格不存在', 'error')
        return redirect(url_for('grid.index'))

    if grid['name'].startswith('虚拟网格'):
        flash('系统内置网格不可编辑', 'error')
        return redirect(url_for('grid.index'))

    if grid['is_deleted']:
        flash('已禁用的网格不可编辑', 'error')
        return redirect(url_for('grid.index'))

    name = request.form.get('name', '').strip()
    manager_ids = request.form.getlist('manager_ids')

    if not name:
        flash('网格名称不能为空', 'error')
    elif len(name) > 50:
        flash('网格名称不能超过50个字符', 'error')
    else:
        try:
            update_grid(grid_id, name=name)

            with get_db_connection() as conn:
                conn.execute("DELETE FROM user_grid WHERE grid_id = ?", (grid_id,))
                if manager_ids:
                    values = [(int(uid), grid_id) for uid in manager_ids if uid.isdigit()]
                    if values:
                        conn.executemany("INSERT OR IGNORE INTO user_grid (user_id, grid_id) VALUES (?, ?)", values)
                conn.commit()

            flash(f'网格 "{name}" 修改成功，负责人授权已更新', 'success')
            logger.info(f"用户 {current_user.username} 编辑网格 {grid_id}（新名称：{name}）")
        except Exception as e:
            logger.error(f"编辑网格失败: {e}")
            flash('修改失败，请重试', 'error')

    return redirect(url_for('grid.index'))

@grid_bp.route('/toggle_status/<int:grid_id>', methods=['POST'])
@login_required
@admin_only
def toggle_status(grid_id):
    grid = get_grid_basic(grid_id)
    if not grid:
        flash('网格不存在', 'error')
        return redirect(url_for('grid.index'))

    if grid['name'].startswith('虚拟网格'):
        flash('系统内置网格不可操作', 'error')
        return redirect(url_for('grid.index'))

    try:
        new_status = toggle_grid_deleted(grid_id)
        action = '启用' if new_status == 0 else '禁用'
        flash(f'网格 "{grid["name"]}" 已{action}', 'success')
        logger.info(f"用户 {current_user.username} {action}网格 {grid_id}")
    except Exception as e:
        logger.error(f"切换网格状态失败: {e}")
        flash('操作失败，请重试', 'error')

    return redirect(url_for('grid.index'))
