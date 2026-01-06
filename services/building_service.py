# services/building_service.py
# 小区/建筑管理业务逻辑（优化版 - 代码更简洁、可读性提升、健壮性更强，功能完全不变）

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
        type_ = data.get('type', '').strip() or 'residential_complex'
        grid_id = data.get('grid_id')

        if not name:
            return False, '小区/建筑名称不能为空'
        if not type_:
            return False, '建筑类型不能为空'

        grid_id = _parse_grid_id(grid_id)
        if grid_id is not None and get_grid_by_id(grid_id) is None:
            return False, '选择的网格不存在'

        create_building(name=name, type_=type_, grid_id=grid_id)

        logger.info(f"用户 {current_user.username} 新增建筑: {name} (类型: {type_}, 网格ID: {grid_id})")
        return True, f'"{name}" 添加成功'

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
        type_ = data.get('type', '').strip() or building.get('type', 'residential_complex')
        grid_id = data.get('grid_id')

        if not name:
            return False, '小区/建筑名称不能为空'
        if not type_:
            return False, '建筑类型不能为空'

        grid_id = _parse_grid_id(grid_id)
        if grid_id is not None and get_grid_by_id(grid_id) is None:
            return False, '选择的网格不存在'

        update_building(building_id, name=name, type_=type_, grid_id=grid_id)

        logger.info(f"用户 {current_user.username} 编辑建筑 ID {building_id}（新名称: {name}）")
        return True, f'"{name}" 修改成功'

    except Exception as e:
        logger.error(f"编辑建筑失败 (ID: {building_id}): {e}")
        return False, '更新失败，请重试'


def delete_building(building_id: int) -> tuple[bool, str]:
    """删除建筑（软删除）"""
    try:
        building = get_building_by_id(building_id)
        if not building:
            return False, '建筑记录不存在'

        person_count = get_person_count_by_building(building_id)
        if person_count > 0:
            return False, f'该建筑下仍有 {person_count} 名人员居住，无法删除'

        delete_building(building_id)

        logger.info(f"用户 {current_user.username} 删除建筑 ID {building_id}: {building['name']}")
        return True, '建筑删除成功'

    except Exception as e:
        logger.error(f"删除建筑失败 (ID: {building_id}): {e}")
        return False, '删除失败，请重试'


# ======================== 辅助函数 ========================
def _parse_grid_id(grid_id) -> int | None:
    """安全解析网格ID（支持空字符串或None返回None）"""
    if not grid_id or grid_id == '':
        return None
    try:
        return int(grid_id)
    except (ValueError, TypeError):
        return None
