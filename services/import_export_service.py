# services/import_export_service.py
# 导入导出总入口（极轻量版） - 只负责公共工具函数和请求转发
# 实际的业务逻辑按实体拆分到各自专属模块：
#   - 人员：import_export_person.py
#   - 建筑：import_export_building.py
#   - 未来扩展：grid、vehicle 等可继续添加转发分支

import os
from typing import Tuple, Optional
from flask import current_app
from werkzeug.utils import secure_filename
from utils import logger

# 支持的文件扩展名（严格限制，避免安全隐患）
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}


def allowed_file(filename: str) -> bool:
    """
    检查上传的文件扩展名是否在允许列表中。
    
    Args:
        filename: 文件名（包含扩展名）
    
    Returns:
        bool: 是否允许上传
    """
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def get_template_path(data_type: str) -> Optional[str]:
    """
    获取指定数据类型的导入模板文件路径。
    当前使用静态文件方式，路径位于 static/templates/excel/ 下。
    
    Args:
        data_type: 数据类型，如 'person', 'building'
    
    Returns:
        str | None: 模板文件的完整路径，或 None（类型不支持）
    """
    base_dir = os.path.join(current_app.static_folder, 'templates', 'excel')
    
    templates_map = {
        'person': os.path.join(base_dir, '人员导入模板.xlsx'),
        'building': os.path.join(base_dir, '建筑导入模板.xlsx'),
        # 未来扩展示例：
        # 'grid': os.path.join(base_dir, '网格导入模板.xlsx'),
    }
    
    path = templates_map.get(data_type)
    if path and os.path.exists(path):
        return path
    
    logger.warning(f"模板文件不存在或类型不支持: {data_type} -> {path}")
    return None


# ==================== 导出请求转发 ====================
def export_data_to_excel(data_type: str, user) -> Tuple[str, str]:
    """
    根据数据类型转发到对应模块的导出函数。
    
    Args:
        data_type: 'person' / 'building' 等
        user: 当前登录用户对象（用于权限过滤和日志）
    
    Returns:
        Tuple[str, str]: (文件完整路径, 下载推荐文件名)
    
    Raises:
        ValueError: 不支持的类型
        ImportError / AttributeError: 对应模块或函数不存在
    """
    try:
        if data_type == 'person':
            from .import_export_person import export_person_to_excel
            logger.info(f"用户 {user.username} 开始导出人员数据")
            return export_person_to_excel(user)
        
        elif data_type == 'building':
            from .import_export_building import export_building_to_excel
            logger.info(f"用户 {user.username} 开始导出建筑数据")
            return export_building_to_excel(user)
        
        else:
            raise ValueError(f"不支持的导出数据类型：{data_type}")
            
    except ImportError as e:
        logger.error(f"导入导出模块失败 ({data_type}): {e}")
        raise ValueError(f"导出功能未实现：{data_type}")
    except Exception as e:
        logger.error(f"导出转发异常 ({data_type}): {e}", exc_info=True)
        raise


# ==================== 导入请求转发 ====================
def process_import_excel(file, data_type: str, user) -> Tuple[bool, str]:
    """
    根据数据类型转发到对应模块的导入处理函数。
    
    Args:
        file: Flask 上传的文件对象
        data_type: 'person' / 'building' 等
        user: 当前登录用户对象
    
    Returns:
        Tuple[bool, str]: (是否成功, 提示消息)
    
    Raises:
        ValueError: 不支持的类型
        ImportError / AttributeError: 对应模块或函数不存在
    """
    try:
        if data_type == 'person':
            from .import_export_person import import_person_from_excel
            logger.info(f"用户 {user.username} 开始导入人员数据")
            return import_person_from_excel(file, user)
        
        elif data_type == 'building':
            from .import_export_building import import_building_from_excel
            logger.info(f"用户 {user.username} 开始导入建筑数据")
            return import_building_from_excel(file, user)
        
        else:
            raise ValueError(f"不支持的导入数据类型：{data_type}")
            
    except ImportError as e:
        logger.error(f"导入模块加载失败 ({data_type}): {e}")
        raise ValueError(f"导入功能未实现：{data_type}")
    except Exception as e:
        logger.error(f"导入转发异常 ({data_type}): {e}", exc_info=True)
        return False, f"导入处理失败：{str(e)}"
