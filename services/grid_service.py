# services/grid_service.py
# 网格管理业务逻辑

from flask_login import current_user
from repositories.grid_repo import (
    get_grid_by_id,
    create_grid,
    update_grid,
    delete_grid,
    get_building_count_by_grid
)
from utils import logger

def create_grid(data: dict) -> tuple[bool, str]:
    """新增网格"""
    try:
        name = data.get('name', '').strip()
        manager_name = data.get('manager_name', '').strip()
        phone = data.get('phone', '').strip()

        if not name:
            return False, '网格名称不能为空'

        create_grid(name=name, manager_name=manager_name, phone=phone)

        logger.info(f"用户 {current_user.username} 新增网格: {name}")
        return True, '网格新增成功'

    except Exception as e:
        logger.error(f"新增网格失败: {e}")
        return False, '新增失败，请重试'

def update_grid(grid_id: int, data: dict) -> tuple[bool, str]:
    """编辑网格"""
    try:
        grid = get_grid_by_id(grid_id)
        if not grid:
            return False, '网格记录不存在'

        name = data.get('name', '').strip()
        manager_name = data.get('manager_name', '').strip()
        phone = data.get('phone', '').strip()

        if not name:
            return False, '网格名称不能为空'

        update_grid(grid_id, name=name, manager_name=manager_name, phone=phone)

        logger.info(f"用户 {current_user.username} 编辑网格 ID {grid_id}: {name}")
        return True, '网格信息更新成功'

    except Exception as e:
        logger.error(f"编辑网格失败 (ID: {grid_id}): {e}")
        return False, '更新失败，请重试'

def delete_grid(grid_id: int) -> tuple[bool, str]:
    """删除网格"""
    try:
        grid = get_grid_by_id(grid_id)
        if not grid:
            return False, '网格记录不存在'

        # 检查是否有建筑绑定
        building_count = get_building_count_by_grid(grid_id)
        if building_count > 0:
            return False, f'该网格下仍有 {building_count} 个建筑，无法删除'

        delete_grid(grid_id)

        logger.info(f"用户 {current_user.username} 删除网格 ID {grid_id}: {grid['name']}")
        return True, '网格删除成功'

    except Exception as e:
        logger.error(f"删除网格失败 (ID: {grid_id}): {e}")
        return False, '删除失败，请重试'
