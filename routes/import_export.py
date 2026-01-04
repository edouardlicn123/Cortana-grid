# routes/import_export.py
# 导入导出路由（模板下载、导出数据、导入处理）

import os
from flask import Blueprint, send_from_directory, request, flash, redirect, url_for, render_template, current_app, send_file
from flask_login import login_required, current_user
from permissions import permission_required
from services.import_export_service import (
    export_data_to_excel,
    process_import_excel,
    get_template_path
)

import_export_bp = Blueprint('import_export', __name__, url_prefix='/import_export')

# 初始化：注册支持的导入导出类型及其处理器（可扩展）
def init_import_export_handlers(app):
    with app.app_context():
        # 这里可以注册更多类型
        pass

@import_export_bp.route('/')
@login_required
@permission_required('import_export:all')
def index():
    return render_template('import_export.html')

@import_export_bp.route('/template/<data_type>')
@login_required
def download_template(data_type):
    template_path = get_template_path(data_type)
    if not template_path or not os.path.exists(template_path):
        flash('模板文件不存在', 'error')
        return redirect(url_for('import_export.index'))
    return send_from_directory(
        directory=os.path.dirname(template_path),
        path=os.path.basename(template_path),
        as_attachment=True
    )

@import_export_bp.route('/export/<data_type>')
@login_required
@permission_required('import_export:all')
def export(data_type):
    try:
        file_path, filename = export_data_to_excel(data_type, current_user)
        return send_from_directory(
            directory=os.path.dirname(file_path),
            path=os.path.basename(file_path),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        flash(f'导出失败：{str(e)}', 'error')
        return redirect(url_for('import_export.index'))

@import_export_bp.route('/import', methods=['POST'])
@login_required
@permission_required('import_export:all')
def import_data():
    if 'file' not in request.files:
        flash('未选择文件', 'error')
        return redirect(url_for('import_export.index'))

    file = request.files['file']
    data_type = request.form.get('import_type')

    if not file or file.filename == '':
        flash('未选择文件', 'error')
        return redirect(url_for('import_export.index'))

    success, msg = process_import_excel(file, data_type, current_user)
    flash(msg, 'success' if success else 'error')
    return redirect(url_for('import_export.index'))
