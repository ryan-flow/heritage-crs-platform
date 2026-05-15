-- ============================================================
-- 非遗文化传播平台 — 数据库Schema
-- 从SQLite自动导出 + 手动格式化
-- 表数量: 16（原5张 → 现完整16张）
-- ============================================================

-- -----------------------------------------------------------
-- 1. users 用户表
-- -----------------------------------------------------------
CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY,
    openid VARCHAR(64) NOT NULL,
    nickname VARCHAR(64),
    phone VARCHAR(20),
    role VARCHAR(20) NOT NULL,
    is_active BOOLEAN NOT NULL,
    preferred_heritage_types TEXT,        -- JSON数组：["工艺","戏曲"]
    preferred_scene_types TEXT,           -- JSON数组：["知识阅读","活动体验"]
    preferred_regions TEXT,               -- JSON数组：["华南","华东"]
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    -- CRS v2.0 置信度字段
    confidence_score REAL DEFAULT 0,      -- 综合置信度 C (0-100)
    score_explicit REAL DEFAULT 0,        -- 显式偏好维度分 (0-100)
    score_implicit REAL DEFAULT 0,        -- 隐式行为维度分 (0-100)
    score_dialogue REAL DEFAULT 0         -- 对话语义维度分 (0-100)
);
CREATE UNIQUE INDEX ix_users_openid ON users (openid);
CREATE INDEX ix_users_id ON users (id);

