# routes/grid.py
# 网格管理专用蓝图（支持独立编辑页面）

from flask import Blueprint, render_template, request, redirect, url_for, flash
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

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'error')
            return redirect(url_for('auth.login'))
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
    grids = get_all_grids_with_managers_and_ids()
    return render_template('grids.html', grids=grids)

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
        except Exception as e:
            logger.error(f"新增网格失败: {e}")
            flash('添加失败，请重试', 'error')
    return redirect(url_for('grid.index'))

@grid_bp.route('/edit/<int:grid_id>', methods=['GET', 'POST'])
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

    # 加载所有活跃用户
    all_users = []
    try:
        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT id, username, full_name
                FROM user
                WHERE is_active = 1 AND is_deleted = 0
                ORDER BY username
            """).fetchall()
            all_users = [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"加载用户列表失败: {e}")

    # 加载当前负责人ID列表
    current_manager_ids = []
    try:
        with get_db_connection() as conn:
            rows = conn.execute("SELECT user_id FROM user_grid WHERE grid_id = ?", (grid_id,)).fetchall()
            current_manager_ids = [row['user_id'] for row in rows]
    except Exception as e:
        logger.error(f"加载当前负责人失败: {e}")

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        manager_ids = request.form.getlist('manager_ids')

        if not name:
            flash('网格名称不能为空', 'error')
        elif len(name) > 50:
            flash('网格名称不能超过50个字符', 'error')
        else:
            try:
                update_grid(grid_id, name)

                with get_db_connection() as conn:
                    conn.execute("DELETE FROM user_grid WHERE grid_id = ?", (grid_id,))
                    if manager_ids:
                        values = [(int(uid), grid_id) for uid in manager_ids if uid.isdigit()]
                        if values:
                            conn.executemany("INSERT OR IGNORE INTO user_grid (user_id, grid_id) VALUES (?, ?)", values)
                    conn.commit()

                flash(f'网格 "{name}" 修改成功', 'success')
                return redirect(url_for('grid.index'))
            except Exception as e:
                logger.error(f"编辑网格失败: {e}")
                flash('保存失败，请重试', 'error')

    # GET 请求：显示编辑页面
    return render_template('edit_grid.html',
                           grid=grid,
                           all_users=all_users,
                           current_manager_ids=current_manager_ids)

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
    except Exception as e:
        logger.error(f"切换网格状态失败: {e}")
        flash('操作失败，请重试', 'error')

    return redirect(url_for('grid.index'))
