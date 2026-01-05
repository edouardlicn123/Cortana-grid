# routes/person.py
# 人员管理专用蓝图（完整终极版 - 支持高级过滤搜索 + 分页 + 查看 + 友好下拉）

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
    url_prefix='/people',           # 已改为 /people
    template_folder='../templates'
)

# ========================== 列表页（支持过滤搜索 + 分页） ==========================
@person_bp.route('/', methods=['GET'])
@login_required
@permission_required('resource:person:view')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # 获取所有过滤参数（支持模糊搜索）
    name = request.args.get('name', '').strip()
    id_card = request.args.get('id_card', '').strip()
    building = request.args.get('building', '').strip()          # 现住小区/建筑名称模糊
    phone = request.args.get('phone', '').strip()
    person_type = request.args.get('person_type', '').strip()    # 精确匹配：常住人口 / 流动人口 / ''（不限）
    household_address = request.args.get('household_address', '').strip()
    family_id = request.args.get('family_id', '').strip()

    # 获取全量数据
    all_persons = get_all_persons()

    # 客户端过滤（数据量不大，性能完全足够）
    filtered_persons = []
    for p in all_persons:
        if name and name.lower() not in p.get('name', '').lower():
            continue
        if id_card and id_card not in p.get('id_card', ''):
            continue
        if building and building.lower() not in p.get('living_building_name', '').lower():
            continue
        if phone and phone not in p.get('phones', ''):
            continue
        if person_type and p.get('person_type') != person_type:
            continue
        if household_address and household_address.lower() not in p.get('household_address', '').lower():
            continue
        if family_id and family_id not in p.get('family_id', ''):
            continue
        filtered_persons.append(p)

    # 计算分页
    total = len(filtered_persons)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    start = (page - 1) * per_page
    end = start + per_page
    persons = filtered_persons[start:end]

    return render_template(
        'people_list.html',
        persons=persons,
        total_pages=total_pages,
        current_page=page,
        total=total
    )

# ========================== 新增 ==========================
@person_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('resource:person:edit')
def add():
    buildings = get_buildings_for_select()

    if request.method == 'POST':
        person_data = {
            'name': request.form.get('name', '').strip(),
            'id_card': request.form.get('id_card', '').strip(),
            'phones': request.form.get('phones', '').strip(),
            'gender': request.form.get('gender'),
            'birth_date': request.form.get('birth_date', '').strip(),
            'person_type': request.form.get('person_type'),
            'living_building_id': request.form.get('living_building_id'),
            'address_detail': request.form.get('address_detail', '').strip(),
            'household_building_id': request.form.get('household_building_id'),
            'household_address': request.form.get('household_address', '').strip(),
            'family_id': request.form.get('family_id', '').strip(),
            'household_entry_date': request.form.get('household_entry_date', '').strip(),
            'is_separated': 'is_separated' in request.form,
            'current_residence': request.form.get('current_residence', '').strip(),
            'is_migrated_out': 'is_migrated_out' in request.form,
            'household_exit_date': request.form.get('household_exit_date', '').strip(),
            'migration_destination': request.form.get('migration_destination', '').strip(),
            'is_deceased': 'is_deceased' in request.form,
            'death_date': request.form.get('death_date', '').strip(),
            'nationality': request.form.get('nationality', '').strip(),
            'political_status': request.form.get('political_status'),
            'marital_status': request.form.get('marital_status'),
            'education': request.form.get('education'),
            'work_study': request.form.get('work_study'),
            'health': request.form.get('health'),
            'notes': request.form.get('notes', '').strip(),
            'is_key_person': 'is_key_person' in request.form,
            'key_categories': ','.join(request.form.getlist('key_categories')),
            'other_id_type': request.form.get('other_id_type'),
            'passport': request.form.get('passport', '').strip(),
            'has_other_id': 'has_other_id' in request.form,
        }

        errors = []
        if not person_data['name']:
            errors.append('姓名不能为空')
        if not person_data['living_building_id']:
            errors.append('必须选择现住小区/建筑')
        if not person_data['address_detail']:
            errors.append('现住详细门牌不能为空')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('edit_person.html', person=person_data, buildings=buildings)

        try:
            create_person(
                name=person_data['name'],
                id_card=person_data['id_card'],
                phones=person_data['phones'],
                gender=person_data['gender'],
                birth_date=person_data['birth_date'],
                person_type=person_data['person_type'],
                living_building_id=int(person_data['living_building_id']) if person_data['living_building_id'] else None,
                address_detail=person_data['address_detail'],
                household_building_id=int(person_data['household_building_id']) if person_data['household_building_id'] else None,
                household_address=person_data['household_address'],
                family_id=person_data['family_id'],
                household_entry_date=person_data['household_entry_date'],
                is_separated=person_data['is_separated'],
                current_residence=person_data['current_residence'],
                is_migrated_out=person_data['is_migrated_out'],
                household_exit_date=person_data['household_exit_date'],
                migration_destination=person_data['migration_destination'],
                is_deceased=person_data['is_deceased'],
                death_date=person_data['death_date'],
                nationality=person_data['nationality'],
                political_status=person_data['political_status'],
                marital_status=person_data['marital_status'],
                education=person_data['education'],
                work_study=person_data['work_study'],
                health=person_data['health'],
                notes=person_data['notes'],
                is_key_person=person_data['is_key_person'],
                key_categories=person_data['key_categories'],
                other_id_type=person_data['other_id_type'],
                passport=person_data['passport']
            )
            flash(f'"{person_data["name"]}" 添加成功', 'success')
            logger.info(f"用户 {current_user.username} 新增人员: {person_data['name']}")
            return redirect(url_for('person.index', _t=int(time.time())))

        except Exception as e:
            logger.error(f"新增人员失败: {e}")
            flash('添加失败（数据库错误，请联系管理员查看日志）', 'error')
            return render_template('edit_person.html', person=person_data, buildings=buildings)

    return render_template('edit_person.html', person=None, buildings=buildings)

