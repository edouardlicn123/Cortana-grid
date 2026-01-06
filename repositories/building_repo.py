# repositories/building_repo.py
# 建筑数据访问层（优化终极版 - 功能完全不变，代码更健壮、可读、专业）

from .base import get_db_connection
from utils import logger


# ==================== 建筑类型映射 ====================
BUILDING_TYPE_MAP = {
    'residential_complex': '住宅小区',
    'commercial': '商业大厦',
    'large_rental': '公寓/大型出租房',
    'private_residence': '私人住宅',
    'public': '公共设施',
    'others': '其他'
}


def get_building_type_display(type_key: str | None) -> str:
    """
    将数据库中的类型键转换为前端友好的中文名称。

    Args:
        type_key: 数据库存储的类型键（如 'residential_complex'）

    Returns:
        str: 中文显示名称，未知时返回原值或“未知类型”
    """
    return BUILDING_TYPE_MAP.get(type_key or '', type_key or '未知类型')


# ============================== 列表与查询 ==============================

def get_all_buildings() -> list[dict]:
    """获取所有未软删除的建筑列表（包含网格名称与类型友好显示）"""
    query = """
        SELECT b.*, g.name AS grid_name
        FROM building b
        LEFT JOIN grid g ON b.grid_id = g.id
        WHERE b.is_deleted = 0
        ORDER BY b.id DESC
    """

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        buildings = [dict(row) for row in rows]

        for b in buildings:
            b['grid_name'] = b['grid_name'] or '无网格'
            b['type_display'] = get_building_type_display(b['type'])

        logger.info(f"成功加载建筑列表：共 {len(buildings)} 条")
        return buildings

    except Exception as e:
        logger.error(f"获取建筑列表失败: {e}")
        return []


def get_building_by_id(bid: int) -> dict | None:
    """根据 ID 获取单个建筑详情（包含网格名称与类型友好显示）"""
    query = """
        SELECT b.*, g.name AS grid_name
        FROM building b
        LEFT JOIN grid g ON b.grid_id = g.id
        WHERE b.id = ? AND b.is_deleted = 0
    """

    try:
        with get_db_connection() as conn:
            row = conn.execute(query, (bid,)).fetchone()

        if not row:
            return None

        building = dict(row)
        building['grid_name'] = building['grid_name'] or '无网格'
        building['type_display'] = get_building_type_display(building['type'])

        return building

    except Exception as e:
        logger.error(f"获取建筑详情失败 (ID: {bid}): {e}")
        return None


def get_building_by_name_or_address(name_or_address: str) -> dict | None:
    """模糊搜索建筑（用于导入数据时匹配已有建筑）"""
    search_pattern = f"%{name_or_address.strip()}%"

    query = """
        SELECT b.*, g.name AS grid_name
        FROM building b
        LEFT JOIN grid g ON b.grid_id = g.id
        WHERE (b.name LIKE ? OR b.address LIKE ?) AND b.is_deleted = 0
        ORDER BY b.id
        LIMIT 1
    """

    try:
        with get_db_connection() as conn:
            row = conn.execute(query, (search_pattern, search_pattern)).fetchone()

        if not row:
            return None

        building = dict(row)
        building['grid_name'] = building['grid_name'] or '无网格'
        building['type_display'] = get_building_type_display(building['type'])

        return building

    except Exception as e:
        logger.error(f"模糊搜索建筑失败 ({name_or_address}): {e}")
        return None


def get_buildings_for_select() -> list[dict]:
    """为前端下拉框提供建筑选项（格式：名称 (类型) - 网格）"""
    query = """
        SELECT b.id, b.name, b.type, g.name AS grid_name
        FROM building b
        LEFT JOIN grid g ON b.grid_id = g.id
        WHERE b.is_deleted = 0
        ORDER BY b.name
    """

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        options = []
        for row in rows:
            row_dict = dict(row)
            label = (f"{row_dict['name']} ({get_building_type_display(row_dict['type'])})"
                     f" - {row_dict['grid_name'] or '无网格'}")
            options.append({
                'id': row_dict['id'],
                'label': label
            })

        logger.debug(f"生成建筑下拉选项：{len(options)} 项")
        return options

    except Exception as e:
        logger.error(f"获取建筑下拉选项失败: {e}")
        return []


