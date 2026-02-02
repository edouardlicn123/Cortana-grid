# repositories/building_repo.py
# 文件功能说明：
#   - 建筑数据访问层（Repository 层核心模块）
#   - 核心职责：
#       • 提供建筑数据的完整 CRUD 操作（新增、查询、更新、软删除）
#       • 支持网格关联查询与友好显示（网格名称、建筑类型中文映射）
#       • 为前端提供下拉选项数据（人员编辑时选择居住建筑）
#       • 支持模糊搜索与名称精确匹配（主要用于 Excel 导入时的建筑自动关联）
#       • 提供首页概览统计所需数据（通过 get_overview_stats 调用）
#       • 仪表盘专用统计查询（v2.3 新增）：
#           - 建筑类型分布统计（用于环形图/饼图）
#       • 导出专用全量数据查询（支持按网格权限过滤）
#       • 单体建筑居住人数统计（用于建筑详情页显示当前居住人数）
#   - 所有查询统一使用字典行工厂（dict_row_factory），返回标准 dict 结构
#   - 全面异常处理 + 日志记录（使用 utils.logger），确保生产环境健壮性
#   - 关键设计原则：
#       • 软删除机制（is_deleted = 1）
#       • 类型映射友好显示（BUILDING_TYPE_MAP）
#       • 支持动态字段更新（update_building）
#       • 网格权限过滤（导出时使用）
#   - 依赖：
#       • repositories.base → get_db_connection
#       • utils → logger
#   - 版本：v2.3（仪表盘增强版）
#   - 更新历史：
#       • 2026-02-02：新增 get_building_count_by_type（仪表盘建筑类型分布）
#       • 2026-02-02：新增 get_person_count_by_building（建筑居住人数统计）
#       • 2026-02-02：修复 typing 导入，补充更多类型注解
#       • 2026-02-02：完善函数文档字符串与日志信息
#       • 2026-02-02：修复 get_buildings_for_select 中的 f-string 括号匹配问题

from .base import get_db_connection
from utils import logger
from typing import List, Dict, Optional, Tuple, Any