# ========================== 编辑 ==========================
@person_bp.route('/edit/<int:pid>', methods=['GET', 'POST'])
@login_required
@permission_required('resource:person:edit')
@grid_data_permission(write=True)
def edit(pid):
    person = get_person_by_id(pid)
    if not person:
        flash('人员记录不存在或已被删除', 'error')
        return redirect(url_for('person.index'))

    buildings = get_buildings_for_select()

    if request.method == 'POST':
        person_data = person.copy()
        person_data.update({
            'name': request.form.get('name', '').strip(),
            'id_card': request.form.get('id_card', '').strip(),
            'phones': request.form.get('phones', '').strip(),
            'gender': request.form.get('gender'),
            'birth_date': request.form.get('birth_date', '').strip(),
            'person_type': request.form.get('person_type'),
            'living_building_id': request.form.get('living_building_id'),
            'address_detail': request.form.get('address_detail', '').strip(),
            'household_building_id': request.form.get('household_building_id'),
            'household_address': request.form.get('household_address', '').strip(),
            'family_id': request.form.get('family_id', '').strip(),
            'household_entry_date': request.form.get('household_entry_date', '').strip(),
            'is_separated': 'is_separated' in request.form,
            'current_residence': request.form.get('current_residence', '').strip(),
            'is_migrated_out': 'is_migrated_out' in request.form,
            'household_exit_date': request.form.get('household_exit_date', '').strip(),
            'migration_destination': request.form.get('migration_destination', '').strip(),
            'is_deceased': 'is_deceased' in request.form,
            'death_date': request.form.get('death_date', '').strip(),
            'nationality': request.form.get('nationality', '').strip(),
            'political_status': request.form.get('political_status'),
            'marital_status': request.form.get('marital_status'),
            'education': request.form.get('education'),
            'work_study': request.form.get('work_study'),
            'health': request.form.get('health'),
            'notes': request.form.get('notes', '').strip(),
            'is_key_person': 'is_key_person' in request.form,
            'key_categories': ','.join(request.form.getlist('key_categories')),
            'other_id_type': request.form.get('other_id_type'),
            'passport': request.form.get('passport', '').strip(),
            'has_other_id': 'has_other_id' in request.form,
        })

        errors = []
        if not person_data['name']:
            errors.append('姓名不能为空')
        if not person_data['living_building_id']:
            errors.append('必须选择现住小区/建筑')
        if not person_data['address_detail']:
            errors.append('现住详细门牌不能为空')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('edit_person.html', person=person_data, buildings=buildings)

        try:
            update_person(
                pid,
                name=person_data['name'],
                id_card=person_data['id_card'],
                phone=person_data['phones'],
                gender=person_data['gender'],
                birth_date=person_data['birth_date'],
                person_type=person_data['person_type'],
                living_building_id=int(person_data['living_building_id']) if person_data['living_building_id'] else None,
                address_detail=person_data['address_detail'],
                household_building_id=int(person_data['household_building_id']) if person_data['household_building_id'] else None,
                household_address=person_data['household_address'],
                family_id=person_data['family_id'],
                household_entry_date=person_data['household_entry_date'],
                is_separated=person_data['is_separated'],
                current_residence=person_data['current_residence'],
                is_migrated_out=person_data['is_migrated_out'],
                household_exit_date=person_data['household_exit_date'],
                migration_destination=person_data['migration_destination'],
                is_deceased=person_data['is_deceased'],
                death_date=person_data['death_date'],
                nationality=person_data['nationality'],
                political_status=person_data['political_status'],
                marital_status=person_data['marital_status'],
                education=person_data['education'],
                work_study=person_data['work_study'],
                health=person_data['health'],
                notes=person_data['notes'],
                is_key_person=person_data['is_key_person'],
                key_categories=person_data['key_categories'],
                other_id_type=person_data['other_id_type'],
                passport=person_data['passport']
            )
            flash(f'"{person_data["name"]}" 修改成功', 'success')
            logger.info(f"用户 {current_user.username} 编辑人员 ID {pid}")
            return redirect(url_for('person.index', _t=int(time.time())))

        except Exception as e:
            logger.error(f"编辑人员失败: {e}")
            flash('修改失败（数据库错误，请联系管理员查看日志）', 'error')
            return render_template('edit_person.html', person=person_data, buildings=buildings)

    return render_template('edit_person.html', person=person, buildings=buildings)

# ========================== 查看详情 ==========================
@person_bp.route('/view/<int:pid>', methods=['GET'])
@login_required
@permission_required('resource:person:view')
def view(pid):
    person = get_person_by_id(pid)
    if not person:
        flash('人员记录不存在或已被删除', 'error')
        return redirect(url_for('person.index'))

    building = None
    if person['living_building_id']:
        building = get_building_by_id(person['living_building_id'])

    return render_template('view_person.html', person=person, building=building)

# ========================== 删除 ==========================
@person_bp.route('/delete/<int:pid>', methods=['POST'])
@login_required
@permission_required('resource:person:delete')
@grid_data_permission(write=True)
def delete(pid):
    success, msg = delete_person(pid)
    flash(msg, 'success' if success else 'error')
    logger.info(f"用户 {current_user.username} {'成功' if success else '失败'}删除人员 ID {pid}")
    return redirect(url_for('person.index', _t=int(time.time())))
