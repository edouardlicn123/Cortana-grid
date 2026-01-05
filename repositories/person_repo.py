# repositories/person_repo.py
# 人员数据访问层（完整终极版 - 支持列表、详情、CRUD、统计、首页概览、导出 + 批量插入）

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


def create_person(name: str, id_card: str, phone: str = None, living_building_id: int = None, **kwargs) -> int:
    """新增单个人员，返回新 ID"""
    try:
        with get_db_connection() as conn:
            base_fields = ['name', 'id_card', 'phone', 'living_building_id', 'is_deleted']
            base_values = [name, id_card, phone, living_building_id, 0]

            extra_fields = []
            extra_values = []
            for key, value in kwargs.items():
                if value is not None:
                    extra_fields.append(key)
                    extra_values.append(value)

            fields = base_fields + extra_fields
            field_names = ', '.join(fields)
            placeholders = ', '.join(['?' for _ in fields])

            cursor = conn.execute(
                f"INSERT INTO person ({field_names}) VALUES ({placeholders})",
                base_values + extra_values
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
                    # 基础必填字段
                    name = data.get('name')
                    id_card = data.get('id_card')
                    if not name or not id_card:
                        errors.append(f"第 {idx} 行: 姓名或身份证号为空")
                        continue

                    # 可选字段
                    phone = data.get('phone')
                    living_building_id = data.get('living_building_id')

                    # 其他扩展字段直接传入 kwargs
                    extra_kwargs = {k: v for k, v in data.items() if k not in {'name', 'id_card', 'phone', 'living_building_id'}}

                    create_person(
                        name=name,
                        id_card=id_card,
                        phone=phone,
                        living_building_id=living_building_id,
                        **extra_kwargs
                    )
                    success_count += 1

                except Exception as row_e:
                    errors.append(f"第 {idx} 行: {str(row_e)}")

            conn.commit()  # 所有成功后统一提交

        logger.info(f"批量插入人员完成: 成功 {success_count} 条, 失败 {len(errors)} 条")
        return success_count, errors

    except Exception as e:
        logger.error(f"批量插入人员异常: {e}")
        return success_count, [f"系统错误: {str(e)}"] + errors


def update_person(pid: int, name: str = None, id_card: str = None, phone: str = None,
                  living_building_id: int = None, **kwargs) -> bool:
    """更新人员信息"""
    try:
        with get_db_connection() as conn:
            updates = []
            values = []

            if name is not None:
                updates.append("name = ?")
                values.append(name)
            if id_card is not None:
                updates.append("id_card = ?")
                values.append(id_card)
            if phone is not None:
                updates.append("phone = ?")
                values.append(phone)
            if living_building_id is not None:
                updates.append("living_building_id = ?")
                values.append(living_building_id)

            for key, value in kwargs.items():
                if value is not None:
                    updates.append(f"{key} = ?")
                    values.append(value)

            if not updates:
                return True

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
