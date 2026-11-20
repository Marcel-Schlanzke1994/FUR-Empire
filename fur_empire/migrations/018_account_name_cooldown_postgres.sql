ALTER TABLE profiles ADD COLUMN name_changed BIGINT NOT NULL DEFAULT 0;
INSERT INTO schema_versions(version) VALUES (18) ON CONFLICT(version) DO NOTHING;
