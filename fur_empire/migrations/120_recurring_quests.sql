BEGIN;
CREATE TABLE recurring_quest_windows (
    id TEXT PRIMARY KEY,
    world_id BIGINT NOT NULL REFERENCES world(id) ON DELETE CASCADE,
    rules_version TEXT NOT NULL REFERENCES rule_catalogs(version),
    starts BIGINT NOT NULL,
    ends BIGINT CHECK(ends >= starts)
);
CREATE UNIQUE INDEX recurring_quests_one_open_window
ON recurring_quest_windows(world_id) WHERE ends IS NULL;
CREATE INDEX recurring_quest_windows_by_time ON recurring_quest_windows(world_id, starts);

CREATE TABLE recurring_quest_progress (
    world_id BIGINT NOT NULL REFERENCES world(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rules_version TEXT NOT NULL REFERENCES rule_catalogs(version),
    period_start BIGINT NOT NULL,
    quest_id TEXT NOT NULL,
    progress INTEGER NOT NULL CHECK(progress > 0),
    claimed_at BIGINT CHECK(claimed_at >= period_start),
    PRIMARY KEY (world_id, user_id, rules_version, period_start, quest_id)
);
INSERT INTO schema_versions(version) VALUES (120) ON CONFLICT(version) DO NOTHING;
COMMIT;
