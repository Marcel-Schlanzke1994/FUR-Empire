CREATE TABLE player_intel(
    observer_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 2),
    observed_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL CHECK(expires_at>observed_at),
    data TEXT NOT NULL,
    PRIMARY KEY(observer_id,target_id),
    CHECK(observer_id<>target_id)
);
CREATE INDEX player_intel_expiry ON player_intel(observer_id,expires_at,target_id);
INSERT INTO schema_versions(version) VALUES (6) ON CONFLICT(version) DO NOTHING;