def get_building_id_by_name(name: str) -> int | None:
    """精确根据建筑名称获取 ID（导入时的备用匹配方案）"""
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT id FROM building WHERE name = ? AND is_deleted = 0",
                (name.strip(),)
            ).fetchone()
        return row['id'] if row else None

    except Exception as e:
        logger.error(f"根据名称获取建筑ID失败 ({name}): {e}")
        return None


# ============================== CRUD 操作 ==============================

def create_building(name: str, type_: str, grid_id: int | None = None) -> int:
    """
    新增建筑记录（仅核心字段必填，其余使用数据库默认值）
    
    Returns:
        int: 新建记录的 ID
    """
    insert_sql = """
        INSERT INTO building (
            name, type, grid_id
        ) VALUES (?, ?, ?)
    """

    try:
        with get_db_connection() as conn:
            cursor = conn.execute(insert_sql, (name.strip(), type_, grid_id))
            conn.commit()

        logger.info(f"新增建筑成功: \"{name}\" (类型: {type_}, 网格ID: {grid_id or '无'}, 新ID: {cursor.lastrowid})")
        return cursor.lastrowid

    except Exception as e:
        logger.error(f"新增建筑失败: 名称=\"{name}\", 类型={type_}, 网格ID={grid_id}, 错误: {e}")
        raise


def update_building(bid: int, name: str, type_: str, grid_id: int | None = None) -> bool:
    """更新建筑核心信息"""
    update_sql = """
        UPDATE building
        SET name = ?, type = ?, grid_id = COALESCE(?, grid_id)
        WHERE id = ?
    """

    try:
        with get_db_connection() as conn:
            conn.execute(update_sql, (name.strip(), type_, grid_id, bid))
            conn.commit()

        logger.info(f"更新建筑成功 (ID: {bid} → 新名称: \"{name}\")")
        return True

    except Exception as e:
        logger.error(f"更新建筑失败 (ID: {bid}): {e}")
        return False


def delete_building(bid: int) -> tuple[bool, str]:
    """软删除建筑（检查是否有居住人员）"""
    try:
        with get_db_connection() as conn:
            # 检查居住人数
            person_count = conn.execute(
                "SELECT COUNT(*) FROM person WHERE living_building_id = ? AND is_deleted = 0",
                (bid,)
            ).fetchone()[0]

            if person_count > 0:
                return False, f'该建筑下仍有 {person_count} 名人员居住，无法删除'

            # 执行软删除
            conn.execute("UPDATE building SET is_deleted = 1 WHERE id = ?", (bid,))
            conn.commit()

        logger.info(f"软删除建筑成功 (ID: {bid})")
        return True, '建筑删除成功'

    except Exception as e:
        logger.error(f"软删除建筑失败 (ID: {bid}): {e}")
        return False, '删除失败：系统异常'


# ============================== 统计与扩展 ==============================

def get_person_count_by_building(bid: int) -> int:
    """统计指定建筑下的居住人数"""
    try:
        with get_db_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM person WHERE living_building_id = ? AND is_deleted = 0",
                (bid,)
            ).fetchone()[0]
        return count
    except Exception as e:
        logger.error(f"统计建筑居住人数失败 (ID: {bid}): {e}")
        return 0


def get_all_buildings_for_export(grid_ids: list[int] | None = None) -> list[dict]:
    """导出建筑数据（支持按网格权限过滤）"""
    base_query = """
        SELECT b.*, g.name AS grid_name
        FROM building b
        LEFT JOIN grid g ON b.grid_id = g.id
        WHERE b.is_deleted = 0
    """
    params: list = []

    if grid_ids:
        placeholders = ','.join(['?' for _ in grid_ids])
        base_query += f" AND b.grid_id IN ({placeholders})"
        params = grid_ids

    base_query += " ORDER BY b.id"

    try:
        with get_db_connection() as conn:
            rows = conn.execute(base_query, params).fetchall()
        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"导出建筑数据失败: {e}")
        raise
