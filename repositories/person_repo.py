# repositories/person_repo.py
# 文件功能说明：
#   - 人员数据访问层（Repository 层核心模块）
#   - 核心职责：
#       • 提供人员数据的完整 CRUD 操作（列表查询、详情、单条新增、批量导入、动态更新、软删除）
#       • 支持建筑关联查询与友好显示（居住建筑名称、建筑类型中文映射）
#       • 首页概览统计（总人数、重点人员、建筑数、网格数）
#       • 仪表盘专用统计查询（v2.3 新增）：
#           - 人员类型分布统计（用于饼图/环形图）
#           - 各网格人员数量统计（用于柱状图）
#       • 导出专用全量数据查询（支持网格权限过滤，返回丰富关联字段）
#       • 批量导入兼容处理（支持 Excel 字段映射、错误收集与回滚提示）
#   - 所有查询统一使用字典行工厂（dict_row_factory），返回标准 dict 结构
#   - 全面异常处理 + 日志记录（使用 utils.logger），确保生产环境健壮性
#   - 关键设计原则：
#       • 软删除机制（is_deleted = 1）
#       • 动态字段更新（update_person 支持任意字段组合）
#       • 网格权限过滤（导出时使用）
#       • 字段兼容性（批量导入时处理 Excel 可能的列名差异）
#       • 布尔字段统一转为 0/1 存储
#   - 依赖：
#       • repositories.base → get_db_connection
#       • repositories.building_repo → get_building_type_display
#       • utils → logger
#   - 版本：v2.3（仪表盘增强版）
#   - 更新历史：
#       • 2026-01-06：补回 household_number 字段支持
#       • 2026-02-02：新增仪表盘统计函数 get_person_count_by_type / get_person_count_by_grid
#       • 2026-02-02：完善 get_overview_stats（增加重点人员统计）
#       • 2026-02-02：优化批量导入逻辑（字段兼容、错误收集更清晰）
#       • 2026-02-02：补充完整类型注解与详细文档字符串

from .base import get_db_connection
from utils import logger
from repositories.building_repo import get_building_type_display
from typing import List, Dict, Optional, Tuple, Any


# ============================== 列表与详情查询 ==============================

def get_all_persons() -> List[Dict]:
    """
    获取所有未软删除的人员列表（包含居住建筑名称与类型友好显示）。
    
    Returns:
        List[Dict]: 人员记录列表，每个 dict 包含 living_building_name 和 building_type_display
    """
    query = """
        SELECT p.*, 
               b.name AS living_building_name,
               b.type AS building_type
        FROM person p
        LEFT JOIN building b ON p.living_building_id = b.id
        WHERE p.is_deleted = 0
        ORDER BY p.id DESC
    """

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        persons = [dict(row) for row in rows]

        for p in persons:
            p['building_type_display'] = (
                get_building_type_display(p.get('building_type'))
                if p.get('building_type')
                else '未知类型'
            )

        logger.info(f"成功加载人员列表：共 {len(persons)} 条")
        return persons

    except Exception as e:
        logger.error(f"获取人员列表失败: {e}")
        return []


def get_person_by_id(pid: int) -> Optional[Dict]:
    """
    根据 ID 获取单个人员完整详情。
    
    Args:
        pid: 人员 ID
    
    Returns:
        Optional[Dict]: 人员信息字典，若不存在或已软删除返回 None
    """
    query = "SELECT * FROM person WHERE id = ? AND is_deleted = 0"

    try:
        with get_db_connection() as conn:
            row = conn.execute(query, (pid,)).fetchone()
        return dict(row) if row else None

    except Exception as e:
        logger.error(f"获取人员详情失败 (ID: {pid}): {e}")
        return None


# ============================== 仪表盘统计（v2.3 新增） ==============================

def get_person_count_by_type() -> List[Dict]:
    """
    统计人员类型分布（用于首页仪表盘饼图/环形图）。
    
    Returns:
        List[Dict]: [{'person_type': str, 'count': int}, ...]，按数量降序
    """
    query = """
        SELECT person_type, COUNT(*) AS count
        FROM person
        WHERE is_deleted = 0
        GROUP BY person_type
        ORDER BY count DESC
    """

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        result = [dict(row) for row in rows]
        # 兜底处理空值
        for item in result:
            if not item['person_type']:
                item['person_type'] = '未分类'

        logger.debug(f"人员类型分布统计成功：{len(result)} 种类型")
        return result

    except Exception as e:
        logger.error(f"人员类型分布统计失败: {e}")
        return []


