# services/import_export_person.py
# 人员专属导入导出逻辑（终极扩展版 - 2026-01-06）
# 新增：导入支持导出全部27个字段（宽松读取，无严格校验）
#       - 必填仍为：姓名、身份证号、联系电话、居住小区/建筑
#       - 其他字段可选存在即读取，缺失用默认值
#       - 建筑名称匹配 living_building_id 和 household_building_id
#       - 布尔字段宽松映射（1/是/True → 1，其他 → 0）
#       - 所有字段直接存（字符串为主，无格式校验）

import os
import pandas as pd
from datetime import datetime
from flask import current_app
from flask_login import current_user
from repositories.person_repo import get_all_people_for_export, bulk_insert_people
from repositories.building_repo import get_building_by_name_or_address
from permissions import check_user_grid_permission, get_user_grid_ids
from repositories.grid_repo import get_grid_by_id
from utils import logger
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from werkzeug.utils import secure_filename


# 布尔宽松映射（不加校验，直接判断是否像“是”）
def str_to_bool(val: str) -> int:
    val = str(val).strip().lower()
    return 1 if val in ['1', '是', 'true', 'yes', 'y'] else 0


def export_person_to_excel(user) -> tuple[str, str]:
    # 【导出逻辑保持不变 - 已完美】
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exports_dir = current_app.config['EXPORTS_FOLDER']
    os.makedirs(exports_dir, exist_ok=True)

    user_grid_ids = get_user_grid_ids(user)
    raw_data = get_all_people_for_export(grid_ids=user_grid_ids if user_grid_ids else None)

    filename_prefix = "人员数据"
    if user_grid_ids and len(user_grid_ids) == 1:
        grid = get_grid_by_id(user_grid_ids[0])
        grid_name = grid['name'] if grid else "未知网格"
        filename_prefix += f"_{grid_name}"

    headers = [
        '姓名', '身份证号', '性别', '出生日期', '联系电话', '现住小区/建筑', '门牌地址', '所属网格',
        '人员类型', '是否重点人员', '重点类别', '户籍小区/建筑', '户籍地址', '户编号',
        '是否人户分离', '实际居住地', '是否已迁出', '迁出日期', '迁往地', '是否已死亡', '死亡日期',
        '民族', '政治面貌', '婚姻状况', '文化程度', '工作学习情况', '健康状况', '备注'
    ]

    comments = [
        '必填，真实姓名', '必填，18位身份证', '男/女', '格式：YYYYMMDD', '多个电话用;分隔',
        '系统内小区名称', '必填，如1单元101室', '自动关联', '常住人口/流动人口', '1=是，0=否',
        '多个类别用,分隔，如独居老人,低保户', '本社区内户籍小区', '外地户籍填写完整地址', '如有则填写',
        '1=是，0=否', '人户分离时填写实际居住地址', '1=是，0=否', '格式：YYYYMMDD', '迁往省市区',
        '1=是，0=否', '格式：YYYYMMDD', '如汉族、回族等', '如中共党员、群众等', '未婚/已婚/离异/丧偶',
        '小学/初中/高中/本科等', '在职/退休/无业等', '健康/良好/残疾/疾病等', '其他补充信息'
    ]

    processed_data = []
    for item in raw_data:
        row = {
            '姓名': item.get('name', ''),
            '身份证号': item.get('id_card', ''),
            '性别': item.get('gender', ''),
            '出生日期': item.get('birth_date', ''),
            '联系电话': item.get('phones', ''),
            '现住小区/建筑': item.get('living_building_name', ''),
            '门牌地址': item.get('address_detail', ''),
            '所属网格': item.get('grid_name') or '无网格',
            '人员类型': item.get('person_type', ''),
            '是否重点人员': '是' if item.get('is_key_person') else '否',
            '重点类别': item.get('key_categories', ''),
            '户籍小区/建筑': item.get('household_building_name', ''),
            '户籍地址': item.get('household_address', ''),
            '户编号': item.get('household_number', ''),
            '是否人户分离': '是' if item.get('is_separated') else '否',
            '实际居住地': item.get('actual_residence', ''),
            '是否已迁出': '是' if item.get('has_moved_out') else '否',
            '迁出日期': item.get('move_out_date', ''),
            '迁往地': item.get('move_to', ''),
            '是否已死亡': '是' if item.get('is_deceased') else '否',
            '死亡日期': item.get('death_date', ''),
            '民族': item.get('ethnicity', ''),
            '政治面貌': item.get('political_status', ''),
            '婚姻状况': item.get('marital_status', ''),
            '文化程度': item.get('education', ''),
            '工作学习情况': item.get('employment_education', ''),
            '健康状况': item.get('health_condition', ''),
            '备注': item.get('notes', '')
        }
        processed_data.append(row)

    if not processed_data:
        processed_data = [dict.fromkeys(headers, '')]

    df = pd.DataFrame(processed_data)

    filename = f"{filename_prefix}_{timestamp}.xlsx"
    file_path = os.path.join(exports_dir, filename)

    wb = Workbook()
    ws = wb.active
    ws.title = 'Person'

    ws.append(headers)
    ws.append(comments)
    for r in dataframe_to_rows(df, index=False, header=False):
        ws.append(r)

    bold_font = Font(bold=True)
    center_align = Alignment(horizontal="center", vertical="center")
    wrap_align = Alignment(wrap_text=True)

    for cell in ws[1]:
        cell.font = bold_font
        cell.alignment = center_align
    for cell in ws[2]:
        cell.alignment = wrap_align

    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            if len(str(cell.value or "")) > max_length:
                max_length = len(str(cell.value))
        ws.column_dimensions[column].width = min(max_length + 2, 50)

    wb.save(file_path)
    logger.info(f"用户 {current_user.username} 导出人员数据: {filename}（共 {len(processed_data)} 条）")
    return file_path, filename


