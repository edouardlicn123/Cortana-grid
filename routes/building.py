# routes/building.py
# 建筑管理专用蓝图（优化终极版 - 代码更简洁、可读性提升、错误处理更健壮，功能完全不变）
# 更新：建筑列表分页尊重用户个人设置的“每页显示条数”（2026-01-07）

import time
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from permissions import permission_required, grid_data_permission
from repositories.grid_repo import get_all_grids
from repositories.building_repo import (
    get_all_buildings,
    get_building_by_id,
    create_building,
    update_building,
    delete_building,
    get_person_count_by_building
)
from repositories.base import get_db_connection
from utils import logger

building_bp = Blueprint(
    'building',
    __name__,
    url_prefix='/buildings',
    template_folder='../templates'
)


# ========================== 列表页 ==========================
@building_bp.route('/', methods=['GET'])
@login_required
@permission_required('resource:building:view')
def index():
    """建筑/小区列表页（支持分页 + 用户个人设置）"""
    # 关键修复：使用用户个人分页设置，兜底 20
    per_page = current_user.page_size or 20
    page = request.args.get('page', 1, type=int)

    # 获取全量数据
    all_buildings = get_all_buildings()  # 已包含 grid_name

    # 分页计算
    total = len(all_buildings)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    buildings = all_buildings[start:start + per_page]

    # 预计算分页后数据的居住人数（避免模板中调用函数）
    for b in buildings:
        b['person_count'] = get_person_count_by_building(b['id'])

    grids = get_all_grids()

    return render_template(
        'buildings.html',
        buildings=buildings,
        grids=grids,
        current_page=page,
        total_pages=total_pages,
        total=total
    )


# ========================== 新增 ==========================
@building_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('resource:building:edit')
def add():
    """新增建筑"""
    grids = get_all_grids()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        type_ = request.form.get('type', '').strip() or 'residential_complex'
        grid_id_str = request.form.get('grid_id', '').strip()

        if not name:
            flash('小区/建筑名称不能为空', 'error')
        elif not grid_id_str:
            flash('必须选择所属网格', 'error')
        else:
            try:
                grid_id = int(grid_id_str)

                # 检查同网格下名称是否重复
                with get_db_connection() as conn:
                    existing = conn.execute(
                        "SELECT id FROM building WHERE name = ? AND grid_id = ? AND is_deleted = 0",
                        (name, grid_id)
                    ).fetchone()

                if existing:
                    flash(f'该网格下已存在名为 “{name}” 的建筑，无法重复添加', 'error')
                else:
                    create_building(name=name, type_=type_, grid_id=grid_id)
                    flash(f'"{name}" 添加成功', 'success')
                    logger.info(f"用户 {current_user.username} 新增建筑: {name} (类型: {type_}, 网格: {grid_id})")
                    return redirect(url_for('building.index', _t=int(time.time())))

            except ValueError:
                flash('网格选择无效，请刷新页面重试', 'error')
            except Exception as e:
                logger.error(f"新增建筑错误: {type(e).__name__}: {e}")
                flash('添加失败（数据库错误，请联系管理员查看日志）', 'error')

        # POST 失败时回填表单数据
        return render_template(
            'edit_building.html',
            building={'name': name, 'type': type_, 'grid_id': grid_id_str or None},
            grids=grids
        )

    # GET 请求：显示空表单
    return render_template('edit_building.html', building=None, grids=grids)


# ========================== 编辑 ==========================
@building_bp.route('/edit/<int:bid>', methods=['GET', 'POST'])
@login_required
@permission_required('resource:building:edit')
@grid_data_permission(write=True)
def edit(bid):
    """编辑建筑"""
    building = get_building_by_id(bid)
    if not building:
        flash('建筑记录不存在或已被删除', 'error')
        return redirect(url_for('building.index'))

    grids = get_all_grids()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        type_ = request.form.get('type', '').strip() or building.get('type', 'residential_complex')
        grid_id_str = request.form.get('grid_id', '').strip()

        if not name:
            flash('小区/建筑名称不能为空', 'error')
        elif not grid_id_str:
            flash('必须选择所属网格', 'error')
        else:
            try:
                grid_id = int(grid_id_str)

                # 检查修改后是否与其他建筑名称冲突（排除自身）
                with get_db_connection() as conn:
                    conflict = conn.execute(
                        "SELECT id FROM building WHERE name = ? AND grid_id = ? AND id != ? AND is_deleted = 0",
                        (name, grid_id, bid)
                    ).fetchone()

                if conflict:
                    flash(f'该网格下已存在名为 “{name}” 的建筑，无法修改为重复名称', 'error')
                else:
                    update_building(bid, name=name, type_=type_, grid_id=grid_id)
                    flash(f'"{name}" 修改成功', 'success')
                    logger.info(f"用户 {current_user.username} 编辑建筑 ID {bid}（新名称: {name}）")
                    return redirect(url_for('building.index', _t=int(time.time())))

            except ValueError:
                flash('网格选择无效，请刷新页面重试', 'error')
            except Exception as e:
                logger.error(f"编辑建筑错误 (ID: {bid}): {type(e).__name__}: {e}")
                flash('修改失败（数据库错误，请联系管理员查看日志）', 'error')

        # POST 失败时回填表单数据
        building.update({
            'name': name,
            'type': type_,
            'grid_id': grid_id_str or None
        })

    return render_template('edit_building.html', building=building, grids=grids)


# ========================== 查看详情 ==========================
@building_bp.route('/view/<int:bid>', methods=['GET'])
@login_required
@permission_required('resource:building:view')
def view(bid):
    """建筑详情页"""
    building = get_building_by_id(bid)
    if not building:
        flash('建筑记录不存在或已被删除', 'error')
        return redirect(url_for('building.index'))

    person_count = get_person_count_by_building(bid)

    return render_template('view_building.html', building=building, person_count=person_count)


# ========================== 删除 ==========================
@building_bp.route('/delete/<int:bid>', methods=['POST'])
@login_required
@permission_required('resource:building:delete')
@grid_data_permission(write=True)
def delete(bid):
    """删除建筑（软删除）"""
    success, msg = delete_building(bid)
    flash(msg, 'success' if success else 'error')
    logger.info(f"用户 {current_user.username} {'成功' if success else '失败'}删除建筑 ID {bid}")
    return redirect(url_for('building.index', _t=int(time.time())))