# ==================== 建筑类型映射（用于前端友好显示） ====================
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
    将数据库中的建筑类型键转换为前端友好的中文名称。
    
    Args:
        type_key: 数据库存储的类型键（如 'residential_complex'）
    
    Returns:
        str: 中文显示名称，若无映射则返回原值或 '未知类型'
    """
    return BUILDING_TYPE_MAP.get(type_key or '', type_key or '未知类型')


# ============================== 列表与详情查询 ==============================

def get_all_buildings() -> List[Dict]:
    """
    获取所有未软删除的建筑列表（包含网格名称与类型友好显示）。
    
    Returns:
        List[Dict]: 建筑记录列表，每个 dict 包含 grid_name 和 type_display
    """
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
            b['type_display'] = get_building_type_display(b.get('type'))

        logger.info(f"成功加载建筑列表：共 {len(buildings)} 条")
        return buildings

    except Exception as e:
        logger.error(f"获取建筑列表失败: {e}")
        return []


def get_building_by_id(bid: int) -> Optional[Dict]:
    """
    根据 ID 获取单个建筑详情（包含网格名称与类型友好显示）。
    
    Args:
        bid: 建筑 ID
    
    Returns:
        Optional[Dict]: 建筑信息字典，若不存在返回 None
    """
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
        building['type_display'] = get_building_type_display(building.get('type'))

        return building

    except Exception as e:
        logger.error(f"获取建筑详情失败 (ID: {bid}): {e}")
        return None


# ============================== 仪表盘统计（v2.3 新增） ==============================

def get_building_count_by_type() -> List[Dict]:
    """
    统计建筑类型分布（用于首页仪表盘环形图/饼图）。
    
    Returns:
        List[Dict]: [{'type_display': str, 'count': int}, ...]，按数量降序
    """
    query = """
        SELECT type, COUNT(*) AS count
        FROM building
        WHERE is_deleted = 0
        GROUP BY type
        ORDER BY count DESC
    """

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        result = [
            {
                'type_display': get_building_type_display(row['type']),
                'count': row['count']
            }
            for row in rows
        ]

        logger.debug(f"建筑类型分布统计成功：{len(result)} 种类型")
        return result

    except Exception as e:
        logger.error(f"建筑类型分布统计失败: {e}")
        return []


# ============================== 建筑关联查询工具 ==============================

def get_building_by_name_or_address(name_or_address: str) -> Optional[Dict]:
    """
    模糊搜索建筑（主要用于导入数据时匹配已有建筑）。
    
    Args:
        name_or_address: 建筑名称或地址（部分匹配）
    
    Returns:
        Optional[Dict]: 匹配到的第一个建筑，若无则返回 None
    """
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
        building['type_display'] = get_building_type_display(building.get('type'))

        return building

    except Exception as e:
        logger.error(f"模糊搜索建筑失败 ({name_or_address}): {e}")
        return None


def get_buildings_for_select() -> List[Dict]:
    """
    为前端下拉框提供建筑选项数据（格式：名称 (类型) - 网格）。
    
    Returns:
        List[Dict]: [{'id': int, 'label': str}, ...]，按名称排序
    """
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
            # 清晰、可读性高的写法，避免 f-string 括号混乱
            type_display = get_building_type_display(row_dict.get('type'))
            grid_name = row_dict['grid_name'] or '无网格'
            label = f"{row_dict['name']} ({type_display}) - {grid_name}"
            
            options.append({
                'id': row_dict['id'],
                'label': label
            })

        logger.debug(f"生成建筑下拉选项：{len(options)} 项")
        return options

    except Exception as e:
        logger.error(f"获取建筑下拉选项失败: {e}")
        return []


def get_building_id_by_name(name: str) -> Optional[int]:
    """
    精确根据建筑名称获取 ID（导入时的备用匹配方案）。
    
    Args:
        name: 建筑完整名称
    
    Returns:
        Optional[int]: 建筑 ID，若不存在返回 None
    """
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

def create_building(name: str, type_: str, grid_id: Optional[int] = None, **extra_fields) -> int:
    """
    新增一条建筑记录（支持任意扩展字段）。
    
    Args:
        name: 建筑名称（必填）
        type_: 建筑类型键（必填）
        grid_id: 所属网格ID（可选）
        **extra_fields: 其他字段（如 address, build_year 等）
    
    Returns:
        int: 新插入的建筑 ID
    
    Raises:
        Exception: 插入失败时抛出
    """
    fields = ['name', 'type', 'grid_id', 'is_deleted']
    values = [name.strip(), type_, grid_id, 0]

    if extra_fields:
        for key, value in extra_fields.items():
            if value is not None:
                fields.append(key)
                values.append(value)

    insert_sql = f"INSERT INTO building ({', '.join(fields)}) VALUES ({', '.join(['?' for _ in fields])})"

    try:
        with get_db_connection() as conn:
            cursor = conn.execute(insert_sql, values)
            conn.commit()

        logger.info(f"新增建筑成功: \"{name}\" (类型: {type_}, 网格ID: {grid_id or '无'}, 新ID: {cursor.lastrowid})")
        return cursor.lastrowid

    except Exception as e:
        logger.error(f"新增建筑失败: 名称=\"{name}\", 类型={type_}, 错误: {e}")
        raise


def update_building(bid: int, **updates) -> bool:
    """
    动态更新建筑记录（只更新传入的非空字段）。
    
    Args:
        bid: 建筑 ID
        **updates: 要更新的字段和值
    
    Returns:
        bool: 更新是否成功
    """
    if not updates:
        return True

    set_parts = []
    values = []

    for key, value in updates.items():
        if value is not None:
            set_parts.append(f"{key} = ?")
            values.append(value)

    if not set_parts:
        return True

    set_clause = ', '.join(set_parts)
    values.append(bid)
    update_sql = f"UPDATE building SET {set_clause} WHERE id = ?"

    try:
        with get_db_connection() as conn:
            conn.execute(update_sql, values)
            conn.commit()

        logger.info(f"更新建筑成功 (ID: {bid})")
        return True

    except Exception as e:
        logger.error(f"更新建筑失败 (ID: {bid}): {e}")
        return False


def delete_building(bid: int) -> Tuple[bool, str]:
    """
    软删除指定建筑（设置 is_deleted = 1）。
    
    Args:
        bid: 建筑 ID
    
    Returns:
        Tuple[bool, str]: (是否成功, 提示信息)
    """
    try:
        with get_db_connection() as conn:
            conn.execute("UPDATE building SET is_deleted = 1 WHERE id = ?", (bid,))
            conn.commit()

        logger.info(f"软删除建筑成功 (ID: {bid})")
        return True, '建筑删除成功'

    except Exception as e:
        logger.error(f"软删除建筑失败 (ID: {bid}): {e}")
        return False, '删除失败：系统异常'


# ============================== 导出与统计专用 ==============================

def get_all_buildings_for_export(grid_ids: Optional[List[int]] = None) -> List[Dict]:
    """
    获取全部建筑数据（支持按网格权限过滤），专用于导出功能。
    
    Args:
        grid_ids: 允许导出的网格 ID 列表（None 表示无限制）
    
    Returns:
        List[Dict]: 建筑记录列表（包含 type_display 和 grid_name）
    
    Raises:
        Exception: 查询失败时抛出
    """
    base_query = """
        SELECT b.*, g.name AS grid_name
        FROM building b
        LEFT JOIN grid g ON b.grid_id = g.id
        WHERE b.is_deleted = 0
    """
    params: List[Any] = []

    if grid_ids:
        placeholders = ','.join(['?' for _ in grid_ids])
        base_query += f" AND b.grid_id IN ({placeholders})"
        params = grid_ids

    base_query += " ORDER BY b.id"

    try:
        with get_db_connection() as conn:
            rows = conn.execute(base_query, params).fetchall()

        buildings = [dict(row) for row in rows]

        for b in buildings:
            b['type_display'] = get_building_type_display(b.get('type'))
            b['grid_name'] = b['grid_name'] or '无网格'

        logger.info(f"成功导出建筑数据：共 {len(buildings)} 条（网格过滤: {grid_ids})")
        return buildings

    except Exception as e:
        logger.error(f"导出建筑数据失败: {e}")
        raise


def get_person_count_by_building(bid: int) -> int:
    """
    获取指定建筑当前的居住人数（排除软删除人员）。
    用于建筑详情页显示“当前居住人数”。
    
    Args:
        bid: 建筑 ID
    
    Returns:
        int: 当前居住人数（0 表示无人员或查询失败）
    """
    query = """
        SELECT COUNT(*) AS count
        FROM person
        WHERE living_building_id = ? AND is_deleted = 0
    """

    try:
        with get_db_connection() as conn:
            row = conn.execute(query, (bid,)).fetchone()
        count = row['count'] if row else 0
        logger.debug(f"建筑 {bid} 当前居住人数: {count}")
        return count
    except Exception as e:
        logger.error(f"获取建筑 {bid} 人员数量失败: {e}")
        return 0
