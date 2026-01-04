# repositories/person_repo.py
# 新增函数：获取人员列表（用于独立列表页）

from .base import get_db_connection
from utils import logger

# 已有函数保持不变（get_person_by_id 等）

def get_all_persons(search=None, page=1, per_page=20):
    """
    获取人员列表（支持搜索和分页）
    - search: 搜索姓名或身份证号
    - page/per_page: 分页参数
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

        if search:
            search_like = f"%{search}%"
            query += " AND (p.name LIKE ? OR p.id_card LIKE ?)"
            params.extend([search_like, search_like])

        # 总数查询
        count_query = query.replace("SELECT p.id, ...", "SELECT COUNT(*)")
        with get_db_connection() as conn:
            total = conn.execute(count_query, params).fetchone()[0]

            query += " ORDER BY p.updated_at DESC LIMIT ? OFFSET ?"
            params.extend([per_page, offset])

            rows = conn.execute(query, params).fetchall()

        persons = [dict(row) for row in rows]
        logger.info(f"加载人员列表: {len(persons)} 条，总计 {total} 条")
        return persons, total

    except Exception as e:
        logger.error(f"获取人员列表失败: {e}")
        return [], 0


# 新增：概览统计函数（用于首页 /overview）


def get_overview_stats():
    """
    获取首页概览统计数据
    返回 dict 包含：
    - total_persons: 总人数
    - total_buildings: 总建筑数
    - total_grids: 总网格数
    - key_persons: 重点人员数
    """
    try:
        with get_db_connection() as conn:
            stats = {}

            # 总人数（未删除）
            stats['total_persons'] = conn.execute(
                "SELECT COUNT(*) FROM person WHERE is_deleted = 0"
            ).fetchone()[0]

            # 总建筑数
            stats['total_buildings'] = conn.execute(
                "SELECT COUNT(*) FROM building WHERE is_deleted = 0"
            ).fetchone()[0]

            # 总网格数（未禁用）
            stats['total_grids'] = conn.execute(
                "SELECT COUNT(*) FROM grid WHERE is_deleted = 0"
            ).fetchone()[0]

            # 重点人员数
            stats['key_persons'] = conn.execute(
                "SELECT COUNT(*) FROM person WHERE is_deleted = 0 AND is_key_person = 1"
            ).fetchone()[0]

            logger.info(f"概览统计加载成功: {stats}")
            return stats

    except Exception as e:
        logger.error(f"概览统计加载失败: {e}")
        # 返回默认0，避免页面崩溃
        return {
            'total_persons': 0,
            'total_buildings': 0,
            'total_grids': 0,
            'key_persons': 0
        }

# 新增：人员分页查询函数（用于管理列表页或独立列表页）
def get_people_paginated(page=1, per_page=20, search=None):
    """
    获取人员分页列表（支持搜索）
    - page: 当前页
    - per_page: 每页条数
    - search: 搜索关键词（姓名或身份证号）
    返回: persons (list), total_pages (int)
    """
    try:
        offset = (page - 1) * per_page

        base_query = """
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

        if search:
            search_like = f"%{search}%"
            base_query += " AND (p.name LIKE ? OR p.id_card LIKE ?)"
            params.extend([search_like, search_like])

        # 总数
        count_query = base_query.replace("SELECT p.id, ...", "SELECT COUNT(*)")
        with get_db_connection() as conn:
            total = conn.execute(count_query, params).fetchone()[0]

        # 数据
        query = base_query + " ORDER BY p.updated_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        rows = conn.execute(query, params).fetchall()

        persons = [dict(row) for row in rows]
        total_pages = (total + per_page - 1) // per_page if total else 1

        logger.info(f"分页加载人员: {len(persons)} 条，总页数: {total_pages}")
        return persons, total_pages

    except Exception as e:
        logger.error(f"分页加载人员失败: {e}")
        return [], 1

# 人员数据访问层（补全核心函数）

# 已有函数保持不变（如 get_all_persons, get_people_paginated, get_overview_stats 等）

# 单人查询
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

# 创建人员（基础版，返回新 ID）
def create_person(person_data: dict):
    """创建新人员记录"""
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

# 更新人员
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

# 删除人员（软删除）
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

# repositories/person_repo.py
# 新增：导出所有人员数据（用于导入导出模块）

def get_all_people_for_export():
    """
    获取所有人员数据用于导出（包含所有字段，不分页）
    返回 list of dict
    """
    try:
        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT 
                    p.*,
                    b.name AS building_name,
                    g.name AS grid_name
                FROM person p
                LEFT JOIN building b ON p.living_building_id = b.id
                LEFT JOIN grid g ON b.grid_id = g.id
                WHERE p.is_deleted = 0
                ORDER BY p.id ASC
            """).fetchall()

        people = [dict(row) for row in rows]
        logger.info(f"导出人员数据: {len(people)} 条")
        return people

    except Exception as e:
        logger.error(f"获取导出人员数据失败: {e}")
        return []

# repositories/person_repo.py
# 新增：批量插入人员（用于导入功能）

def bulk_insert_people(people_data: list[dict]):
    """
    批量插入人员数据
    - people_data: list of dict，每项包含人员字段
    返回: 成功插入条数, 失败条数
    """
    if not people_data:
        return 0, 0

    try:
        with get_db_connection() as conn:
            # 动态构建插入语句
            sample = people_data[0]
            columns = ', '.join(sample.keys())
            placeholders = ', '.join('?' for _ in sample)
            query = f"INSERT OR IGNORE INTO person ({columns}) VALUES ({placeholders})"

            values_list = [tuple(d.values()) for d in people_data]

            cursor = conn.executemany(query, values_list)
            conn.commit()

            inserted = cursor.rowcount
            logger.info(f"批量插入人员成功: {inserted} 条")
            return inserted, len(people_data) - inserted

    except Exception as e:
        logger.error(f"批量插入人员失败: {e}")
        return 0, len(people_data)
