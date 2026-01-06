# repositories/grid_repo.py
# 网格数据访问层（优化终极版 - 负责人显示修复：仅显示真实姓名或用户名，不带括号）

from .base import get_db_connection
from utils import logger
from typing import List, Dict, Optional


# ==================== 核心查询函数 ====================

def get_all_grids_with_managers_and_ids() -> List[Dict]:
    """
    获取所有网格列表（用于管理页面）
    - managers: 负责人显示字符串，如 "张三、李四、王五"（仅姓名，不带括号）
    - managers_ids: 逗号分隔的 user_id 字符串，用于编辑时预选复选框
    """
    query = """
        SELECT 
            g.id,
            g.name,
            g.is_deleted,
            COALESCE(GROUP_CONCAT(
                COALESCE(u.full_name, u.username)
            ), '') AS managers,
            GROUP_CONCAT(ug.user_id) AS managers_ids
        FROM grid g
        LEFT JOIN user_grid ug ON g.id = ug.grid_id
        LEFT JOIN user u ON ug.user_id = u.id AND u.is_deleted = 0
        GROUP BY g.id
        ORDER BY g.id ASC
    """

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        grids = [dict(row) for row in rows]
        for g in grids:
            g['managers'] = g['managers'] if g['managers'] else None
            g['managers_ids'] = g['managers_ids'] if g['managers_ids'] else ''

        logger.info(f"成功加载网格列表（带负责人信息）：共 {len(grids)} 条")
        return grids

    except Exception as e:
        logger.error(f"获取网格列表（带负责人ID）失败: {e}")
        return []


def get_grid_basic(grid_id: int) -> Optional[Dict]:
    """仅获取网格基本字段，用于存在性检查或简单引用"""
    query = "SELECT id, name, is_deleted FROM grid WHERE id = ?"

    try:
        with get_db_connection() as conn:
            row = conn.execute(query, (grid_id,)).fetchone()
        return dict(row) if row else None

    except Exception as e:
        logger.error(f"获取网格基本信息失败 (ID: {grid_id}): {e}")
        return None


def get_grid_by_id_with_stats(grid_id: int) -> Optional[Dict]:
    """
    获取网格完整信息（用于详情查看页）
    包含：负责人显示、建筑数量、居住人员数量
    """
    try:
        with get_db_connection() as conn:
            # 负责人显示字符串（仅姓名）
            managers_row = conn.execute("""
                SELECT COALESCE(GROUP_CONCAT(
                    COALESCE(u.full_name, u.username)
                ), '') AS managers
                FROM user_grid ug
                LEFT JOIN user u ON ug.user_id = u.id AND u.is_deleted = 0
                WHERE ug.grid_id = ?
            """, (grid_id,)).fetchone()

            managers = managers_row['managers'] if managers_row and managers_row['managers'] else None

            # 建筑数量统计
            building_count = conn.execute(
                "SELECT COUNT(*) FROM building WHERE grid_id = ? AND is_deleted = 0",
                (grid_id,)
            ).fetchone()[0]

            # 人员数量统计（通过建筑关联）
            person_count = conn.execute("""
                SELECT COUNT(*)
                FROM person p
                JOIN building b ON p.living_building_id = b.id
                WHERE b.grid_id = ? AND p.is_deleted = 0 AND b.is_deleted = 0
            """, (grid_id,)).fetchone()[0]

            # 基本信息
            basic = get_grid_basic(grid_id)
            if not basic:
                return None

            basic.update({
                'managers': managers,
                'building_count': building_count,
                'person_count': person_count
            })

            return basic

    except Exception as e:
        logger.error(f"获取网格完整信息失败 (ID: {grid_id}): {e}")
        return None


# ==================== CRUD 操作 ====================

def create_grid(name: str) -> int:
    """
    创建新网格
    
    Returns:
        int: 新网格的 ID
    """
    insert_sql = "INSERT INTO grid (name, is_deleted) VALUES (?, 0)"

    try:
        with get_db_connection() as conn:
            cursor = conn.execute(insert_sql, (name.strip(),))
            conn.commit()

        logger.info(f"创建网格成功: \"{name}\" (新ID: {cursor.lastrowid})")
        return cursor.lastrowid

    except Exception as e:
        logger.error(f"创建网格失败 (名称: \"{name}\"): {e}")
        raise


def update_grid(grid_id: int, name: str) -> bool:
    """更新网格名称"""
    update_sql = "UPDATE grid SET name = ? WHERE id = ?"

    try:
        with get_db_connection() as conn:
            result = conn.execute(update_sql, (name.strip(), grid_id))
            conn.commit()

        affected = result.rowcount > 0
        if affected:
            logger.info(f"更新网格成功 (ID: {grid_id} → 新名称: \"{name}\")")
        return affected

    except Exception as e:
        logger.error(f"更新网格失败 (ID: {grid_id}): {e}")
        return False


def toggle_grid_deleted(grid_id: int) -> int:
    """
    切换网格启用/禁用状态（软删除）
    
    Returns:
        int: 切换后的新状态 (0=启用, 1=禁用)
    """
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT is_deleted FROM grid WHERE id = ?", (grid_id,)).fetchone()
            if not row:
                raise ValueError("网格不存在")

            new_status = 1 - row['is_deleted']
            conn.execute("UPDATE grid SET is_deleted = ? WHERE id = ?", (new_status, grid_id))
            conn.commit()

        logger.info(f"网格状态切换成功 (ID: {grid_id} → {'禁用' if new_status else '启用'})")
        return new_status

    except Exception as e:
        logger.error(f"切换网格状态失败 (ID: {grid_id}): {e}")
        raise


# ==================== 兼容旧接口（保持原有调用不变） ====================

def get_all_grids(include_deleted: bool = False) -> List[Dict]:
    """获取网格列表（兼容旧代码）"""
    query = "SELECT id, name, is_deleted FROM grid"
    if not include_deleted:
        query += " WHERE is_deleted = 0"
    query += " ORDER BY id ASC"

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()
        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"获取网格列表失败: {e}")
        return []


def get_grid_by_id(grid_id: int) -> Optional[Dict]:
    """兼容旧接口：直接调用优化后的基本查询"""
    return get_grid_basic(grid_id)


def get_user_grid_ids(user) -> List[int]:
    """
    根据当前用户权限返回可访问的网格ID列表
    - 超级管理员或有全局权限：返回所有网格
    - 普通网格员：返回所属网格
    """
    if not (hasattr(user, 'is_authenticated') and user.is_authenticated):
        return []

    # 超级管理员或具备全局查看权限
    if getattr(user, 'role', None) == 'admin' or getattr(user, 'can_view_all_grids', False):
        grids = get_all_grids()
        return [g['id'] for g in grids]

    # 普通用户：仅返回自己负责的网格
    if getattr(user, 'grid_id', None):
        return [user.grid_id]

    return []
