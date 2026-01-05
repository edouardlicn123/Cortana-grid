# repositories/person_repo.py
# 人员数据访问层（完整终极版 - 支持列表、详情、CRUD、统计、首页概览、导出 + 批量插入）
# 2026-01-05 修复：参数名统一为 phones，新增 address_detail 必填字段

from .base import get_db_connection
from utils import logger
from repositories.building_repo import get_building_type_display


def get_all_persons():
    """获取所有人员列表（带居住建筑名称和类型显示）"""
    try:
        query = """
            SELECT p.*, 
                   b.name AS living_building_name,
                   b.type AS building_type
            FROM person p
            LEFT JOIN building b ON p.living_building_id = b.id
            WHERE p.is_deleted = 0
            ORDER BY p.id DESC
        """

        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        persons = [dict(row) for row in rows]

        for p in persons:
            if p['building_type']:
                p['building_type_display'] = get_building_type_display(p['building_type'])
            else:
                p['building_type_display'] = '未知类型'

        logger.info(f"加载人员列表: {len(persons)} 条")
        return persons

    except Exception as e:
        logger.error(f"获取人员列表失败: {e}")
        return []


def get_person_by_id(pid: int):
    """根据 ID 获取单个人员详情"""
    try:
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM person WHERE id = ? AND is_deleted = 0",
                (pid,)
            ).fetchone()
        return dict(row) if row else None

    except Exception as e:
        logger.error(f"获取人员详情失败 (ID: {pid}): {e}")
        return None


