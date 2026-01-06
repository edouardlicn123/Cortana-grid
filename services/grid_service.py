# services/grid_service.py
# 网格管理业务逻辑（优化版 - 代码更简洁、可读性提升、健壮性更强，功能完全不变）

from flask_login import current_user
from repositories.grid_repo import (
    get_grid_basic,          # 使用更轻量的基本查询
    create_grid,
    update_grid,
    toggle_grid_deleted,     # 当前实际删除使用软删除
    get_building_count_by_grid
)
from utils import logger


def create_grid(data: dict) -> tuple[bool, str]:
    """新增网格"""
    try:
        name = data.get('name', '').strip()

        if not name:
            return False, '网格名称不能为空'

        if len(name) > 50:
            return False, '网格名称不能超过50个字符'

        create_grid(name=name)

        logger.info(f"用户 {current_user.username} 新增网格: {name}")
        return True, f'网格 "{name}" 添加成功'

    except Exception as e:
        logger.error(f"新增网格失败: {e}")
        return False, '新增失败，请重试'


def update_grid(grid_id: int, data: dict) -> tuple[bool, str]:
    """编辑网格（仅支持名称修改，负责人分配已移至系统设置）"""
    try:
        grid = get_grid_basic(grid_id)
        if not grid:
            return False, '网格不存在'

        if grid['name'].startswith('虚拟网格'):
            return False, '系统内置网格不可编辑'

        if grid['is_deleted']:
            return False, '已禁用的网格不可编辑'

        name = data.get('name', '').strip()

        if not name:
            return False, '网格名称不能为空'

        if len(name) > 50:
            return False, '网格名称不能超过50个字符'

        update_grid(grid_id, name)

        logger.info(f"用户 {current_user.username} 编辑网格 ID {grid_id}（新名称: {name}）")
        return True, f'网格 "{name}" 修改成功'

    except Exception as e:
        logger.error(f"编辑网格失败 (ID: {grid_id}): {e}")
        return False, '更新失败，请重试'


def delete_grid(grid_id: int) -> tuple[bool, str]:
    """删除网格（实际为软删除）"""
    try:
        grid = get_grid_basic(grid_id)
        if not grid:
            return False, '网格不存在'

        if grid['name'].startswith('虚拟网格'):
            return False, '系统内置网格不可删除'

        # 检查是否有建筑绑定
        building_count = get_building_count_by_grid(grid_id)
        if building_count > 0:
            return False, f'该网格下仍有 {building_count} 个建筑，无法删除'

        new_status = toggle_grid_deleted(grid_id)
        action = '禁用' if new_status else '启用'  # 当前删除等同于禁用
        logger.info(f"用户 {current_user.username} {action}网格 ID {grid_id}: {grid['name']}")
        return True, f'网格 "{grid['name']}" 已{action}'

    except Exception as e:
        logger.error(f"删除网格失败 (ID: {grid_id}): {e}")
        return False, '删除失败，请重试'
