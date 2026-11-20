ALTER TABLE world_settings
ADD COLUMN terra_retreat_threshold_percent INTEGER NOT NULL DEFAULT 60
CHECK(terra_retreat_threshold_percent BETWEEN 1 AND 100);

INSERT INTO schema_versions(version) VALUES (76);
