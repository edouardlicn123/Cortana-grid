# repositories/building_repo.py
# 建筑数据访问层（完整终极版 - 支持类型友好显示 + 导入匹配 + 下拉选项）

from .base import get_db_connection
from utils import logger


# 建筑类型映射字典（数据库键 → 前端显示名称）
BUILDING_TYPE_MAP = {
    'residential_complex': '住宅小区',
    'commercial': '商业大厦',
    'large_rental': '公寓/大型出租房',
    'private_residence': '私人住宅',
    'public': '公共设施',
    'others': '其他'
}

def get_building_type_display(type_key: str) -> str:
    """将数据库类型键转换为中文友好名称"""
    return BUILDING_TYPE_MAP.get(type_key, type_key or '未知类型')


# ============================== 列表与查询 ==============================

def get_all_buildings():
    """获取所有建筑列表（始终带网格名称和类型显示）"""
    try:
        query = """
            SELECT b.*, g.name AS grid_name
            FROM building b
            LEFT JOIN grid g ON b.grid_id = g.id
            WHERE b.is_deleted = 0
            ORDER BY b.id DESC
        """

        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        buildings = [dict(row) for row in rows]

        for b in buildings:
            # 网格名称处理
            if b['grid_name'] is None:
                b['grid_name'] = '无网格'
            # 类型友好显示
            b['type_display'] = get_building_type_display(b['type'])

        logger.info(f"加载建筑列表: {len(buildings)} 条")
        return buildings

    except Exception as e:
        logger.error(f"获取建筑列表失败: {e}")
        return []


def get_building_by_id(bid: int):
    """根据 ID 获取单个建筑详情（包含网格名称和类型显示）"""
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
        building = dict(row) if row else None
        if building:
            if building['grid_name'] is None:
                building['grid_name'] = '无网格'
            building['type_display'] = get_building_type_display(building['type'])
        return building

    except Exception as e:
        logger.error(f"获取建筑详情失败 (ID: {bid}): {e}")
        return None


def get_building_by_name_or_address(name_or_address: str):
    """模糊搜索建筑（用于导入时匹配建筑）"""
    try:
        search_like = f"%{name_or_address}%"
        with get_db_connection() as conn:
            row = conn.execute(
                """
                SELECT b.*, g.name AS grid_name
                FROM building b
                LEFT JOIN grid g ON b.grid_id = g.id
                WHERE (b.name LIKE ? OR b.address LIKE ?) AND b.is_deleted = 0
                ORDER BY b.id
                LIMIT 1
                """,
                (search_like, search_like)
            ).fetchone()
        building = dict(row) if row else None
        if building:
            building['grid_name'] = building['grid_name'] or '无网格'
            building['type_display'] = get_building_type_display(building['type'])
        return building

    except Exception as e:
        logger.error(f"模糊查找建筑失败 ({name_or_address}): {e}")
        return None


def get_buildings_for_select() -> list[dict]:
    """专门为人员新增/编辑页面提供建筑下拉选项（友好格式）"""
    try:
        query = """
            SELECT b.id, b.name, b.type, g.name AS grid_name
            FROM building b
            LEFT JOIN grid g ON b.grid_id = g.id
            WHERE b.is_deleted = 0
            ORDER BY b.name
        """

        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        options = []
        for row in rows:
            row_dict = dict(row)
            type_display = get_building_type_display(row_dict['type'])
            grid_display = row_dict['grid_name'] or '无网格'
            label = f"{row_dict['name']} ({type_display}) - {grid_display}"
            options.append({
                'id': row_dict['id'],
                'label': label
            })

        return options

    except Exception as e:
        logger.error(f"获取建筑下拉选项失败: {e}")
        return []


def get_building_id_by_name(name: str) -> int | None:
    """根据建筑名称精确获取 ID（导入备选方案）"""
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT id FROM building WHERE name = ? AND is_deleted = 0",
                (name,)
            ).fetchone()
        return row['id'] if row else None
    except Exception as e:
        logger.error(f"根据名称获取建筑ID失败 ({name}): {e}")
        return None


