# services/person_service.py
# 人员业务层：新增/编辑核心逻辑（照片上传、校验、日志）

import os
from werkzeug.utils import secure_filename
from flask import current_app, flash
from flask_login import current_user
from repositories.person_repo import create_person, update_person, get_person_by_id
from utils import logger, allowed_file  # 确保 utils.py 有 allowed_file

MAX_PHOTOS = 3  # 最多允许上传照片数量

def process_person_form(form, files, person_id=None):
    """
    处理人员新增/编辑表单
    form: request.form
    files: request.files
    person_id: 编辑时传入
    返回 (success: bool, message: str)
    """
    try:
        # 注意：这里才访问 current_app（在函数运行时已有应用上下文）
        upload_folder = current_app.config['UPLOAD_FOLDER']

        # 1. 基本字段清洗
        data = {
            'name': form.get('name', '').strip(),
            'id_card': form.get('id_card', '').strip(),
            'phone': form.get('phone', '').strip(),
            'living_building_id': form.get('living_building_id'),
            'household_building_id': form.get('household_building_id'),
            'address': form.get('address', '').strip(),
            'remarks': form.get('remarks', '').strip(),
            'photos': ''
        }

        # 必填校验
        if not data['name']:
            return False, '姓名不能为空'
        if not data['id_card']:
            return False, '身份证号不能为空'

        # 建筑 ID 转换
        if data['living_building_id']:
            try:
                data['living_building_id'] = int(data['living_building_id'])
            except (ValueError, TypeError):
                return False, '居住建筑选择无效'
        else:
            data['living_building_id'] = None

        if data['household_building_id']:
            try:
                data['household_building_id'] = int(data['household_building_id'])
            except (ValueError, TypeError):
                data['household_building_id'] = None
        else:
            data['household_building_id'] = None

        # 2. 处理照片上传
        photo_filenames = []

        # 编辑时保留原有照片
        existing_photos = []
        if person_id:
            person = get_person_by_id(person_id)
            if person and person.get('photos'):
                existing_photos = [p.strip() for p in person['photos'].split(';') if p.strip()]

        # 新上传照片
        uploaded_files = files.getlist('photos')
        for file in uploaded_files:
            if file and file.filename:
                if not allowed_file(file.filename):
                    return False, '不支持的文件类型（仅限图片）'
                if len(existing_photos) + len(photo_filenames) >= MAX_PHOTOS:
                    return False, f'照片最多允许 {MAX_PHOTOS} 张'

                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                photo_filenames.append(filename)

        # 合并所有照片路径
        all_photos = existing_photos + photo_filenames
        data['photos'] = ';'.join(all_photos)

        # 3. 数据库操作
        if person_id:
            success = update_person(person_id, data)
            action = '编辑'
        else:
            create_person(data)
            success = True
            action = '新增'

        if not success and person_id:
            return False, '数据库更新失败'

        # 4. 操作日志
        logger.info(
            f"用户 {current_user.username} {action}人员: {data['name']} "
            f"(身份证: {data['id_card']}, ID: {person_id or '新'} )"
        )

        return True, f'人员{action}成功'

    except Exception as e:
        logger.error(f"人员表单处理异常 (person_id={person_id}): {e}")
        return False, '操作失败，请重试或联系管理员'
