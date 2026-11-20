BEGIN;
CREATE TABLE IF NOT EXISTS terra_boss_raids (
    id TEXT PRIMARY KEY,
    world_id BIGINT NOT NULL REFERENCES world(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    rules_version TEXT NOT NULL REFERENCES rule_catalogs(version),
    rules_digest TEXT NOT NULL,
    health INTEGER NOT NULL CHECK(health > 0),
    remaining_health INTEGER NOT NULL CHECK(remaining_health BETWEEN 0 AND health),
    starts BIGINT NOT NULL,
    ends BIGINT NOT NULL CHECK(ends > starts),
    defeated_at BIGINT,
    CHECK((remaining_health = 0 AND defeated_at IS NOT NULL)
        OR (remaining_health > 0 AND defeated_at IS NULL))
);
CREATE INDEX IF NOT EXISTS terra_boss_raids_world ON terra_boss_raids(world_id, starts, id);

CREATE TABLE IF NOT EXISTS terra_boss_contributions (
    raid_id TEXT NOT NULL REFERENCES terra_boss_raids(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mission_id TEXT NOT NULL UNIQUE,
    rangers INTEGER NOT NULL CHECK(rangers BETWEEN 1 AND 40),
    due BIGINT NOT NULL,
    damage INTEGER CHECK(damage >= 0),
    survivors INTEGER CHECK(survivors BETWEEN 0 AND rangers),
    claimed_at BIGINT,
    PRIMARY KEY(raid_id, user_id),
    CHECK((damage IS NULL) = (survivors IS NULL)),
    CHECK(claimed_at IS NULL OR (damage IS NOT NULL AND damage > 0))
);
CREATE INDEX IF NOT EXISTS terra_boss_contributions_player ON terra_boss_contributions(user_id, raid_id);
INSERT INTO schema_versions(version) VALUES (118) ON CONFLICT(version) DO NOTHING;
COMMIT;
