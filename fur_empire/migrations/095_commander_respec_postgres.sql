ALTER TABLE commander_heroes ADD COLUMN last_respec_at BIGINT;
INSERT INTO schema_versions(version) VALUES (95) ON CONFLICT(version) DO NOTHING;