-- -----------------------------------------------------------
-- 2. contents 内容表
-- -----------------------------------------------------------
CREATE TABLE contents (
    id INTEGER NOT NULL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    cover_url VARCHAR(255),
    content_type VARCHAR(30) NOT NULL,
    source_site VARCHAR(120),
    source_url VARCHAR(500),
    summary TEXT,
    body TEXT,
    chapter VARCHAR(120),
    sub_chapter VARCHAR(120),
    content_hash VARCHAR(40),
    quality_score FLOAT NOT NULL,
    review_status VARCHAR(20) NOT NULL,
    import_batch VARCHAR(60),
    is_featured BOOLEAN NOT NULL,
    status VARCHAR(20) NOT NULL,
    published_at DATETIME,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX ix_contents_id ON contents (id);

-- -----------------------------------------------------------
-- 3. activities 活动表
-- -----------------------------------------------------------
CREATE TABLE activities (
    id INTEGER NOT NULL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    cover_url VARCHAR(255),
    location VARCHAR(200),
    organizer VARCHAR(120),
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    max_participants INTEGER NOT NULL,
    description TEXT,
    notes TEXT,
    is_featured BOOLEAN NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX ix_activities_id ON activities (id);

-- -----------------------------------------------------------
-- 4. activity_registrations 活动报名表
-- -----------------------------------------------------------
CREATE TABLE activity_registrations (
    id INTEGER NOT NULL PRIMARY KEY,
    activity_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    remark VARCHAR(255),
    status VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uk_activity_user UNIQUE (activity_id, user_id)
);
CREATE INDEX ix_activity_registrations_activity_id ON activity_registrations (activity_id);
CREATE INDEX ix_activity_registrations_user_id ON activity_registrations (user_id);

-- -----------------------------------------------------------
-- 5. ai_qa_logs AI问答记录表
-- -----------------------------------------------------------
CREATE TABLE ai_qa_logs (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    source VARCHAR(30) NOT NULL,
    confidence NUMERIC(4, 2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX ix_ai_qa_logs_user_id ON ai_qa_logs (user_id);

-- -----------------------------------------------------------
-- 6. crs_sessions CRS会话状态表 (v2.0新增)
-- -----------------------------------------------------------
CREATE TABLE crs_sessions (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    mode VARCHAR(20) NOT NULL,            -- cold_start / mixed / precision
    turn_count INTEGER NOT NULL DEFAULT 0,
    last_ask_attribute VARCHAR(30),        -- 最近ASK的属性：category/region/scene/level
    last_ask_id VARCHAR(10),              -- 最近ASK模板ID：A01/B02/R01等
    asked_attributes TEXT DEFAULT "[]",    -- JSON数组：完整已问属性列表
    context_summary TEXT,                  -- 对话上下文摘要
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE UNIQUE INDEX ix_crs_sessions_session_id ON crs_sessions (session_id);
CREATE INDEX ix_crs_sessions_user_id ON crs_sessions (user_id);

-- -----------------------------------------------------------
-- 7. crs_ask_logs CRS提问记录表 (v2.0新增)
-- -----------------------------------------------------------
CREATE TABLE crs_ask_logs (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    ask_id VARCHAR(10) NOT NULL,          -- A01-A05 / B01-B05 / R01-R03
    attribute VARCHAR(30) NOT NULL,       -- category / region / scene / level
    question_text TEXT NOT NULL,          -- 提问原文
    answer TEXT,                          -- 用户回答
    score_delta INTEGER NOT NULL,         -- 本次回答带来的置信度增量
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX ix_crs_ask_logs_session_id ON crs_ask_logs (session_id);
CREATE INDEX ix_crs_ask_logs_user_id ON crs_ask_logs (user_id);

-- -----------------------------------------------------------
-- 8. recommend_logs 推荐记录表
-- -----------------------------------------------------------
CREATE TABLE recommend_logs (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(20) NOT NULL,          -- impression / click / dismiss
    target_type VARCHAR(20) NOT NULL,     -- content / activity / topic
    target_id INTEGER NOT NULL,
    source_scene VARCHAR(30),             -- ai / home / discover
    explain_json TEXT,                    -- 推荐解释（算法打分明细）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX ix_recommend_logs_user_id ON recommend_logs (user_id);
CREATE INDEX ix_recommend_logs_action ON recommend_logs (action);
CREATE INDEX ix_recommend_logs_target_type ON recommend_logs (target_type);
CREATE INDEX ix_recommend_logs_target_id ON recommend_logs (target_id);

-- -----------------------------------------------------------
-- 9. local_knowledge_base 本地知识库表
-- -----------------------------------------------------------
CREATE TABLE local_knowledge_base (
    id INTEGER NOT NULL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    qa_answer TEXT,
    keywords VARCHAR(255),
    chapter VARCHAR(120),
    sub_chapter VARCHAR(120),
    source VARCHAR(100),
    status VARCHAR(20) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX ix_local_knowledge_base_id ON local_knowledge_base (id);

-- -----------------------------------------------------------
-- 10. electronic_materials 电子资料表
-- -----------------------------------------------------------
CREATE TABLE electronic_materials (
    id INTEGER NOT NULL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    file_url VARCHAR(255) NOT NULL,
    file_type VARCHAR(30) NOT NULL,
    summary TEXT,
    status VARCHAR(20) NOT NULL,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX ix_electronic_materials_id ON electronic_materials (id);

-- -----------------------------------------------------------
-- 11. discussion_topics 讨论话题表
-- -----------------------------------------------------------
CREATE TABLE discussion_topics (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    nickname VARCHAR(64),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    cover_url VARCHAR(255),
    image_urls TEXT,
    is_featured BOOLEAN NOT NULL,
    like_count INTEGER NOT NULL DEFAULT 0,
    favorite_count INTEGER NOT NULL DEFAULT 0,
    comment_count INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX ix_discussion_topics_user_id ON discussion_topics (user_id);

-- -----------------------------------------------------------
-- 12. discussion_comments 讨论评论表
-- -----------------------------------------------------------
CREATE TABLE discussion_comments (
    id INTEGER NOT NULL PRIMARY KEY,
    topic_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    nickname TEXT,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX ix_discussion_comments_topic_id ON discussion_comments (topic_id);
CREATE INDEX ix_discussion_comments_user_id ON discussion_comments (user_id);

-- -----------------------------------------------------------
-- 13. discussion_likes 讨论点赞表
-- -----------------------------------------------------------
CREATE TABLE discussion_likes (
    id INTEGER NOT NULL PRIMARY KEY,
    topic_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uk_topic_user_like UNIQUE (topic_id, user_id)
);
CREATE INDEX ix_discussion_likes_topic_id ON discussion_likes (topic_id);
CREATE INDEX ix_discussion_likes_user_id ON discussion_likes (user_id);

-- -----------------------------------------------------------
-- 14. discussion_favorites 讨论收藏表
-- -----------------------------------------------------------
CREATE TABLE discussion_favorites (
    id INTEGER NOT NULL PRIMARY KEY,
    topic_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uk_topic_user_favorite UNIQUE (topic_id, user_id)
);
CREATE INDEX ix_discussion_favorites_topic_id ON discussion_favorites (topic_id);
CREATE INDEX ix_discussion_favorites_user_id ON discussion_favorites (user_id);

-- -----------------------------------------------------------
-- 15. discussion_topic_tags 讨论标签表
-- -----------------------------------------------------------
CREATE TABLE discussion_topic_tags (
    id INTEGER NOT NULL PRIMARY KEY,
    topic_id INTEGER NOT NULL,
    tag VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE INDEX ix_discussion_topic_tags_topic_id ON discussion_topic_tags (topic_id);
CREATE INDEX ix_discussion_topic_tags_tag ON discussion_topic_tags (tag);

-- -----------------------------------------------------------
-- 16. content_favorites 内容收藏表
-- -----------------------------------------------------------
CREATE TABLE content_favorites (
    id INTEGER NOT NULL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    content_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uk_user_content_favorite UNIQUE (user_id, content_id)
);
CREATE INDEX ix_content_favorites_user_id ON content_favorites (user_id);
CREATE INDEX ix_content_favorites_content_id ON content_favorites (content_id);
