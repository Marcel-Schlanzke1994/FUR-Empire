ALTER TABLE system_announcements ADD COLUMN publish_at BIGINT NOT NULL DEFAULT 0;
ALTER TABLE system_announcements ADD COLUMN emergency INTEGER NOT NULL DEFAULT 0 CHECK(emergency IN (0,1));
UPDATE system_announcements SET publish_at=created WHERE publish_at=0;
CREATE INDEX system_announcements_publish_idx ON system_announcements(publish_at,created DESC,id DESC);
INSERT INTO schema_versions(version) VALUES (103) ON CONFLICT(version) DO NOTHING;
