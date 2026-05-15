USE china_heritage_platform;

INSERT INTO users (openid, nickname, role) VALUES
('demo_openid_admin', '管理员', 'admin'),
('demo_openid_user', '普通用户', 'user');

INSERT INTO contents (title, content_type, summary, body, status) VALUES
('昆曲艺术导读', 'article', '昆曲基本审美与入门路径', '昆曲以曲词、身段与水磨腔见长，是中国传统戏曲的重要代表。', 'published');

INSERT INTO activities (title, location, start_time, end_time, max_participants, description, status) VALUES
('非遗体验公开课', '市民文化中心', '2026-05-01 09:00:00', '2026-05-01 11:00:00', 100, '面向公众的非遗体验课程与讲解。', 'open');
