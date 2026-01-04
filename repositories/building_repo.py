# repositories/building_repo.py
# 建筑数据访问层：所有对 building 表的操作集中于此（完整最终版）

from .base import get_db_connection
from utils import logger

def get_all_buildings(with_grid=False):
    """获取所有建筑列表"""
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
                FROM building b
                WHERE b.is_deleted = 0
                ORDER BY b.id DESC
            """

        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()
        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"获取建筑列表失败: {e}")
        return []


def get_building_by_id(bid: int):
    """根据 ID 获取单个建筑"""
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
    """模糊查找建筑（用于导入匹配）"""
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM building
                WHERE (name LIKE ? OR address LIKE ?) AND is_deleted = 0
                ORDER BY id
                LIMIT 1
                """,
                (f'%{name_or_address}%', f'%{name_or_address}%')
            ).fetchone()
        return dict(row) if row else None

    except Exception as e:
        logger.error(f"查找建筑失败 ({name_or_address}): {e}")
        return None


def get_building_id_by_name(name: str) -> int | None:
    """根据建筑名称精确获取 ID（导入时备选）"""
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


def create_building(name: str, type_: str, grid_id: int = None):
    """新增建筑"""
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
        return cursor.lastrowid

    except Exception as e:
        logger.error(f"新增建筑失败: {e}")
        raise


def update_building(bid: int, name: str, type_: str, grid_id: int = None):
    """更新建筑"""
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
        return True

    except Exception as e:
        logger.error(f"更新建筑失败 (ID: {bid}): {e}")
        return False


def delete_building(bid: int):
    """软删除建筑"""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE building SET is_deleted = 1 WHERE id = ?",
                (bid,)
            )
            conn.commit()
        return True

    except Exception as e:
        logger.error(f"删除建筑失败 (ID: {bid}): {e}")
        return False


def get_person_count_by_building(bid: int) -> int:
    """统计建筑下人员数量"""
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
        return row['cnt'] if row else 0

    except Exception as e:
        logger.error(f"统计建筑人数失败 (ID: {bid}): {e}")
        return 0
