# services/import_export_service.py
# 导入导出总入口（极轻量） - 只负责公共工具和转发
# 实际逻辑按实体拆分到 import_export_person.py 和 import_export_building.py

import os
from flask import current_app
from werkzeug.utils import secure_filename
from utils import logger

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_template_path(data_type: str) -> str | None:
    """返回指定类型的导入模板路径"""
    base_dir = os.path.join(current_app.static_folder, 'templates', 'excel')
    templates = {
        'person': os.path.join(base_dir, '人员导入模板.xlsx'),
        'building': os.path.join(base_dir, '建筑导入模板.xlsx'),
    }
    return templates.get(data_type)


# ==================== 导出转发 ====================
def export_data_to_excel(data_type: str, user) -> tuple[str, str]:
    if data_type == 'person':
        from .import_export_person import export_person_to_excel
        return export_person_to_excel(user)
    elif data_type == 'building':
        from .import_export_building import export_building_to_excel
        return export_building_to_excel(user)
    else:
        raise ValueError("不支持的导出类型")


# ==================== 导入转发 ====================
def process_import_excel(file, data_type: str, user) -> tuple[bool, str]:
    if data_type == 'person':
        from .import_export_person import import_person_from_excel
        return import_person_from_excel(file, user)
    elif data_type == 'building':
        from .import_export_building import import_building_from_excel
        return import_building_from_excel(file, user)
    else:
        raise ValueError("不支持的导入类型")
