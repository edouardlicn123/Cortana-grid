# routes/person.py
# 人员管理专用蓝图（优化终极版 - 代码更简洁、可读性提升、错误处理更一致，功能完全不变）

import time
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from permissions import permission_required, grid_data_permission
from repositories.person_repo import (
    get_all_persons,
    get_person_by_id,
    create_person,
    update_person,
    delete_person
)
from repositories.building_repo import get_buildings_for_select, get_building_by_id
from utils import logger


person_bp = Blueprint(
    'person',
    __name__,
    url_prefix='/people',
    template_folder='../templates'
)


# ========================== 列表页（高级过滤 + 分页） ==========================
@person_bp.route('/', methods=['GET'])
@login_required
@permission_required('resource:person:view')
def index():
    """人员列表页（支持多条件模糊/精确搜索 + 分页）"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # 搜索参数
    name = request.args.get('name', '').strip().lower()
    id_card = request.args.get('id_card', '').strip()
    building = request.args.get('building', '').strip().lower()
    phone = request.args.get('phone', '').strip()
    person_type = request.args.get('person_type', '').strip()
    household_address = request.args.get('household_address', '').strip().lower()
    family_id = request.args.get('family_id', '').strip()

    # 获取全量数据
    all_persons = get_all_persons()

    # 客户端过滤（数据量适中，性能完全足够）
    filtered_persons = [
        p for p in all_persons
        if (not name or name in p.get('name', '').lower())
        and (not id_card or id_card in p.get('id_card', ''))
        and (not building or building in p.get('living_building_name', '').lower())
        and (not phone or phone in p.get('phones', ''))
        and (not person_type or p.get('person_type') == person_type)
        and (not household_address or household_address in p.get('household_address', '').lower())
        and (not family_id or family_id in p.get('family_id', ''))
    ]

    # 分页计算
    total = len(filtered_persons)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    persons = filtered_persons[start:start + per_page]

    return render_template(
        'people_list.html',
        persons=persons,
        total_pages=total_pages,
        current_page=page,
        total=total
    )


# ========================== 新增人员 ==========================
@person_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('resource:person:edit')
def add():
    """新增人员"""
    buildings = get_buildings_for_select()

    if request.method == 'POST':
        person_data = _extract_person_data(request.form)

        errors = _validate_required_fields(person_data)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('edit_person.html', person=person_data, buildings=buildings)

        try:
            create_person(**_prepare_person_args(person_data))
            flash(f'"{person_data["name"]}" 添加成功', 'success')
            logger.info(f"用户 {current_user.username} 新增人员: {person_data['name']}")
            return redirect(url_for('person.index', _t=int(time.time())))
        except Exception as e:
            logger.error(f"新增人员失败: {e}")
            flash('添加失败（数据库错误，请联系管理员查看日志）', 'error')
            return render_template('edit_person.html', person=person_data, buildings=buildings)

    return render_template('edit_person.html', person=None, buildings=buildings)


# ========================== 编辑人员 ==========================
@person_bp.route('/edit/<int:pid>', methods=['GET', 'POST'])
@login_required
@permission_required('resource:person:edit')
@grid_data_permission(write=True)
def edit(pid):
    """编辑人员"""
    person = get_person_by_id(pid)
    if not person:
        flash('人员记录不存在或已被删除', 'error')
        return redirect(url_for('person.index'))

    buildings = get_buildings_for_select()

    if request.method == 'POST':
        person_data = person.copy()
        person_data.update(_extract_person_data(request.form))

        errors = _validate_required_fields(person_data)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('edit_person.html', person=person_data, buildings=buildings)

        try:
            update_person(pid, **_prepare_person_args(person_data))
            flash(f'"{person_data["name"]}" 修改成功', 'success')
            logger.info(f"用户 {current_user.username} 编辑人员 ID {pid}")
            return redirect(url_for('person.index', _t=int(time.time())))
        except Exception as e:
            logger.error(f"编辑人员失败 (ID: {pid}): {e}")
            flash('修改失败（数据库错误，请联系管理员查看日志）', 'error')
            return render_template('edit_person.html', person=person_data, buildings=buildings)

    return render_template('edit_person.html', person=person, buildings=buildings)


# ========================== 查看详情 ==========================
@person_bp.route('/view/<int:pid>', methods=['GET'])
@login_required
@permission_required('resource:person:view')
def view(pid):
    """人员详情页"""
    person = get_person_by_id(pid)
    if not person:
        flash('人员记录不存在或已被删除', 'error')
        return redirect(url_for('person.index'))

    building = None
    if person.get('living_building_id'):
        building = get_building_by_id(person['living_building_id'])

    return render_template('view_person.html', person=person, building=building)


# ========================== 删除人员 ==========================
@person_bp.route('/delete/<int:pid>', methods=['POST'])
@login_required
@permission_required('resource:person:delete')
@grid_data_permission(write=True)
def delete(pid):
    """删除人员（软删除）"""
    success, msg = delete_person(pid)
    flash(msg, 'success' if success else 'error')
    logger.info(f"用户 {current_user.username} {'成功' if success else '失败'}删除人员 ID {pid}")
    return redirect(url_for('person.index', _t=int(time.time())))


# ======================== 辅助函数 ========================
def _extract_person_data(form) -> dict:
    """从表单提取人员数据"""
    return {
        'name': form.get('name', '').strip(),
        'id_card': form.get('id_card', '').strip(),
        'phones': form.get('phones', '').strip(),
        'gender': form.get('gender'),
        'birth_date': form.get('birth_date', '').strip(),
        'person_type': form.get('person_type'),
        'living_building_id': form.get('living_building_id'),
        'address_detail': form.get('address_detail', '').strip(),
        'household_building_id': form.get('household_building_id'),
        'household_address': form.get('household_address', '').strip(),
        'family_id': form.get('family_id', '').strip(),
        'household_entry_date': form.get('household_entry_date', '').strip(),
        'is_separated': 'is_separated' in form,
        'current_residence': form.get('current_residence', '').strip(),
        'is_migrated_out': 'is_migrated_out' in form,
        'household_exit_date': form.get('household_exit_date', '').strip(),
        'migration_destination': form.get('migration_destination', '').strip(),
        'is_deceased': 'is_deceased' in form,
        'death_date': form.get('death_date', '').strip(),
        'nationality': form.get('nationality', '').strip(),
        'political_status': form.get('political_status'),
        'marital_status': form.get('marital_status'),
        'education': form.get('education'),
        'work_study': form.get('work_study'),
        'health': form.get('health'),
        'notes': form.get('notes', '').strip(),
        'is_key_person': 'is_key_person' in form,
        'key_categories': ','.join(form.getlist('key_categories')),
        'other_id_type': form.get('other_id_type'),
        'passport': form.get('passport', '').strip(),
    }


def _validate_required_fields(data: dict) -> list:
    """校验必填字段"""
    errors = []
    if not data['name']:
        errors.append('姓名不能为空')
    if not data['living_building_id']:
        errors.append('必须选择现住小区/建筑')
    if not data['address_detail']:
        errors.append('现住详细门牌不能为空')
    return errors


def _prepare_person_args(data: dict) -> dict:
    """准备传给 repo 的参数（类型转换）"""
    return {
        'name': data['name'],
        'id_card': data['id_card'],
        'phones': data['phones'],
        'gender': data['gender'],
        'birth_date': data['birth_date'],
        'person_type': data['person_type'],
        'living_building_id': int(data['living_building_id']) if data['living_building_id'] else None,
        'address_detail': data['address_detail'],
        'household_building_id': int(data['household_building_id']) if data['household_building_id'] else None,
        'household_address': data['household_address'],
        'family_id': data['family_id'],
        'household_entry_date': data['household_entry_date'],
        'is_separated': data['is_separated'],
        'current_residence': data['current_residence'],
        'is_migrated_out': data['is_migrated_out'],
        'household_exit_date': data['household_exit_date'],
        'migration_destination': data['migration_destination'],
        'is_deceased': data['is_deceased'],
        'death_date': data['death_date'],
        'nationality': data['nationality'],
        'political_status': data['political_status'],
        'marital_status': data['marital_status'],
        'education': data['education'],
        'work_study': data['work_study'],
        'health': data['health'],
        'notes': data['notes'],
        'is_key_person': data['is_key_person'],
        'key_categories': data['key_categories'],
        'other_id_type': data['other_id_type'],
        'passport': data['passport'],
    }