def get_person_count_by_grid() -> List[Dict]:
    """
    统计各网格下的人员数量（用于首页仪表盘柱状图）。
    
    Returns:
        List[Dict]: [{'grid_name': str, 'count': int}, ...]，按数量降序
    """
    query = """
        SELECT g.name AS grid_name, COUNT(p.id) AS count
        FROM person p
        LEFT JOIN building b ON p.living_building_id = b.id
        LEFT JOIN grid g ON b.grid_id = g.id
        WHERE p.is_deleted = 0
        GROUP BY g.id, g.name
        ORDER BY count DESC
    """

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        result = [dict(row) for row in rows]
        # 兜底处理无网格
        for item in result:
            item['grid_name'] = item['grid_name'] or '无网格'

        logger.debug(f"各网格人员数量统计成功：{len(result)} 个网格")
        return result

    except Exception as e:
        logger.error(f"各网格人员数量统计失败: {e}")
        return []


# ============================== 新增与批量插入 ==============================

def create_person(
    name: str,
    id_card: str,
    phones: Optional[str] = None,
    gender: Optional[str] = None,
    birth_date: Optional[str] = None,
    person_type: str = '常住人口',
    living_building_id: Optional[int] = None,
    address_detail: Optional[str] = None,
    household_building_id: Optional[int] = None,
    household_address: Optional[str] = None,
    family_id: Optional[str] = None,
    household_number: Optional[str] = None,
    household_entry_date: Optional[str] = None,
    is_separated: bool = False,
    current_residence: Optional[str] = None,
    is_migrated_out: bool = False,
    household_exit_date: Optional[str] = None,
    migration_destination: Optional[str] = None,
    is_deceased: bool = False,
    death_date: Optional[str] = None,
    nationality: Optional[str] = None,
    political_status: Optional[str] = None,
    marital_status: Optional[str] = None,
    education: Optional[str] = None,
    work_study: Optional[str] = None,
    health: Optional[str] = None,
    notes: Optional[str] = None,
    is_key_person: bool = False,
    key_categories: Optional[str] = None,
    other_id_type: Optional[str] = None,
    passport: Optional[str] = None
) -> int:
    """
    新增单个人员记录（支持所有字段）。
    
    Args:
        name: 姓名（必填）
        id_card: 身份证号（必填）
        ... 其他字段均为可选
    
    Returns:
        int: 新插入的人员 ID
    
    Raises:
        Exception: 插入失败时抛出
    """
    base_fields = [
        'name', 'id_card', 'phones', 'gender', 'birth_date', 'person_type',
        'living_building_id', 'address_detail', 'is_deleted'
    ]
    base_values = [
        name.strip(), id_card.strip(), phones, gender, birth_date, person_type,
        living_building_id, address_detail, 0
    ]

    optional_mapping: List[Tuple[str, Any]] = [
        ('household_building_id', household_building_id),
        ('household_address', household_address),
        ('family_id', family_id),
        ('household_number', household_number),
        ('household_entry_date', household_entry_date),
        ('is_separated', 1 if is_separated else 0),
        ('current_residence', current_residence),
        ('is_migrated_out', 1 if is_migrated_out else 0),
        ('household_exit_date', household_exit_date),
        ('migration_destination', migration_destination),
        ('is_deceased', 1 if is_deceased else 0),
        ('death_date', death_date),
        ('nationality', nationality),
        ('political_status', political_status),
        ('marital_status', marital_status),
        ('education', education),
        ('work_study', work_study),
        ('health', health),
        ('notes', notes),
        ('is_key_person', 1 if is_key_person else 0),
        ('key_categories', key_categories),
        ('other_id_type', other_id_type),
        ('passport', passport),
    ]

    fields = base_fields[:]
    values = base_values[:]

    for field, value in optional_mapping:
        if value is not None:
            fields.append(field)
            values.append(value)

    placeholders = ', '.join(['?' for _ in fields])
    insert_sql = f"INSERT INTO person ({', '.join(fields)}) VALUES ({placeholders})"

    try:
        with get_db_connection() as conn:
            cursor = conn.execute(insert_sql, values)
            conn.commit()

        logger.info(f"新增人员成功: \"{name}\" (身份证: {id_card}, 新ID: {cursor.lastrowid})")
        return cursor.lastrowid

    except Exception as e:
        logger.error(f"新增人员失败 (姓名: \"{name}\", 身份证: {id_card}): {e}")
        raise