def create_person(
    name: str,
    id_card: str,
    phones: str = None,
    gender: str = None,
    birth_date: str = None,
    person_type: str = '常住人口',
    living_building_id: int = None,
    address_detail: str = None,                # ← 新增必填字段
    household_building_id: int = None,
    household_address: str = None,
    family_id: str = None,
    household_entry_date: str = None,
    is_separated: bool = False,
    current_residence: str = None,
    is_migrated_out: bool = False,
    household_exit_date: str = None,
    migration_destination: str = None,
    is_deceased: bool = False,
    death_date: str = None,
    nationality: str = None,
    political_status: str = None,
    marital_status: str = None,
    education: str = None,
    work_study: str = None,
    health: str = None,
    notes: str = None,
    is_key_person: bool = False,
    key_categories: str = None,
    other_id_type: str = None,
    passport: str = None
) -> int:
    """新增单个人员，返回新 ID"""
    try:
        with get_db_connection() as conn:
            # 基础必填字段
            fields = ['name', 'id_card', 'phones', 'gender', 'birth_date', 'person_type',
                      'living_building_id', 'address_detail', 'is_deleted']
            values = [name, id_card, phones, gender, birth_date, person_type,
                      living_building_id, address_detail, 0]

            # 可选字段（有值才加入）
            optional_pairs = [
                ('household_building_id', household_building_id),
                ('household_address', household_address),
                ('family_id', family_id),
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

            for field, value in optional_pairs:
                if value is not None:
                    fields.append(field)
                    values.append(value)

            placeholders = ', '.join(['?' for _ in fields])
            cursor = conn.execute(
                f"INSERT INTO person ({', '.join(fields)}) VALUES ({placeholders})",
                values
            )
            conn.commit()

        logger.info(f"新增人员成功: {name} (ID: {cursor.lastrowid})")
        return cursor.lastrowid

    except Exception as e:
        logger.error(f"新增人员失败: {e}")
        raise


def bulk_insert_people(people_data: list[dict]) -> tuple[int, list[str]]:
    """批量插入人员数据（用于导入），返回 (成功数量, 错误列表)"""
    success_count = 0
    errors = []

    try:
        with get_db_connection() as conn:
            for idx, data in enumerate(people_data, start=1):
                try:
                    name = data.get('name')
                    id_card = data.get('id_card')
                    if not name or not id_card:
                        errors.append(f"第 {idx} 行: 姓名或身份证号为空")
                        continue

                    phones = data.get('phones') or data.get('phone')
                    living_building_id = data.get('living_building_id')
                    address_detail = data.get('address_detail') or data.get('address')

                    extra_kwargs = {k: v for k, v in data.items()
                                    if k not in {'name', 'id_card', 'phones', 'phone',
                                                 'living_building_id', 'address_detail', 'address'}}

                    create_person(
                        name=name,
                        id_card=id_card,
                        phones=phones,
                        living_building_id=living_building_id,
                        address_detail=address_detail,
                        **extra_kwargs
                    )
                    success_count += 1

                except Exception as row_e:
                    errors.append(f"第 {idx} 行: {str(row_e)}")

            conn.commit()

        logger.info(f"批量插入人员完成: 成功 {success_count} 条, 失败 {len(errors)} 条")
        return success_count, errors

    except Exception as e:
        logger.error(f"批量插入人员异常: {e}")
        return success_count, [f"系统错误: {str(e)}"] + errors


def update_person(pid: int,
                  name: str = None,
                  id_card: str = None,
                  phones: str = None,                     # ← 统一为 phones
                  gender: str = None,
                  birth_date: str = None,
                  person_type: str = None,
                  living_building_id: int = None,
                  address_detail: str = None,
                  household_building_id: int = None,
                  household_address: str = None,
                  family_id: str = None,
                  household_entry_date: str = None,
                  is_separated: bool = None,
                  current_residence: str = None,
                  is_migrated_out: bool = None,
                  household_exit_date: str = None,
                  migration_destination: str = None,
                  is_deceased: bool = None,
                  death_date: str = None,
                  nationality: str = None,
                  political_status: str = None,
                  marital_status: str = None,
                  education: str = None,
                  work_study: str = None,
                  health: str = None,
                  notes: str = None,
                  is_key_person: bool = None,
                  key_categories: str = None,
                  other_id_type: str = None,
                  passport: str = None) -> bool:
    """更新人员信息"""
    try:
        with get_db_connection() as conn:
            updates = []
            values = []

            optional_params = [
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
                ('household_entry_date', household_entry_date),
                ('is_separated', 1 if is_separated else 0 if is_separated is not None else None),
                ('current_residence', current_residence),
                ('is_migrated_out', 1 if is_migrated_out else 0 if is_migrated_out is not None else None),
                ('household_exit_date', household_exit_date),
                ('migration_destination', migration_destination),
                ('is_deceased', 1 if is_deceased else 0 if is_deceased is not None else None),
                ('death_date', death_date),
                ('nationality', nationality),
                ('political_status', political_status),
                ('marital_status', marital_status),
                ('education', education),
                ('work_study', work_study),
                ('health', health),
                ('notes', notes),
                ('is_key_person', 1 if is_key_person else 0 if is_key_person is not None else None),
                ('key_categories', key_categories),
                ('other_id_type', other_id_type),
                ('passport', passport),
            ]

            for field, value in optional_params:
                if value is not None:
                    updates.append(f"{field} = ?")
                    values.append(value)

            if not updates:
                return True  # 无需更新

            set_clause = ', '.join(updates)
            values.append(pid)

            conn.execute(f"UPDATE person SET {set_clause} WHERE id = ?", values)
            conn.commit()

        logger.info(f"更新人员成功 (ID: {pid})")
        return True

    except Exception as e:
        logger.error(f"更新人员失败 (ID: {pid}): {e}")
        return False


def delete_person(pid: int) -> tuple[bool, str]:
    """软删除人员"""
    try:
        with get_db_connection() as conn:
            conn.execute("UPDATE person SET is_deleted = 1 WHERE id = ?", (pid,))
            conn.commit()
        logger.info(f"软删除人员成功 (ID: {pid})")
        return True, '人员删除成功'
    except Exception as e:
        logger.error(f"删除人员失败 (ID: {pid}): {e}")
        return False, '删除失败'


# ============================== 统计与概览 ==============================

def get_overview_stats():
    """获取首页概览统计数据"""
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

        return {
            'total_persons': total_persons,
            'total_buildings': total_buildings,
            'total_grids': total_grids,
            'key_persons': key_persons
        }

    except Exception as e:
        logger.error(f"获取概览统计失败: {e}")
        return {
            'total_persons': 0,
            'total_buildings': 0,
            'total_grids': 0,
            'key_persons': 0
        }


# ============================== 导出专用函数 ==============================

def get_all_people_for_export():
    """获取用于导出的人员数据（完整关联信息）"""
    try:
        query = """
            SELECT p.*, 
                   b.name AS living_building_name,
                   b.type AS building_type,
                   g.name AS grid_name
            FROM person p
            LEFT JOIN building b ON p.living_building_id = b.id
            LEFT JOIN grid g ON b.grid_id = g.id
            WHERE p.is_deleted = 0
            ORDER BY p.id
        """

        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        people = [dict(row) for row in rows]

        for person in people:
            person['building_type_display'] = get_building_type_display(person.get('building_type'))
            person['grid_name'] = person['grid_name'] or '无网格'

        logger.info(f"导出人员数据: {len(people)} 条")
        return people

    except Exception as e:
        logger.error(f"导出人员数据失败: {e}")
        raise
