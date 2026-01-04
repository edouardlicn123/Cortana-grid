# services/import_export_service.py
# 导入导出核心业务逻辑（2026-01-03 最终版：独立目录 + 自动清理临时文件）

import os
import datetime
import pandas as pd
from flask import current_app
from flask_login import current_user
from werkzeug.utils import secure_filename
from repositories.person_repo import (
    get_all_people_for_export,
    bulk_insert_people
)
from repositories.building_repo import get_building_by_name_or_address
from permissions import check_user_grid_permission
from utils import logger

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_template_path(data_type: str) -> str:
    """返回模板文件路径（放在 static/templates/excel 下）"""
    base_dir = os.path.join(current_app.static_folder, 'templates', 'excel')
    templates = {
        'person': os.path.join(base_dir, '人员导入模板.xlsx'),
        # 可扩展其他类型
    }
    return templates.get(data_type)

def export_data_to_excel(data_type: str, user) -> tuple[str, str]:
    """导出数据到 Excel（使用独立的 exports 目录）"""
    exports_folder = current_app.config['EXPORTS_FOLDER']
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{data_type}_export_{timestamp}.xlsx"
    file_path = os.path.join(exports_folder, filename)

    try:
        if data_type == 'person':
            grid_ids = user.managed_grids if 'grid_user' in user.roles and not user.is_admin() else None
            data = get_all_people_for_export(grid_ids=grid_ids)
            df = pd.DataFrame(data)
            df = df[['name', 'id_card', 'phone', 'building_name', 'address', 'remarks']]
        else:
            raise ValueError('不支持的导出类型')

        df.to_excel(file_path, index=False, engine='openpyxl')
        logger.info(f"用户 {user.username} 导出 {data_type} 数据: {filename}")

        return file_path, filename

    except Exception as e:
        logger.error(f"导出失败: {e}")
        raise

def process_import_excel(file, data_type: str, user) -> tuple[bool, str]:
    """处理导入 Excel（使用独立的 imports 目录，并自动清理临时文件）"""
    imports_folder = current_app.config['IMPORTS_FOLDER']
    temp_path = None
    try:
        if not allowed_file(file.filename):
            return False, '只支持 .xlsx 或 .xls 文件'

        filename = secure_filename(file.filename)
        temp_path = os.path.join(imports_folder, filename)
        file.save(temp_path)

        if data_type != 'person':
            return False, '暂不支持该类型导入'

        df = pd.read_excel(temp_path, dtype=str)
        df = df.fillna('')

        required_columns = ['姓名', '身份证号', '联系电话', '居住小区/建筑']
        if not all(col in df.columns for col in required_columns):
            return False, 'Excel 模板列不匹配，请下载最新模板'

        success_count = 0
        fail_count = 0
        fail_reasons = []

        records = []

        for idx, row in df.iterrows():
            name = str(row['姓名']).strip()
            id_card = str(row['身份证号']).strip()
            phone = str(row['联系电话']).strip()
            building_name = str(row['居住小区/建筑']).strip()

            if not name or not id_card:
                fail_count += 1
                fail_reasons.append(f"第 {idx+2} 行：姓名或身份证为空")
                continue

            building = get_building_by_name_or_address(building_name)
            if not building:
                fail_count += 1
                fail_reasons.append(f"第 {idx+2} 行：未找到建筑 '{building_name}'")
                continue

            building_id = building['id']

            # 网格权限检查
            if not check_user_grid_permission(building_id):
                fail_count += 1
                fail_reasons.append(f"第 {idx+2} 行：无权操作该网格建筑 '{building_name}'")
                continue

            records.append({
                'name': name,
                'id_card': id_card,
                'phone': phone,
                'living_building_id': building_id,
                'address': str(row.get('详细地址', '')),
                'remarks': str(row.get('备注', ''))
            })

        if records:
            inserted = bulk_insert_people(records)
            success_count = inserted
            fail_count += len(records) - inserted

        msg = f'导入完成：成功 {success_count} 条，失败 {fail_count} 条'
        if fail_reasons:
            msg += f"<br>失败原因示例：{fail_reasons[0]}（查看日志获取全部）"

        logger.info(f"用户 {user.username} 导入人员：成功{success_count}，失败{fail_count}")

        return True, msg

    except Exception as e:
        logger.error(f"导入处理异常: {e}")
        return False, f'导入失败：{str(e)}'
    finally:
        # 关键：始终清理上传的临时 Excel 文件
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(f"清理导入临时文件: {temp_path}")
            except Exception as e:
                logger.warning(f"清理导入临时文件失败: {temp_path} - {e}")