def import_person_from_excel(file, user) -> tuple[bool, str]:
    """扩展版：支持全部27字段导入（宽松、无校验）"""
    imports_folder = current_app.config['IMPORTS_FOLDER']
    temp_path = os.path.join(imports_folder, secure_filename(file.filename))
    file.save(temp_path)

    try:
        df = pd.read_excel(temp_path, dtype=str).fillna('')

        # 必填列检查（保持严格，避免垃圾数据）
        required_columns = ['姓名', '身份证号', '联系电话', '居住小区/建筑']
        actual_columns = [str(col).strip() for col in df.columns]
        missing = [col for col in required_columns if col not in actual_columns]
        if missing:
            return False, f'人员导入失败：缺少必填列 {", ".join(missing)}。<br>请下载最新模板并确保包含这些列。'

        records = []
        fail_reasons = []

        for idx, row in df.iterrows():
            # 核心必填
            name = str(row['姓名']).strip()
            id_card = str(row['身份证号']).strip()
            phones = str(row.get('联系电话', '')).strip()
            living_building_name = str(row['居住小区/建筑']).strip()

            if not name or not id_card:
                fail_reasons.append(f"第 {idx+2} 行：姓名或身份证为空")
                continue

            # 现住建筑匹配
            living_building = get_building_by_name_or_address(living_building_name)
            if not living_building:
                fail_reasons.append(f"第 {idx+2} 行：未找到现住建筑 '{living_building_name}'")
                continue

            if not check_user_grid_permission(living_building['id']):
                fail_reasons.append(f"第 {idx+2} 行：无权操作该网格建筑 '{living_building_name}'")
                continue

            # 户籍建筑匹配（可选）
            household_building_name = str(row.get('户籍小区/建筑', '')).strip()
            household_building_id = None
            if household_building_name:
                household_building = get_building_by_name_or_address(household_building_name)
                if household_building:
                    household_building_id = household_building['id']
                # 如果没找到也不报错，直接留空

            # 构建记录（所有字段宽松读取）
            record = {
                'name': name,
                'id_card': id_card,
                'phones': phones,
                'living_building_id': living_building['id'],
                'address_detail': str(row.get('门牌地址', '')).strip(),
                'notes': str(row.get('备注', '')).strip(),

                # 新增扩展字段（全部可选、无校验）
                'gender': str(row.get('性别', '')).strip(),
                'birth_date': str(row.get('出生日期', '')).strip(),
                'person_type': str(row.get('人员类型', '')).strip(),
                'is_key_person': str_to_bool(row.get('是否重点人员', '')),
                'key_categories': str(row.get('重点类别', '')).strip(),
                'household_building_id': household_building_id,
                'household_address': str(row.get('户籍地址', '')).strip(),
                'household_number': str(row.get('户编号', '')).strip(),
                'is_separated': str_to_bool(row.get('是否人户分离', '')),
                'actual_residence': str(row.get('实际居住地', '')).strip(),
                'has_moved_out': str_to_bool(row.get('是否已迁出', '')),
                'move_out_date': str(row.get('迁出日期', '')).strip(),
                'move_to': str(row.get('迁往地', '')).strip(),
                'is_deceased': str_to_bool(row.get('是否已死亡', '')),
                'death_date': str(row.get('死亡日期', '')).strip(),
                'ethnicity': str(row.get('民族', '')).strip(),
                'political_status': str(row.get('政治面貌', '')).strip(),
                'marital_status': str(row.get('婚姻状况', '')).strip(),
                'education': str(row.get('文化程度', '')).strip(),
                'employment_education': str(row.get('工作学习情况', '')).strip(),
                'health_condition': str(row.get('健康状况', '')).strip(),
            }

            records.append(record)

        # 批量插入（需确保 repositories/person_repo.py 的 bulk_insert_people 支持这些字段）
        success_count, errors = bulk_insert_people(records) if records else (0, [])
        fail_count = len(df) - success_count

        msg = f'人员导入完成：成功 {success_count} 条，失败 {fail_count} 条'
        all_errors = fail_reasons + errors
        if all_errors:
            sample = all_errors[:5]
            msg += f"<br>失败原因示例：{'；'.join(sample)}"
            if len(all_errors) > 5:
                msg += "（更多错误见服务器日志）"

        logger.info(f"用户 {user.username} 导入人员：成功 {success_count}，失败 {fail_count}")
        return True, msg

    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {temp_path} - {e}")
