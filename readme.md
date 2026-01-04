# Cortana Grid - 社区网格化人口管理系统

**Cortana Grid** 是一个专为社区网格化治理设计的现代化 Flask Web 系统，实现对**网格、小区/建筑、人员**的全生命周期管理，支持精细化的数据权限隔离、Excel 导入导出、主题切换等功能，已达到生产级水准。

重构状态：完成（三大核心模块完全独立、路由规范、权限体系完善）

## 主要特性

- **三大核心模块高度独立**
  - 网格管理（Grids）
  - 小区/建筑管理（Buildings）
  - 人员管理（People）
- **路由规范**
  - 统一复数路径：`/grids`、`/people`、`/buildings`
  - 每个模块独立蓝图，便于维护与扩展
- **完整权限体系**
  - 角色控制（admin / 网格员）
  - 通配符权限 + 网格级数据隔离（网格员只能查看/操作自己网格数据）
- **数据导入导出**
  - 支持人员、小区/建筑 Excel 批量导入
  - 导出文件带中文表头 + 第二行注释说明
  - 文件存储于独立 `downloads/` 目录
- **用户体验优化**
  - 个人设置：真实姓名显示、分页大小、主题切换（多套自定义主题）
  - 完全自定义样式，已彻底移除 Bootstrap
  - 响应式布局，适配 PC / 平板 / 手机
- **安全与稳定**
  - 软删除机制
  - 详细操作日志
  - 缓存自动清理

## 项目结构
Cortana-grid/
├── app.py                      # 主入口，蓝图注册
├── run.sh                      # 智能启动脚本（支持 SQLite / MySQL 切换）
├── clear_cache.py              # 缓存清理工具
├── requirements.txt            # 依赖列表
├── schema.sql                  # 数据库结构
├── downloads/                  # 导出文件存储目录（git 忽略）
├── static/
│   ├── css/style.css           # 核心自定义样式
│   ├── themes/.css            # 多主题样式
│   ├── js/.js                 # 自定义脚本（开关、照片预览等）
│   ├── uploads/                # 人员照片上传目录
│   └── favicon.ico
├── templates/
│   ├── people.html             # 人员列表
│   ├── buildings.html          # 小区/建筑列表
│   ├── grids.html              # 网格列表
│   ├── import_export.html      # 导入导出中心
│   ├── includes/               # 组件（_navbar.html、_styles.html、_scripts.html 等）
│   └── errors/                 # 错误页面
├── routes/                     # 路由蓝图
│   ├── main.py
│   ├── grid.py
│   ├── person.py
│   ├── building.py
│   ├── import_export.py
│   └── system_settings.py
├── repositories/               # 数据访问层（DAO）
│   ├── base.py
│   ├── grid_repo.py
│   ├── person_repo.py
│   ├── building_repo.py
│   └── ...
├── services/                   # 业务逻辑层
│   └── import_export_service.py
├── permissions.py              # 权限装饰器 + 工具函数（含 get_user_grid_ids）
└── code2ai.py                  # 项目代码打包工具（用于 AI 分析或备份）


## 快速启动
./run.sh

脚本会启动虚拟环境，自动下载需要的模块。
系统默认运行在 http://127.0.0.1:5000


## 权限说明

super admin：超级管理员，可操作全部数据 默认密码 a12345678
community admin：社区管理员，可导出导入内容
网格员：普通用户，仅能查看/编辑/导出自己负责网格下的建筑和人员
建议日常使用将文件交给社区管理员导入导出


## 与AI的沟通交流工具

打包与备份使用内置工具生成纯代码包（不含数据库、导出文件、照片）：

python code2ai.py

生成的 .txt 文件位于 code2ai/ 目录，适合提交 AI 分析、文档归档或版本评审。