# ============================== CRUD 操作 ==============================

def create_building(name: str, type_: str, grid_id: int = None) -> int:
    """新增建筑 - 显式提供所有字段默认值"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO building (
                    name, type, grid_id, address, build_year, households, buildings_count,
                    approx_residents, businesses_count, ground_floor_shops, has_gas_pipeline,
                    property_fee, elevators, indoor_parking, outdoor_parking,
                    security_manager, security_manager_phone, latitude, longitude,
                    developer, constructor, property_management_company, property_contact_phone,
                    notes, owners_committee_contact, owners_committee_phone,
                    owner_name, owner_phone, landlord_name, landlord_phone,
                    commercial_type, is_external, is_deleted
                ) VALUES (
                    ?, ?, ?, '', NULL, NULL, NULL, NULL, NULL, NULL, 0,
                    '', NULL, NULL, NULL, '', '', NULL, NULL,
                    '', '', '', '', '', '', '', '', '', '', '', '', 0, 0
                )
                """,
                (name, type_, grid_id)
            )
            conn.commit()
        logger.info(f"新增建筑成功: {name} (类型: {type_}, 网格ID: {grid_id or '无'}, 新ID: {cursor.lastrowid})")
        return cursor.lastrowid

    except Exception as e:
        logger.error(f"新增建筑失败！名称: {name}, 类型: {type_}, 网格ID: {grid_id}, 错误: {type(e).__name__}: {e}")
        raise


def update_building(bid: int, name: str, type_: str, grid_id: int = None) -> bool:
    """更新建筑核心字段"""
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                UPDATE building
                SET name = ?, type = ?, grid_id = COALESCE(?, grid_id)
                WHERE id = ?
                """,
                (name, type_, grid_id, bid)
            )
            conn.commit()
        logger.info(f"更新建筑成功 (ID: {bid}, 新名称: {name})")
        return True
    except Exception as e:
        logger.error(f"更新建筑失败 (ID: {bid}): {e}")
        return False


def delete_building(bid: int) -> tuple[bool, str]:
    """软删除建筑"""
    try:
        with get_db_connection() as conn:
            person_count = conn.execute(
                "SELECT COUNT(*) FROM person WHERE living_building_id = ? AND is_deleted = 0",
                (bid,)
            ).fetchone()[0]

            if person_count > 0:
                return False, f'该建筑下仍有 {person_count} 名人员居住，无法删除'

            conn.execute("UPDATE building SET is_deleted = 1 WHERE id = ?", (bid,))
            conn.commit()
        logger.info(f"软删除建筑成功 (ID: {bid})")
        return True, '建筑删除成功'
    except Exception as e:
        logger.error(f"删除建筑失败 (ID: {bid}): {e}")
        return False, '删除失败'


# ============================== 统计与扩展 ==============================

def get_person_count_by_building(bid: int) -> int:
    """统计该建筑下居住人员数量"""
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM person WHERE living_building_id = ? AND is_deleted = 0",
                (bid,)
            ).fetchone()
        return row[0] if row else 0
    except Exception as e:
        logger.error(f"统计人数失败 (ID: {bid}): {e}")
        return 0


def get_all_buildings_for_export(grid_ids: list = None):
    """获取用于导出的建筑数据（支持网格权限过滤）"""
    try:
        with get_db_connection() as conn:
            query = """
                SELECT b.*, g.name AS grid_name
                FROM building b
                LEFT JOIN grid g ON b.grid_id = g.id
                WHERE b.is_deleted = 0
            """
            params = []
            if grid_ids:
                placeholders = ','.join(['?' for _ in grid_ids])
                query += f" AND b.grid_id IN ({placeholders})"
                params = grid_ids
            query += " ORDER BY b.id"
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"导出建筑失败: {e}")
        raise
