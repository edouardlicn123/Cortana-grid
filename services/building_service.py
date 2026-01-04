# services/building_service.py
# 小区/建筑管理业务逻辑

from flask_login import current_user
from repositories.building_repo import (
    get_building_by_id,
    create_building,
    update_building,
    delete_building,
    get_person_count_by_building
)
from repositories.grid_repo import get_grid_by_id
from utils import logger

def create_building(data: dict) -> tuple[bool, str]:
    """新增建筑"""
    try:
        name = data.get('name', '').strip()
        type_ = data.get('type', '').strip()
        grid_id = data.get('grid_id')

        if not name or not type_:
            return False, '建筑名称和类型不能为空'

        if grid_id:
            grid_id = int(grid_id)
            if not get_grid_by_id(grid_id):
                return False, '选择的网格不存在'
        else:
            grid_id = None

        create_building(name=name, type_=type_, grid_id=grid_id)

        logger.info(f"用户 {current_user.username} 新增建筑: {name} (类型: {type_}, 网格ID: {grid_id})")
        return True, '建筑新增成功'

    except Exception as e:
        logger.error(f"新增建筑失败: {e}")
        return False, '新增失败，请重试'

def update_building(building_id: int, data: dict) -> tuple[bool, str]:
    """编辑建筑"""
    try:
        building = get_building_by_id(building_id)
        if not building:
            return False, '建筑记录不存在'

        name = data.get('name', '').strip()
        type_ = data.get('type', '').strip()
        grid_id = data.get('grid_id')

        if not name or not type_:
            return False, '建筑名称和类型不能为空'

        if grid_id != '':
            grid_id = int(grid_id)
            if not get_grid_by_id(grid_id):
                return False, '选择的网格不存在'
        else:
            grid_id = None

        update_building(building_id, name=name, type_=type_, grid_id=grid_id)

        logger.info(f"用户 {current_user.username} 编辑建筑 ID {building_id}: {name}")
        return True, '建筑信息更新成功'

    except Exception as e:
        logger.error(f"编辑建筑失败 (ID: {building_id}): {e}")
        return False, '更新失败，请重试'

def delete_building(building_id: int) -> tuple[bool, str]:
    """删除建筑（软删除或硬删除，根据 repo 实现）"""
    try:
        building = get_building_by_id(building_id)
        if not building:
            return False, '建筑记录不存在'

        # 检查是否有人员居住
        person_count = get_person_count_by_building(building_id)
        if person_count > 0:
            return False, f'该建筑下仍有 {person_count} 名人员居住，无法删除'

        delete_building(building_id)

        logger.info(f"用户 {current_user.username} 删除建筑 ID {building_id}: {building['name']}")
        return True, '建筑删除成功'

    except Exception as e:
        logger.error(f"删除建筑失败 (ID: {building_id}): {e}")
        return False, '删除失败，请重试'
