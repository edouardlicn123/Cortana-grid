# repositories/person_repo.py
# 人员数据访问层（完整版）

from .base import get_db_connection
from utils import logger


# ============================== 列表与分页 ==============================

def get_all_persons(search=None, page=1, per_page=20):
    """
    获取人员列表（支持搜索和分页）
    返回: list of dict, total_count
    """
    try:
        offset = (page - 1) * per_page
        query = """
            SELECT 
                p.id,
                p.name,
                p.id_card,
                p.address_detail,
                p.updated_at,
                b.name AS building_name,
                g.name AS grid_name
            FROM person p
            LEFT JOIN building b ON p.living_building_id = b.id
            LEFT JOIN grid g ON b.grid_id = g.id
            WHERE p.is_deleted = 0
        """
        params = []
        count_query = "SELECT COUNT(*) FROM person p WHERE p.is_deleted = 0"

        if search:
            search_like = f"%{search}%"
            query += " AND (p.name LIKE ? OR p.id_card LIKE ?)"
            count_query += " AND (p.name LIKE ? OR p.id_card LIKE ?)"
            params.extend([search_like, search_like])

        with get_db_connection() as conn:
            total = conn.execute(count_query, params[:2] if search else []).fetchone()[0]

            query += " ORDER BY p.updated_at DESC LIMIT ? OFFSET ?"
            params.extend([per_page, offset])

            rows = conn.execute(query, params).fetchall()

        persons = [dict(row) for row in rows]
        logger.info(f"加载人员列表: {len(persons)} 条，总计 {total} 条")
        return persons, total

    except Exception as e:
        logger.error(f"获取人员列表失败: {e}")
        return [], 0


def get_people_paginated(page=1, per_page=20, search=None):
    """
    获取人员分页列表（兼容旧调用）
    返回: persons (list), total_pages (int)
    """
    persons, total = get_all_persons(search=search, page=page, per_page=per_page)
    total_pages = (total + per_page - 1) // per_page if total else 1
    return persons, total_pages


# ============================== 概览统计 ==============================

def get_overview_stats():
    """
    获取首页概览统计数据
    """
    try:
        with get_db_connection() as conn:
            stats = {
                'total_persons': conn.execute(
                    "SELECT COUNT(*) FROM person WHERE is_deleted = 0"
                ).fetchone()[0],
                'total_buildings': conn.execute(
                    "SELECT COUNT(*) FROM building WHERE is_deleted = 0"
                ).fetchone()[0],
                'total_grids': conn.execute(
                    "SELECT COUNT(*) FROM grid WHERE is_deleted = 0"
                ).fetchone()[0],
                'key_persons': conn.execute(
                    "SELECT COUNT(*) FROM person WHERE is_deleted = 0 AND is_key_person = 1"
                ).fetchone()[0]
            }
            logger.info(f"概览统计加载成功: {stats}")
            return stats
    except Exception as e:
        logger.error(f"概览统计加载失败: {e}")
        return {'total_persons': 0, 'total_buildings': 0, 'total_grids': 0, 'key_persons': 0}


# ============================== 单个人员操作 ==============================

def get_person_by_id(person_id: int):
    """根据 ID 获取单个人员详情"""
    try:
        with get_db_connection() as conn:
            row = conn.execute("""
                SELECT 
                    p.*,
                    b.name AS building_name,
                    g.name AS grid_name
                FROM person p
                LEFT JOIN building b ON p.living_building_id = b.id
                LEFT JOIN grid g ON b.grid_id = g.id
                WHERE p.id = ? AND p.is_deleted = 0
            """, (person_id,)).fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"获取人员详情失败 ID {person_id}: {e}")
        return None


def create_person(person_data: dict):
    """创建新人员"""
    try:
        with get_db_connection() as conn:
            columns = ', '.join(person_data.keys())
            placeholders = ', '.join('?' for _ in person_data)
            query = f"INSERT INTO person ({columns}) VALUES ({placeholders})"
            cursor = conn.execute(query, tuple(person_data.values()))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"创建人员失败: {e}")
        raise


def update_person(person_id: int, person_data: dict):
    """更新人员信息"""
    try:
        with get_db_connection() as conn:
            set_clause = ', '.join(f"{k} = ?" for k in person_data.keys())
            query = f"UPDATE person SET {set_clause} WHERE id = ?"
            conn.execute(query, tuple(person_data.values()) + (person_id,))
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"更新人员失败 ID {person_id}: {e}")
        raise


def delete_person(person_id: int):
    """软删除人员"""
    try:
        with get_db_connection() as conn:
            conn.execute("UPDATE person SET is_deleted = 1 WHERE id = ?", (person_id,))
            conn.commit()
            return True, "删除成功"
    except Exception as e:
        logger.error(f"删除人员失败 ID {person_id}: {e}")
        return False, "删除失败"


# ============================== 导出 ==============================

def get_all_people_for_export(grid_ids: list = None):
    """
    获取用于导出的人员数据（支持网格权限过滤）
    """
    try:
        with get_db_connection() as conn:
            query = """
                SELECT p.*, b.name as building_name, g.name as grid_name
                FROM person p
                LEFT JOIN building b ON p.living_building_id = b.id
                LEFT JOIN grid g ON b.grid_id = g.id
                WHERE p.is_deleted = 0
            """
            params = []

            if grid_ids is not None and grid_ids:
                placeholders = ','.join(['?' for _ in grid_ids])
                query += f" AND b.grid_id IN ({placeholders})"
                params.extend(grid_ids)

            query += " ORDER BY p.id"

            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"导出人员查询失败: {e}")
        raise


# ============================== 批量导入 ==============================

def bulk_insert_people(people_data: list[dict]):
    """
    批量插入人员数据（导入用）
    使用 INSERT OR IGNORE 避免重复
    返回: 成功数, 失败数
    """
    if not people_data:
        return 0, 0

    try:
        with get_db_connection() as conn:
            sample = people_data[0]
            columns = ', '.join(sample.keys())
            placeholders = ', '.join('?' for _ in sample)
            query = f"INSERT OR IGNORE INTO person ({columns}) VALUES ({placeholders})"

            values_list = [tuple(d.get(k) for k in sample.keys()) for d in people_data]

            cursor = conn.executemany(query, values_list)
            conn.commit()

            inserted = cursor.rowcount
            logger.info(f"批量插入人员成功: {inserted} 条")
            return inserted, len(people_data) - inserted

    except Exception as e:
        logger.error(f"批量插入人员失败: {e}")
        return 0, len(people_data)
