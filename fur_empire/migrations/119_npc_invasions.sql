BEGIN;
CREATE TABLE IF NOT EXISTS npc_invasions (
    id TEXT PRIMARY KEY,
    world_id BIGINT NOT NULL REFERENCES world(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    rules_version TEXT NOT NULL REFERENCES rule_catalogs(version),
    rules_digest TEXT NOT NULL,
    budget INTEGER NOT NULL CHECK(budget > 0),
    created BIGINT NOT NULL,
    starts BIGINT NOT NULL CHECK(starts > created),
    ends BIGINT NOT NULL CHECK(ends > starts)
);
CREATE INDEX IF NOT EXISTS npc_invasions_world ON npc_invasions(world_id, ends, id);

CREATE TABLE IF NOT EXISTS npc_invasion_attacks (
    mission_id TEXT PRIMARY KEY REFERENCES npc_attack_missions(id) ON DELETE CASCADE,
    invasion_id TEXT NOT NULL REFERENCES npc_invasions(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS npc_invasion_attacks_invasion ON npc_invasion_attacks(invasion_id);
INSERT INTO schema_versions(version) VALUES (119) ON CONFLICT(version) DO NOTHING;
COMMIT;
