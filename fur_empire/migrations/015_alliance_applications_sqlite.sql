CREATE TABLE IF NOT EXISTS alliance_applications (
    id TEXT PRIMARY KEY,
    alliance_id TEXT NOT NULL REFERENCES alliances(id),
    user_id TEXT NOT NULL REFERENCES users(id),
    created BIGINT NOT NULL,
    UNIQUE(alliance_id, user_id)
);
CREATE INDEX IF NOT EXISTS alliance_applications_user
    ON alliance_applications(user_id, created);
INSERT INTO schema_versions(version) VALUES (15) ON CONFLICT(version) DO NOTHING;