def bulk_insert_people(people_data: List[Dict]) -> Tuple[int, List[str]]:
    """
    批量导入人员数据（主要用于 Excel 导入）。
    
    Args:
        people_data: 每行数据的字典列表（键为字段名）
    
    Returns:
        Tuple[int, List[str]]: (成功导入条数, 错误信息列表)
    """
    success_count = 0
    errors: List[str] = []

    try:
        with get_db_connection() as conn:
            for idx, data in enumerate(people_data, start=1):
                try:
                    name = data.get('name')
                    id_card = data.get('id_card')

                    if not name:
                        errors.append(f"第 {idx+2} 行：姓名为空，跳过")
                        continue
                    if not id_card:
                        errors.append(f"第 {idx+2} 行：身份证号为空，跳过")
                        continue

                    # 字段兼容处理（Excel 可能使用 phone 而非 phones）
                    phones = data.get('phones') or data.get('phone')
                    living_building_id = data.get('living_building_id')
                    address_detail = data.get('address_detail') or data.get('address')

                    # 其余字段作为额外参数
                    extra_kwargs = {
                        k: v for k, v in data.items()
                        if k not in {
                            'name', 'id_card', 'phones', 'phone',
                            'living_building_id', 'address_detail', 'address'
                        }
                    }

                    create_person(
                        name=name.strip(),
                        id_card=id_card.strip(),
                        phones=phones,
                        living_building_id=living_building_id,
                        address_detail=address_detail,
                        **extra_kwargs
                    )
                    success_count += 1

                except Exception as row_e:
                    error_msg = str(row_e).replace('\n', ' ')
                    name_str = data.get('name', '未知')
                    errors.append(f"第 {idx+2} 行 ({name_str}): {error_msg}")

            conn.commit()

        logger.info(f"批量导入完成：成功 {success_count} 条，失败 {len(errors)} 条")
        return success_count, errors

    except Exception as e:
        logger.error(f"批量导入人员异常终止: {e}")
        return success_count, [f"系统异常: {str(e)}"] + errors


# ============================== 更新与删除 ==============================

def update_person(
    pid: int,
    name: Optional[str] = None,
    id_card: Optional[str] = None,
    phones: Optional[str] = None,
    gender: Optional[str] = None,
    birth_date: Optional[str] = None,
    person_type: Optional[str] = None,
    living_building_id: Optional[int] = None,
    address_detail: Optional[str] = None,
    household_building_id: Optional[int] = None,
    household_address: Optional[str] = None,
    family_id: Optional[str] = None,
    household_number: Optional[str] = None,
    household_entry_date: Optional[str] = None,
    is_separated: Optional[bool] = None,
    current_residence: Optional[str] = None,
    is_migrated_out: Optional[bool] = None,
    household_exit_date: Optional[str] = None,
    migration_destination: Optional[str] = None,
    is_deceased: Optional[bool] = None,
    death_date: Optional[str] = None,
    nationality: Optional[str] = None,
    political_status: Optional[str] = None,
    marital_status: Optional[str] = None,
    education: Optional[str] = None,
    work_study: Optional[str] = None,
    health: Optional[str] = None,
    notes: Optional[str] = None,
    is_key_person: Optional[bool] = None,
    key_categories: Optional[str] = None,
    other_id_type: Optional[str] = None,
    passport: Optional[str] = None
) -> bool:
    """
    动态更新人员信息（仅更新提供的非空字段）。
    
    Args:
        pid: 人员 ID
        ... 各字段均为可选
    
    Returns:
        bool: 更新是否成功
    """
    updates: List[str] = []
    values: List[Any] = []

    field_mappings = [
        ('name', name),
        ('id_card', id_card),
        ('phones', phones),
        ('gender', gender),
        ('birth_date', birth_date),
        ('person_type', person_type),
        ('living_building_id', living_building_id),
        ('address_detail', address_detail),
        ('household_building_id', household_building_id),
        ('household_address', household_address),
        ('family_id', family_id),
        ('household_number', household_number),
        ('household_entry_date', household_entry_date),
        ('current_residence', current_residence),
        ('household_exit_date', household_exit_date),
        ('migration_destination', migration_destination),
        ('death_date', death_date),
        ('nationality', nationality),
        ('political_status', political_status),
        ('marital_status', marital_status),
        ('education', education),
        ('work_study', work_study),
        ('health', health),
        ('notes', notes),
        ('key_categories', key_categories),
        ('other_id_type', other_id_type),
        ('passport', passport),
    ]

    bool_fields = [
        ('is_separated', is_separated),
        ('is_migrated_out', is_migrated_out),
        ('is_deceased', is_deceased),
        ('is_key_person', is_key_person),
    ]

    for field, value in field_mappings:
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(value.strip() if isinstance(value, str) else value)

    for field, value in bool_fields:
        if value is not None:
            updates.append(f"{field} = ?")
            values.append(1 if value else 0)

    if not updates:
        return True  # 无需更新

    set_clause = ', '.join(updates)
    values.append(pid)
    update_sql = f"UPDATE person SET {set_clause} WHERE id = ?"

    try:
        with get_db_connection() as conn:
            conn.execute(update_sql, values)
            conn.commit()

        logger.info(f"更新人员成功 (ID: {pid})")
        return True

    except Exception as e:
        logger.error(f"更新人员失败 (ID: {pid}): {e}")
        return False


