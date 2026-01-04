# routes/building.py
# 建筑管理专用蓝图（完整实现：列表、新增、编辑、删除）

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from permissions import permission_required, grid_data_permission
from repositories.grid_repo import get_all_grids
from repositories.building_repo import (
    get_all_buildings,
    get_building_by_id,
    create_building,
    update_building,
    delete_building
)
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
    buildings = get_all_buildings()
    grids = get_all_grids()
    return render_template('buildings.html', buildings=buildings, grids=grids)

# ========================== 新增 ==========================
@building_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('resource:building:edit')
def add():
    grids = get_all_grids()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        type_ = request.form.get('type', '').strip()
        grid_id_str = request.form.get('grid_id', '').strip()

        if not name:
            flash('小区/建筑名称不能为空', 'error')
        elif not type_:
            flash('请选择建筑类型', 'error')
        elif not grid_id_str:
            flash('必须选择所属网格', 'error')
        else:
            try:
                grid_id = int(grid_id_str)
                create_building(name=name, type=type_, grid_id=grid_id)
                flash(f'"{name}" 添加成功', 'success')
                logger.info(
                    f"用户 {current_user.username} 新增建筑: {name} "
                    f"(类型: {type_}, 网格ID: {grid_id})"
                )
                return redirect(url_for('building.index'))
            except ValueError:
                flash('网格选择无效', 'error')
            except Exception as e:
                logger.error(f"新增建筑失败: {e}")
                flash('添加失败（可能名称在该网格下已存在）', 'error')

        # POST 失败时保留用户输入，回显表单
        return render_template(
            'edit_building.html',
            building={'name': name, 'type': type_, 'grid_id': grid_id_str or None},
            grids=grids
        )

    # GET 请求：显示空白新增表单
    return render_template('edit_building.html', building=None, grids=grids)

# ========================== 编辑 ==========================
@building_bp.route('/edit/<int:bid>', methods=['GET', 'POST'])
@login_required
@permission_required('resource:building:edit')
@grid_data_permission(write=True)
def edit(bid):
    building = get_building_by_id(bid)
    if not building:
        flash('建筑记录不存在或已被删除', 'error')
        return redirect(url_for('building.index'))

    grids = get_all_grids()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        type_ = request.form.get('type', '').strip()
        grid_id_str = request.form.get('grid_id', '').strip()

        if not name:
            flash('小区/建筑名称不能为空', 'error')
        elif not type_:
            flash('请选择建筑类型', 'error')
        elif not grid_id_str:
            flash('必须选择所属网格', 'error')
        else:
            try:
                grid_id = int(grid_id_str)
                update_building(bid, name=name, type=type_, grid_id=grid_id)
                flash(f'"{name}" 修改成功', 'success')
                logger.info(
                    f"用户 {current_user.username} 编辑建筑 ID {bid}: {name} "
                    f"(新类型: {type_}, 新网格ID: {grid_id})"
                )
                return redirect(url_for('building.index'))
            except ValueError:
                flash('网格选择无效', 'error')
            except Exception as e:
                logger.error(f"编辑建筑失败: {e}")
                flash('修改失败（可能名称在该网格下已存在）', 'error')

        # POST 失败时保留用户输入
        building.update({
            'name': name,
            'type': type_,
            'grid_id': grid_id_str or None
        })

    return render_template('edit_building.html', building=building, grids=grids)

# ========================== 删除 ==========================
@building_bp.route('/delete/<int:bid>', methods=['POST'])
@login_required
@permission_required('resource:building:delete')
@grid_data_permission(write=True)
def delete(bid):
    success, msg = delete_building(bid)
    flash(msg, 'success' if success else 'error')
    logger.info(
        f"用户 {current_user.username} {'成功' if success else '失败'}删除建筑 ID {bid}"
    )
    return redirect(url_for('building.index'))
