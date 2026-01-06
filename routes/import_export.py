# routes/import_export.py
# 导入导出路由（优化版 - 代码更简洁、可读性提升、错误处理更友好，功能完全不变）

import os
from flask import (
    Blueprint, send_from_directory, request, flash,
    redirect, url_for, render_template, current_app
)
from flask_login import login_required, current_user
from permissions import permission_required
from services.import_export_service import (
    export_data_to_excel,
    process_import_excel,
    get_template_path
)


import_export_bp = Blueprint('import_export', __name__, url_prefix='/import_export')


def init_import_export_handlers(app):
    """初始化导入导出处理器（预留扩展点）"""
    with app.app_context():
        # 未来可在此注册更多类型处理器
        pass


@import_export_bp.route('/')
@login_required
@permission_required('import_export:all')
def index():
    """导入导出首页"""
    return render_template('import_export.html')


@import_export_bp.route('/template/<data_type>')
@login_required
def download_template(data_type):
    """下载导入模板"""
    template_path = get_template_path(data_type)

    if not template_path or not os.path.exists(template_path):
        flash('请求的模板文件不存在', 'error')
        return redirect(url_for('import_export.index'))

    return send_from_directory(
        directory=os.path.dirname(template_path),
        path=os.path.basename(template_path),
        as_attachment=True,
        download_name=os.path.basename(template_path)
    )


@import_export_bp.route('/export/<data_type>')
@login_required
@permission_required('import_export:all')
def export(data_type):
    """导出数据为 Excel 文件"""
    try:
        file_path, filename = export_data_to_excel(data_type, current_user)

        return send_from_directory(
            directory=os.path.dirname(file_path),
            path=os.path.basename(file_path),
            as_attachment=True,
            download_name=filename
        )
    except ValueError as ve:
        flash(f'导出失败：{str(ve)}', 'error')
    except Exception as e:
        flash('导出过程中发生未知错误，请查看日志', 'error')
        current_app.logger.error(f"用户 {current_user.username} 导出 {data_type} 失败: {e}")

    return redirect(url_for('import_export.index'))


@import_export_bp.route('/import', methods=['POST'])
@login_required
@permission_required('import_export:all')
def import_data():
    """处理 Excel 文件导入"""
    if 'file' not in request.files:
        flash('未选择文件', 'error')
        return redirect(url_for('import_export.index'))

    file = request.files['file']
    data_type = request.form.get('import_type')

    if file.filename == '':
        flash('未选择文件', 'error')
        return redirect(url_for('import_export.index'))

    if not data_type:
        flash('未指定导入类型', 'error')
        return redirect(url_for('import_export.index'))

    success, msg = process_import_excel(file, data_type, current_user)
    flash(msg, 'success' if success else 'error')

    return redirect(url_for('import_export.index'))
