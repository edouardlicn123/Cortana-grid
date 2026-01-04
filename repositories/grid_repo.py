# repositories/grid_repo.py
# 网格数据访问层（最终完整版 - 支持负责人显示 + ID列表 + 统计 + 禁用切换）

from .base import get_db_connection
from utils import logger

# ==================== 获取所有网格（用于列表页，带负责人显示和ID列表） ====================
def get_all_grids_with_managers_and_ids():
    """
    获取所有网格列表
    - managers: 用于显示的字符串（姓名 (用户名)）
    - managers_ids: 逗号分隔的 user_id 字符串，用于编辑模态框预勾选
    """
    query = """
        SELECT 
            g.id,
            g.name,
            g.is_deleted,
            COALESCE(GROUP_CONCAT(
                COALESCE(u.full_name || ' (' || u.username || ')', u.username)
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
        return grids
    except Exception as e:
        logger.error(f"获取网格列表（带负责人ID）失败: {e}")
        return []

# ==================== 简单获取网格基本信息（用于存在性检查） ====================
def get_grid_basic(grid_id: int):
    """仅获取基本字段，用于存在性检查和虚拟网格判断"""
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT id, name, is_deleted FROM grid WHERE id = ?",
                (grid_id,)
            ).fetchone()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"获取网格基本信息失败 ID {grid_id}: {e}")
        return None

# ==================== 获取完整网格信息（带负责人和统计，用于查看页） ====================
def get_grid_by_id_with_stats(grid_id: int):
    """用于查看页：负责人 + 建筑数 + 人员数"""
    try:
        with get_db_connection() as conn:
            # 负责人显示字符串
            managers_row = conn.execute("""
                SELECT COALESCE(GROUP_CONCAT(
                    COALESCE(u.full_name || ' (' || u.username || ')', u.username)
                ), '') AS managers
                FROM user_grid ug
                LEFT JOIN user u ON ug.user_id = u.id AND u.is_deleted = 0
                WHERE ug.grid_id = ?
            """, (grid_id,)).fetchone()
            managers = managers_row['managers'] if managers_row and managers_row['managers'] else None

            # 建筑统计
            building_count = conn.execute(
                "SELECT COUNT(*) FROM building WHERE grid_id = ? AND is_deleted = 0",
                (grid_id,)
            ).fetchone()[0]

            # 人员统计
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

            basic['managers'] = managers
            basic['building_count'] = building_count
            basic['person_count'] = person_count
            return basic
    except Exception as e:
        logger.error(f"获取网格完整信息失败 ID {grid_id}: {e}")
        return None

# ==================== 创建 / 更新 / 切换 ====================
def create_grid(name: str):
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO grid (name, is_deleted) VALUES (?, 0)", (name,))
            conn.commit()
    except Exception as e:
        logger.error(f"创建网格失败: {e}")
        raise

def update_grid(grid_id: int, name: str):
    try:
        with get_db_connection() as conn:
            conn.execute("UPDATE grid SET name = ? WHERE id = ?", (name, grid_id))
            conn.commit()
    except Exception as e:
        logger.error(f"更新网格失败: {e}")
        raise

def toggle_grid_deleted(grid_id: int) -> int:
    try:
        with get_db_connection() as conn:
            current = conn.execute("SELECT is_deleted FROM grid WHERE id = ?", (grid_id,)).fetchone()
            if not current:
                raise ValueError("网格不存在")
            new_status = 1 - current['is_deleted']
            conn.execute("UPDATE grid SET is_deleted = ? WHERE id = ?", (new_status, grid_id))
            conn.commit()
            return new_status
    except Exception as e:
        logger.error(f"切换网格状态失败: {e}")
        raise

# ==================== 兼容旧接口 ====================
def get_all_grids(include_deleted=False):
    query = "SELECT id, name, is_deleted FROM grid"
    if not include_deleted:
        query += " WHERE is_deleted = 0"
    query += " ORDER BY id ASC"
    try:
        with get_db_connection() as conn:
            return [dict(r) for r in conn.execute(query).fetchall()]
    except Exception as e:
        logger.error(f"获取网格列表失败: {e}")
        return []

def get_grid_by_id(grid_id: int):
    return get_grid_basic(grid_id)
