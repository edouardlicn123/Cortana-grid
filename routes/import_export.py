# routes/import_export.py
# 导入导出路由（优化版 - 代码更简洁、可读性提升、错误处理更友好，功能完全不变）
# 更新：2026-02-09 字段全面同步最新 schema，支持人员模块所有字段的导入导出
# 优化：导入/导出错误提示更具体，日志记录更详细，支持人员专属处理器

import os
import time
from flask import (
    Blueprint, send_from_directory, request, flash,
    redirect, url_for, render_template, current_app, jsonify
)
from flask_login import login_required, current_user
from permissions import permission_required
from services.import_export_service import (
    export_data_to_excel,
    process_import_excel,
    get_template_path
)
from services.import_export_person import export_person_to_excel, import_person_from_excel
from utils import logger


import_export_bp = Blueprint('import_export', __name__, url_prefix='/import_export')


def init_import_export_handlers(app):
    """初始化导入导出处理器（预留扩展点，可注册更多类型）"""
    with app.app_context():
        # 未来可在此注册其他模块的处理器（如建筑、网格等）
        pass


@import_export_bp.route('/')
@login_required
@permission_required('import_export:all')
def index():
    """导入导出首页"""
    return render_template('import_export.html')


@import_export_bp.route('/template/<data_type>')
@login_required
@permission_required('import_export:all')
def download_template(data_type):
    """下载导入模板（Excel空表 + 注释）"""
    template_path = get_template_path(data_type)

    if not template_path or not os.path.exists(template_path):
        flash(f'模板文件不存在：{data_type}', 'error')
        logger.warning(f"用户 {current_user.username} 请求不存在的模板：{data_type}")
        return redirect(url_for('import_export.index'))

    try:
        return send_from_directory(
            directory=os.path.dirname(template_path),
            path=os.path.basename(template_path),
            as_attachment=True,
            download_name=f"{data_type}_导入模板.xlsx"
        )
    except Exception as e:
        logger.error(f"下载模板失败 ({data_type}): {e}")
        flash('下载模板失败，请联系管理员', 'error')
        return redirect(url_for('import_export.index'))


@import_export_bp.route('/export/<data_type>')
@login_required
@permission_required('import_export:all')
def export(data_type):
    """导出数据为 Excel 文件"""
    try:
        if data_type == 'person':
            # 使用人员专属导出函数（支持所有字段）
            file_path, filename = export_person_to_excel(current_user)
        else:
            # 其他类型走通用处理器（未来扩展）
            file_path, filename = export_data_to_excel(data_type, current_user)

        # 强制刷新避免缓存
        return send_from_directory(
            directory=os.path.dirname(file_path),
            path=os.path.basename(file_path),
            as_attachment=True,
            download_name=filename
        )

    except ValueError as ve:
        flash(f'导出失败：{str(ve)}', 'error')
        logger.warning(f"用户 {current_user.username} 导出 {data_type} 失败（ValueError）：{ve}")
    except PermissionError:
        flash('权限不足，无法导出该类型数据', 'error')
    except Exception as e:
        flash('导出过程中发生未知错误，请查看日志', 'error')
        logger.error(f"用户 {current_user.username} 导出 {data_type} 异常: {e}", exc_info=True)

    return redirect(url_for('import_export.index'))


@import_export_bp.route('/import', methods=['POST'])
@login_required
@permission_required('import_export:all')
def import_data():
    """处理 Excel 文件导入"""
    if 'file' not in request.files or not request.files['file'].filename:
        flash('未选择文件或文件名为空', 'error')
        return redirect(url_for('import_export.index'))

    file = request.files['file']
    data_type = request.form.get('import_type', '').strip()

    if not data_type:
        flash('未指定导入类型', 'error')
        return redirect(url_for('import_export.index'))

    # 支持的文件类型校验
    allowed_extensions = {'.xlsx', '.xls'}
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        flash('仅支持 .xlsx / .xls 文件', 'error')
        return redirect(url_for('import_export.index'))

    try:
        if data_type == 'person':
            # 使用人员专属导入函数（真实写入 + 详细错误反馈）
            success, msg = import_person_from_excel(file, current_user)
        else:
            # 其他类型走通用处理器（未来扩展）
            success, msg = process_import_excel(file, data_type, current_user)

        flash(msg, 'success' if success else 'error')

        # 导入成功后强制刷新列表（避免缓存）
        if success and data_type == 'person':
            return redirect(url_for('person.index', _refresh=int(time.time())))

        return redirect(url_for('import_export.index'))

    except Exception as e:
        logger.error(f"用户 {current_user.username} 导入 {data_type} 失败: {e}", exc_info=True)
        flash(f'导入失败：{str(e)[:100]}...（详情见日志）', 'error')
        return redirect(url_for('import_export.index'))


# 可选：添加简单的 API 接口，用于前端异步上传（未来扩展）
@import_export_bp.route('/api/import/status', methods=['GET'])
@login_required
@permission_required('import_export:all')
def import_status():
    """查看最近导入状态（占位，未来可实现）"""
    return jsonify({
        'status': 'idle',
        'message': '暂无导入任务'
    })
