# services/person_service.py
# 人员业务层：新增/编辑核心逻辑（照片上传、校验、日志）（优化版）

import os
from werkzeug.utils import secure_filename
from flask import current_app
from flask_login import current_user
from repositories.person_repo import create_person, update_person, get_person_by_id
from utils import logger, allowed_file  # 确保 utils.py 中定义了 allowed_file


MAX_PHOTOS = 3  # 最多允许上传的照片数量


def process_person_form(form, files, person_id: int | None = None) -> tuple[bool, str]:
    """
    处理人员新增/编辑表单（统一业务逻辑）

    Args:
        form: request.form
        files: request.files
        person_id: 编辑时传入的人员 ID，新增时为 None

    Returns:
        (success: bool, message: str)
    """
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)

        # ==================== 1. 提取并清洗基础字段 ====================
        data = {
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
            'notes': form.get('notes', '').strip(),
            'is_key_person': 'is_key_person' in form,
            'key_categories': ','.join(form.getlist('key_categories')),
            'photos': ''
        }

        # ==================== 2. 必填字段校验 ====================
        if not data['name']:
            return False, '姓名不能为空'
        if not data['id_card']:
            return False, '身份证号不能为空'
        if not data['living_building_id']:
            return False, '必须选择现住小区/建筑'
        if not data['address_detail']:
            return False, '现住详细门牌不能为空'

        # ==================== 3. 建筑 ID 安全转换 ====================
        try:
            data['living_building_id'] = int(data['living_building_id'])
        except (ValueError, TypeError):
            return False, '现住建筑选择无效'

        if data['household_building_id']:
            try:
                data['household_building_id'] = int(data['household_building_id'])
            except (ValueError, TypeError):
                data['household_building_id'] = None
        else:
            data['household_building_id'] = None

        # ==================== 4. 照片处理 ====================
        # 获取现有照片（编辑模式）
        existing_photos = []
        if person_id:
            person = get_person_by_id(person_id)
            if person and person.get('photos'):
                existing_photos = [p.strip() for p in person['photos'].split(';') if p.strip()]

        new_photos = []
        uploaded_files = files.getlist('photos')

        for file in uploaded_files:
            if file and file.filename:
                if not allowed_file(file.filename):
                    return False, '不支持的文件类型（仅支持图片格式）'

                if len(existing_photos) + len(new_photos) >= MAX_PHOTOS:
                    return False, f'照片最多允许上传 {MAX_PHOTOS} 张'

                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                new_photos.append(filename)

        # 合并照片路径
        all_photos = existing_photos + new_photos
        data['photos'] = ';'.join(all_photos[:MAX_PHOTOS])  # 保险起见再截断

        # ==================== 5. 数据库操作 ====================
        if person_id:
            update_person(person_id, **data)
            action = '编辑'
            log_id = person_id
        else:
            create_person(**data)
            action = '新增'
            log_id = '新记录'

        logger.info(
            f"用户 {current_user.username} {action}人员: {data['name']} "
            f"(身份证: {data['id_card']}, 人员ID: {log_id})"
        )

        return True, f'人员{action}成功'

    except Exception as e:
        logger.error(f"人员表单处理异常 (person_id={person_id}): {e}")
        return False, '操作失败，请重试或联系管理员'
