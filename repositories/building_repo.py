# repositories/building_repo.py
# 文件功能说明：
#   - 建筑数据访问层（Repository 层核心模块）
#   - 核心职责：
#       • 提供建筑数据的完整 CRUD 操作（列表、详情、新增、更新、软删除）
#       • 支持网格关联显示（网格名称、类型友好中文显示）
#       • 下拉选项生成（用于人员编辑时的建筑选择）
#       • 模糊搜索与精确匹配（用于导入时建筑匹配）
#       • 首页概览统计（建筑总数，由 get_overview_stats 调用）
#       • 仪表盘专用统计查询（v2.3 新增）：
#           - 建筑类型分布统计（用于环形图）
#       • 导出专用全量数据查询（支持网格权限过滤）
#   - 所有操作统一使用字典行工厂，返回标准 dict 结构
#   - 全面异常处理 + 日志记录，确保生产环境健壮性
#   - 依赖：repositories.base（数据库连接）、utils.logger
#   - 版本：v2.3（仪表盘增强版 - 新增建筑类型分布统计函数 get_building_count_by_type）
#   - 更新历史：
#       • 2026-02-02：新增仪表盘统计函数 get_building_count_by_type
#       • 2026-02-02：修复 typing 导入（补充 Tuple）

from .base import get_db_connection
from utils import logger
from typing import List, Dict, Optional, Tuple, Any


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
    """
    return BUILDING_TYPE_MAP.get(type_key or '', type_key or '未知类型')


# ============================== 列表与查询 ==============================

def get_all_buildings() -> List[Dict]:
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


def get_building_by_id(bid: int) -> Dict | None:
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


# ============================== 仪表盘统计（v2.3 新增） ==============================

def get_building_count_by_type() -> List[Dict]:
    """
    统计建筑类型分布（用于首页仪表盘环形图）
    
    Returns:
        List[Dict]: [{'type_display': str, 'count': int}, ...]
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


# ============================== 其他查询工具 ==============================

def get_building_by_name_or_address(name_or_address: str) -> Dict | None:
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


def get_buildings_for_select() -> List[Dict]:
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

def create_building(name: str, type_: str, grid_id: int | None = None, **extra_fields) -> int:
    """新增建筑记录（支持扩展字段）"""
    # 核心字段
    fields = ['name', 'type', 'grid_id', 'is_deleted']
    values = [name.strip(), type_, grid_id, 0]
    placeholders = ', '.join(['?' for _ in fields])

    # 扩展字段支持
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
    """动态更新建筑信息（仅更新提供的字段）"""
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
    """软删除建筑记录"""
    try:
        with get_db_connection() as conn:
            conn.execute("UPDATE building SET is_deleted = 1 WHERE id = ?", (bid,))
            conn.commit()

        logger.info(f"软删除建筑成功 (ID: {bid})")
        return True, '建筑删除成功'

    except Exception as e:
        logger.error(f"软删除建筑失败 (ID: {bid}): {e}")
        return False, '删除失败：系统异常'


# ============================== 导出专用 ==============================

def get_all_buildings_for_export(grid_ids: Optional[List[int]] = None) -> List[Dict]:
    """导出全部建筑数据（支持按网格权限过滤）"""
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
    获取指定建筑下的当前居住人数（排除软删除人员）
    
    Args:
        bid: 建筑 ID
    
    Returns:
        int: 居住人数（living_building_id 匹配且未软删除）
    """
    query = """
        SELECT COUNT(*) AS count
        FROM person
        WHERE living_building_id = ? AND is_deleted = 0
    """

    try:
        with get_db_connection() as conn:
            row = conn.execute(query, (bid,)).fetchone()
        return row['count'] if row else 0
    except Exception as e:
        logger.error(f"获取建筑 {bid} 人员数量失败: {e}")
        return 0
