-- schema.sql
-- 社区网格化人口管理系统数据库结构（生产级终极版 - 2026-02-09）
-- 核心设计原则：支持软删除、网格隔离、灵活导入、家庭/户籍关联
-- 关键更新记录：
--   2026-01-06：gender 和 phones 允许为空（现实常见未填写情况）
--   2026-02-09：新增 relationship 字段（人员间关系自由文本）、unique_id、passport 等扩展字段
--   建筑类型限制为枚举值，增加商业相关字段

-- ==================== 用户相关表 ====================

-- 用户表
CREATE TABLE IF NOT EXISTS user (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    username            TEXT UNIQUE NOT NULL,
    password_hash       TEXT NOT NULL,
    full_name           TEXT,
    phone               TEXT,
    page_size           INTEGER DEFAULT 20,
    preferred_css       TEXT DEFAULT '',
    is_active           INTEGER DEFAULT 1,
    must_change_password INTEGER DEFAULT 0,
    is_deleted          INTEGER DEFAULT 0
);

-- 角色表
CREATE TABLE IF NOT EXISTS role (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT UNIQUE NOT NULL
);

-- 角色权限表
CREATE TABLE IF NOT EXISTS role_permission (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id     INTEGER NOT NULL,
    permission  TEXT NOT NULL,
    FOREIGN KEY (role_id) REFERENCES role (id) ON DELETE CASCADE
);

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS user_role (
    user_id  INTEGER,
    role_id  INTEGER,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id)  REFERENCES user (id)  ON DELETE CASCADE,
    FOREIGN KEY (role_id)  REFERENCES role (id)  ON DELETE CASCADE
);

-- 用户负责的网格（多对多）
CREATE TABLE IF NOT EXISTS user_grid (
    user_id  INTEGER,
    grid_id  INTEGER,
    PRIMARY KEY (user_id, grid_id),
    FOREIGN KEY (user_id) REFERENCES user (id)   ON DELETE CASCADE,
    FOREIGN KEY (grid_id) REFERENCES grid (id)   ON DELETE CASCADE
);

-- ==================== 网格与建筑表 ====================

-- 网格表
CREATE TABLE IF NOT EXISTS grid (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    is_deleted  INTEGER DEFAULT 0
);

-- 小区/建筑表
CREATE TABLE IF NOT EXISTS building (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    name                        TEXT NOT NULL,
    type                        TEXT NOT NULL DEFAULT 'residential_complex'
        CHECK(type IN ('residential_complex', 'private_residence', 'large_rental', 'commercial')),
    grid_id                     INTEGER,
    address                     TEXT,
    build_year                  INTEGER,
    households                  INTEGER,
    buildings_count             INTEGER,
    approx_residents            INTEGER,
    businesses_count            INTEGER,
    ground_floor_shops          INTEGER,
    has_gas_pipeline            INTEGER DEFAULT 0 CHECK(has_gas_pipeline IN (0, 1)),
    property_fee                TEXT,                    -- 可存 "1.2元/㎡·月" 等文本格式
    elevators                   INTEGER,
    indoor_parking              INTEGER,
    outdoor_parking             INTEGER,
    security_manager            TEXT,
    security_manager_phone      TEXT,
    latitude                    REAL,
    longitude                   REAL,
    developer                   TEXT,
    constructor                 TEXT,
    property_management_company TEXT,
    property_contact_phone      TEXT,
    owners_committee_contact    TEXT,
    owners_committee_phone      TEXT,
    owner_name                  TEXT,
    owner_phone                 TEXT,
    landlord_name               TEXT,
    landlord_phone              TEXT,
    commercial_type             TEXT,
    is_external                 INTEGER DEFAULT 0,
    notes                       TEXT,
    is_deleted                  INTEGER DEFAULT 0,
    
    FOREIGN KEY (grid_id) REFERENCES grid (id) ON DELETE SET NULL,
    UNIQUE (name, grid_id)
);

-- ==================== 人员表（核心表） ====================

CREATE TABLE IF NOT EXISTS person (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    unique_id               TEXT UNIQUE,                          -- 系统内部唯一标识（可选用于导入去重）
    name                    TEXT NOT NULL,
    id_card                 TEXT UNIQUE,
    passport                TEXT,
    other_id_type           TEXT,                                 -- 其他证件类型
    gender                  TEXT CHECK(gender IN ('男', '女')),   -- 允许为空
    birth_date              TEXT,                                 -- 建议格式 YYYY-MM-DD
    phones                  TEXT,                                 -- 允许多个，用逗号或分号分隔
    address_detail          TEXT NOT NULL,                        -- 现住详细地址（房号等）
    relationship            TEXT,                                 -- 与其他人员关系（自由文本）
    person_type             TEXT DEFAULT '常住人口' 
        CHECK(person_type IN ('常住人口', '流动人口')),
    is_key_person           INTEGER DEFAULT 0,
    key_categories          TEXT,                                 -- 重点人员分类，可多选逗号分隔
    nationality             TEXT,
    political_status        TEXT,
    marital_status          TEXT,
    education               TEXT,
    work_study              TEXT,
    health                  TEXT,
    notes                   TEXT,
    images                  TEXT,                                 -- 图片路径或ID列表，逗号分隔
    living_building_id      INTEGER,
    household_building_id   INTEGER,
    household_address       TEXT,
    family_id               TEXT,                                 -- 家庭编号
    household_number        TEXT,                                 -- 户号
    household_entry_date    TEXT,
    is_migrated_out         INTEGER DEFAULT 0,
    household_exit_date     TEXT,
    migration_destination   TEXT,
    is_deceased             INTEGER DEFAULT 0,
    death_date              TEXT,
    is_separated            INTEGER DEFAULT 0,
    current_residence       TEXT,
    updated_at              TEXT DEFAULT (datetime('now', 'localtime')),
    is_deleted              INTEGER DEFAULT 0,

    FOREIGN KEY (living_building_id)    REFERENCES building (id) ON DELETE SET NULL,
    FOREIGN KEY (household_building_id) REFERENCES building (id) ON DELETE SET NULL
);

-- ==================== 系统设置表 ====================

CREATE TABLE IF NOT EXISTS settings (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);

-- ==================== 性能优化索引 ====================

-- 人员表常用查询字段
CREATE INDEX IF NOT EXISTS idx_person_name               ON person (name);
CREATE INDEX IF NOT EXISTS idx_person_id_card             ON person (id_card);
CREATE INDEX IF NOT EXISTS idx_person_family_id           ON person (family_id);
CREATE INDEX IF NOT EXISTS idx_person_household_number    ON person (household_number);
CREATE INDEX IF NOT EXISTS idx_person_living_building_id  ON person (living_building_id);
CREATE INDEX IF NOT EXISTS idx_person_household_building_id ON person (household_building_id);

-- 建筑表常用字段
CREATE INDEX IF NOT EXISTS idx_building_grid_id           ON building (grid_id);
CREATE INDEX IF NOT EXISTS idx_building_type              ON building (type);
CREATE INDEX IF NOT EXISTS idx_building_name              ON building (name);

-- 用户相关索引（视查询频率可选添加）
-- CREATE INDEX IF NOT EXISTS idx_user_username           ON user (username);
-- CREATE INDEX IF NOT EXISTS idx_user_grid_user_id       ON user_grid (user_id);
