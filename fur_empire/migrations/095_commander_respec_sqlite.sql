ALTER TABLE commander_heroes ADD COLUMN last_respec_at INTEGER;
INSERT INTO schema_versions(version) VALUES (95);
