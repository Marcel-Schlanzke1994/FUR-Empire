ALTER TABLE sessions ADD COLUMN session_id TEXT;
ALTER TABLE sessions ADD COLUMN created BIGINT NOT NULL DEFAULT 0;
ALTER TABLE sessions ADD COLUMN user_agent TEXT NOT NULL DEFAULT '';
CREATE UNIQUE INDEX IF NOT EXISTS sessions_session_id_unique ON sessions(session_id);
INSERT INTO schema_versions(version) VALUES (16) ON CONFLICT(version) DO NOTHING;