def delete_person(pid: int) -> Tuple[bool, str]:
    """
    软删除指定人员（设置 is_deleted = 1）。
    
    Args:
        pid: 人员 ID
    
    Returns:
        Tuple[bool, str]: (是否成功, 提示信息)
    """
    try:
        with get_db_connection() as conn:
            conn.execute("UPDATE person SET is_deleted = 1 WHERE id = ?", (pid,))
            conn.commit()

        logger.info(f"软删除人员成功 (ID: {pid})")
        return True, '人员删除成功'

    except Exception as e:
        logger.error(f"软删除人员失败 (ID: {pid}): {e}")
        return False, '删除失败：系统异常'


# ============================== 统计与概览 ==============================

def get_overview_stats() -> Dict[str, int]:
    """
    获取系统首页关键统计数据（供 routes/main.py 使用）。
    
    Returns:
        Dict[str, int]: {'total_persons', 'key_persons', 'total_buildings', 'total_grids'}
    """
    default_stats = {
        'total_persons': 0,
        'key_persons': 0,
        'total_buildings': 0,
        'total_grids': 0
    }

    try:
        with get_db_connection() as conn:
            # 总人数（未软删除）
            persons_row = conn.execute(
                "SELECT COUNT(*) AS count FROM person WHERE is_deleted = 0"
            ).fetchone()
            total_persons = persons_row['count'] if persons_row else 0

            # 重点人员（已启用真实统计）
            key_persons_row = conn.execute(
                "SELECT COUNT(*) AS count FROM person WHERE is_key_person = 1 AND is_deleted = 0"
            ).fetchone()
            key_persons = key_persons_row['count'] if key_persons_row else 0

            # 总建筑数（未软删除）
            buildings_row = conn.execute(
                "SELECT COUNT(*) AS count FROM building WHERE is_deleted = 0"
            ).fetchone()
            total_buildings = buildings_row['count'] if buildings_row else 0

            # 总网格数（未软删除）
            grids_row = conn.execute(
                "SELECT COUNT(*) AS count FROM grid WHERE is_deleted = 0"
            ).fetchone()
            total_grids = grids_row['count'] if grids_row else 0

        stats = {
            'total_persons': total_persons,
            'key_persons': key_persons,
            'total_buildings': total_buildings,
            'total_grids': total_grids
        }
        logger.debug(f"首页统计数据加载成功: {stats}")
        return stats

    except Exception as e:
        logger.error(f"获取概览统计失败: {e}")
        return default_stats


# ============================== 导出专用 ==============================

def get_all_people_for_export(grid_ids: Optional[List[int]] = None) -> List[Dict]:
    """
    获取全部人员数据（支持按网格权限过滤），专用于导出功能。
    
    Args:
        grid_ids: 允许导出的网格 ID 列表（None 表示无限制）
    
    Returns:
        List[Dict]: 人员记录列表（包含 living_building_name、building_type_display、grid_name）
    
    Raises:
        Exception: 查询失败时抛出
    """
    base_query = """
        SELECT p.*, 
               b.name AS living_building_name,
               b.type AS building_type,
               g.name AS grid_name
        FROM person p
        LEFT JOIN building b ON p.living_building_id = b.id
        LEFT JOIN grid g ON b.grid_id = g.id
        WHERE p.is_deleted = 0
    """
    params: List[Any] = []

    if grid_ids:
        placeholders = ','.join(['?' for _ in grid_ids])
        base_query += f" AND b.grid_id IN ({placeholders})"
        params = grid_ids

    base_query += " ORDER BY p.id"

    try:
        with get_db_connection() as conn:
            rows = conn.execute(base_query, params).fetchall()

        people = [dict(row) for row in rows]

        for person in people:
            person['building_type_display'] = get_building_type_display(person.get('building_type'))
            person['grid_name'] = person['grid_name'] or '无网格'

        logger.info(f"成功导出人员数据：共 {len(people)} 条（网格过滤: {grid_ids})")
        return people

    except Exception as e:
        logger.error(f"导出人员数据失败: {e}")
        raise
