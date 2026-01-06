# repositories/person_repo.py
# 人员数据访问层（优化终极版 - 功能完全不变，代码更健壮、可读、专业）
# 2026-01-06 更新：补回 household_number 字段支持

from .base import get_db_connection
from utils import logger
from repositories.building_repo import get_building_type_display
from typing import List, Dict, Tuple, Any


# ============================== 列表与查询 ==============================

def get_all_persons() -> List[Dict]:
    """获取所有未软删除的人员列表（包含居住建筑名称与类型友好显示）"""
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
                get_building_type_display(p['building_type'])
                if p['building_type']
                else '未知类型'
            )

        logger.info(f"成功加载人员列表：共 {len(persons)} 条")
        return persons

    except Exception as e:
        logger.error(f"获取人员列表失败: {e}")
        return []


def get_person_by_id(pid: int) -> Dict | None:
    """根据 ID 获取单个人员完整详情"""
    query = "SELECT * FROM person WHERE id = ? AND is_deleted = 0"

    try:
        with get_db_connection() as conn:
            row = conn.execute(query, (pid,)).fetchone()

        return dict(row) if row else None

    except Exception as e:
        logger.error(f"获取人员详情失败 (ID: {pid}): {e}")
        return None


# ============================== 新增与批量插入 ==============================

def create_person(
    name: str,
    id_card: str,
    phones: str | None = None,
    gender: str | None = None,
    birth_date: str | None = None,
    person_type: str = '常住人口',
    living_building_id: int | None = None,
    address_detail: str | None = None,
    household_building_id: int | None = None,
    household_address: str | None = None,
    family_id: str | None = None,
    household_number: str | None = None,          # 补回
    household_entry_date: str | None = None,
    is_separated: bool = False,
    current_residence: str | None = None,
    is_migrated_out: bool = False,
    household_exit_date: str | None = None,
    migration_destination: str | None = None,
    is_deceased: bool = False,
    death_date: str | None = None,
    nationality: str | None = None,
    political_status: str | None = None,
    marital_status: str | None = None,
    education: str | None = None,
    work_study: str | None = None,
    health: str | None = None,
    notes: str | None = None,
    is_key_person: bool = False,
    key_categories: str | None = None,
    other_id_type: str | None = None,
    passport: str | None = None
) -> int:
    """
    新增单个人员记录
    
    Returns:
        int: 新建记录的 ID
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
        ('household_number', household_number),                  # 补回
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
    批量导入人员数据（支持 Excel 导入）
    
    Returns:
        Tuple[int, List[str]]: (成功数量, 错误信息列表)
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
                        fail_reasons.append(f"第 {idx+2} 行：姓名为空")
                        continue
                    if not phones:
                        fail_reasons.append(f"第 {idx+2} 行：联系电话为空（{name}）")
                        continue
                    if not living_building_name:
                        fail_reasons.append(f"第 {idx+2} 行：现住小区/建筑为空（{name}）")
                        continue

                    # 参数兼容处理
                    phones = data.get('phones') or data.get('phone')
                    living_building_id = data.get('living_building_id')
                    address_detail = data.get('address_detail') or data.get('address')

                    # 过滤掉已处理的键，剩余作为额外字段
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
                    errors.append(f"第 {idx} 行: {error_msg}")

            conn.commit()

        logger.info(f"批量导入完成：成功 {success_count} 条，失败 {len(errors)} 条")
        return success_count, errors

    except Exception as e:
        logger.error(f"批量导入人员异常终止: {e}")
        return success_count, [f"系统异常: {str(e)}"] + errors


# ============================== 更新与删除 ==============================

def update_person(
    pid: int,
    name: str | None = None,
    id_card: str | None = None,
    phones: str | None = None,
    gender: str | None = None,
    birth_date: str | None = None,
    person_type: str | None = None,
    living_building_id: int | None = None,
    address_detail: str | None = None,
    household_building_id: int | None = None,
    household_address: str | None = None,
    family_id: str | None = None,
    household_number: str | None = None,          # 补回
    household_entry_date: str | None = None,
    is_separated: bool | None = None,
    current_residence: str | None = None,
    is_migrated_out: bool | None = None,
    household_exit_date: str | None = None,
    migration_destination: str | None = None,
    is_deceased: bool | None = None,
    death_date: str | None = None,
    nationality: str | None = None,
    political_status: str | None = None,
    marital_status: str | None = None,
    education: str | None = None,
    work_study: str | None = None,
    health: str | None = None,
    notes: str | None = None,
    is_key_person: bool | None = None,
    key_categories: str | None = None,
    other_id_type: str | None = None,
    passport: str | None = None
) -> bool:
    """动态更新人员信息（仅更新提供的字段）"""
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
        ('household_number', household_number),               # 补回
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

    # 布尔字段特殊处理
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
    """软删除人员记录"""
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
    """获取系统首页关键统计数据"""
    default_stats = {
        'total_persons': 0,
        'total_buildings': 0,
        'total_grids': 0,
        'key_persons': 0
    }

    try:
        with get_db_connection() as conn:
            total_persons = conn.execute(
                "SELECT COUNT(*) FROM person WHERE is_deleted = 0"
            ).fetchone()[0]

            total_buildings = conn.execute(
                "SELECT COUNT(*) FROM building WHERE is_deleted = 0"
            ).fetchone()[0]

            total_grids = conn.execute(
                "SELECT COUNT(*) FROM grid WHERE is_deleted = 0"
            ).fetchone()[0]

            key_persons = conn.execute(
                "SELECT COUNT(*) FROM person WHERE is_key_person = 1 AND is_deleted = 0"
            ).fetchone()[0]

        stats = {
            'total_persons': total_persons,
            'total_buildings': total_buildings,
            'total_grids': total_grids,
            'key_persons': key_persons
        }
        logger.debug(f"首页统计数据加载成功: {stats}")
        return stats

    except Exception as e:
        logger.error(f"获取概览统计失败: {e}")
        return default_stats


# ============================== 导出专用 ==============================

def get_all_people_for_export(grid_ids: list[int] | None = None) -> List[Dict]:
    """导出全部人员数据（支持按网格权限过滤）"""
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
    params: list = []

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
