# repositories/building_repo.py
# 建筑数据访问层（完整最终版）

from .base import get_db_connection
from utils import logger


# ============================== 列表与查询 ==============================

def get_all_buildings(with_grid: bool = False):
    """
    获取所有建筑列表
    :param with_grid: 是否关联网格名称
    :return: list of dict
    """
    try:
        if with_grid:
            query = """
                SELECT b.*, g.name AS grid_name
                FROM building b
                LEFT JOIN grid g ON b.grid_id = g.id
                WHERE b.is_deleted = 0
                ORDER BY b.id DESC
            """
        else:
            query = """
                SELECT *
                FROM building
                WHERE is_deleted = 0
                ORDER BY b.id DESC
            """

        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        buildings = [dict(row) for row in rows]
        logger.info(f"加载建筑列表: {len(buildings)} 条")
        return buildings

    except Exception as e:
        logger.error(f"获取建筑列表失败: {e}")
        return []


def get_building_by_id(bid: int):
    """根据 ID 获取单个建筑详情（包含网格名称）"""
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT b.*, g.name AS grid_name
                FROM building b
                LEFT JOIN grid g ON b.grid_id = g.id
                WHERE b.id = ? AND b.is_deleted = 0
                """,
                (bid,)
            ).fetchone()
        return dict(row) if row else None

    except Exception as e:
        logger.error(f"获取建筑详情失败 (ID: {bid}): {e}")
        return None


def get_building_by_name_or_address(name_or_address: str):
    """模糊搜索建筑（用于导入匹配）"""
    try:
        search_like = f"%{name_or_address}%"
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM building
                WHERE (name LIKE ? OR address LIKE ?) AND is_deleted = 0
                ORDER BY id
                LIMIT 1
                """,
                (search_like, search_like)
            ).fetchone()
        return dict(row) if row else None

    except Exception as e:
        logger.error(f"模糊查找建筑失败 ({name_or_address}): {e}")
        return None


def get_building_id_by_name(name: str) -> int | None:
    """根据建筑名称精确获取 ID（导入备选方案）"""
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT id
                FROM building
                WHERE name = ? AND is_deleted = 0
                """,
                (name,)
            ).fetchone()
        return row['id'] if row else None

    except Exception as e:
        logger.error(f"根据名称获取建筑ID失败 ({name}): {e}")
        return None


# ============================== CRUD 操作 ==============================

def create_building(name: str, type_: str, grid_id: int = None) -> int:
    """新增建筑，返回新 ID"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO building (name, type, grid_id, is_deleted)
                VALUES (?, ?, ?, 0)
                """,
                (name, type_, grid_id)
            )
            conn.commit()
        logger.info(f"新增建筑成功: {name} (ID: {cursor.lastrowid})")
        return cursor.lastrowid

    except Exception as e:
        logger.error(f"新增建筑失败 ({name}): {e}")
        raise


def update_building(bid: int, name: str, type_: str, grid_id: int = None) -> bool:
    """更新建筑信息"""
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                UPDATE building
                SET name = ?, type = ?, grid_id = ?
                WHERE id = ?
                """,
                (name, type_, grid_id, bid)
            )
            conn.commit()
        logger.info(f"更新建筑成功 (ID: {bid})")
        return True

    except Exception as e:
        logger.error(f"更新建筑失败 (ID: {bid}): {e}")
        return False


def delete_building(bid: int) -> bool:
    """软删除建筑"""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE building SET is_deleted = 1 WHERE id = ?",
                (bid,)
            )
            conn.commit()
        logger.info(f"软删除建筑成功 (ID: {bid})")
        return True

    except Exception as e:
        logger.error(f"软删除建筑失败 (ID: {bid}): {e}")
        return False


# ============================== 统计与扩展 ==============================

def get_person_count_by_building(bid: int) -> int:
    """统计该建筑下居住人员数量"""
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM person p
                WHERE p.living_building_id = ? AND p.is_deleted = 0
                """,
                (bid,)
            ).fetchone()
        count = row['cnt'] if row else 0
        logger.info(f"建筑 {bid} 下人员数量: {count}")
        return count

    except Exception as e:
        logger.error(f"统计建筑人数失败 (ID: {bid}): {e}")
        return 0


# 预留：支持权限过滤的导出函数（未来与 import_export 模块配合）
def get_all_buildings_for_export(grid_ids: list = None):
    """
    获取用于导出的建筑数据（支持网格权限过滤）
    """
    try:
        with get_db_connection() as conn:
            query = """
                SELECT b.*, g.name AS grid_name
                FROM building b
                LEFT JOIN grid g ON b.grid_id = g.id
                WHERE b.is_deleted = 0
            """
            params = []

            if grid_ids is not None and grid_ids:
                placeholders = ','.join(['?' for _ in grid_ids])
                query += f" AND b.grid_id IN ({placeholders})"
                params.extend(grid_ids)

            query += " ORDER BY b.id"

            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"导出建筑查询失败: {e}")
        raise
