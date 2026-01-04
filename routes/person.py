# routes/person.py
# 人员管理专用蓝图（完全独立重构版）

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from permissions import permission_required, grid_data_permission
from repositories.person_repo import (
    get_person_by_id,
    get_all_persons,  # 新增：假设你有这个函数获取人员列表
    create_person,
    update_person,
    delete_person
)
from services.person_service import process_person_form
from utils import logger

person_bp = Blueprint('person', __name__, url_prefix='/persons', template_folder='../templates')

# 独立列表页
@person_bp.route('/', methods=['GET'])
@login_required
@permission_required('resource:person:view')
@grid_data_permission(write=False)
def index():
    logger.info(f"用户 {current_user.username} 进入人员管理列表页 (/persons/)")
    
    search = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 20

    persons, total = get_all_persons(search=search, page=page, per_page=per_page)
    total_pages = (total + per_page - 1) // per_page if total else 1

    return render_template(
        'people.html',
        people=persons,
        search=search,
        page=page,
        total_pages=total_pages
    )

# 新增
@person_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('resource:person:edit')
@grid_data_permission(write=True)
def add():
    logger.info(f"用户 {current_user.username} 访问人员新增")
    if request.method == 'POST':
        success, msg = process_person_form(request.form, request.files)
        if success:
            flash(msg or '人员新增成功', 'success')
            return redirect(url_for('person.index'))
        flash(msg or '新增失败', 'error')

    return render_template('edit_person.html', person=None)

# 编辑
@person_bp.route('/edit/<int:pid>', methods=['GET', 'POST'])
@login_required
@permission_required('resource:person:edit')
@grid_data_permission(write=True)
def edit(pid):
    person = get_person_by_id(pid)
    if not person:
        flash('人员记录不存在', 'error')
        return redirect(url_for('person.index'))

    if request.method == 'POST':
        success, msg = process_person_form(request.form, request.files, person_id=pid)
        if success:
            flash(msg or '人员信息更新成功', 'success')
            return redirect(url_for('person.index'))
        flash(msg or '更新失败', 'error')

    return render_template('edit_person.html', person=person)

# 删除
@person_bp.route('/delete/<int:pid>', methods=['POST'])
@login_required
@permission_required('resource:person:delete')
@grid_data_permission(write=True)
def delete(pid):
    success, msg = delete_person(pid)
    flash(msg or ('人员删除成功' if success else '删除失败'), 'success' if success else 'error')
    return redirect(url_for('person.index'))

# 查看详情
@person_bp.route('/view/<int:pid>', methods=['GET'])
@login_required
@permission_required('resource:person:view')
@grid_data_permission(write=False)
def view(pid):
    person = get_person_by_id(pid)
    if not person:
        flash('人员记录不存在', 'error')
        return redirect(url_for('person.index'))
    return render_template('person_view.html', person=person)
