BEGIN;
CREATE TABLE npc_convoys (
    id TEXT PRIMARY KEY,
    world_id BIGINT NOT NULL REFERENCES world(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    rules_version TEXT NOT NULL REFERENCES rule_catalogs(version),
    rules_digest TEXT NOT NULL,
    route TEXT NOT NULL,
    starts BIGINT NOT NULL,
    ends BIGINT NOT NULL CHECK(ends > starts)
);
CREATE INDEX npc_convoys_by_world ON npc_convoys(world_id, ends);
CREATE TABLE npc_convoy_participants (
    convoy_id TEXT NOT NULL REFERENCES npc_convoys(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    mission_id TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK(role IN ('escort', 'raid')),
    rangers INTEGER NOT NULL CHECK(rangers > 0 AND rangers <= 40),
    stage INTEGER NOT NULL CHECK(stage >= 0 AND stage < 3),
    started BIGINT NOT NULL,
    due BIGINT NOT NULL CHECK(due > started),
    travel_seconds INTEGER NOT NULL CHECK(travel_seconds > 0),
    status TEXT NOT NULL DEFAULT 'marching' CHECK(status IN ('marching','completed','cancelled')),
    victory INTEGER CHECK(victory IN (0,1)),
    survivors INTEGER CHECK(survivors >= 0 AND survivors <= rangers),
    reward_ore INTEGER NOT NULL DEFAULT 0 CHECK(reward_ore >= 0 AND reward_ore <= 300),
    claimed_at BIGINT,
    PRIMARY KEY(convoy_id,user_id)
);
INSERT INTO schema_versions(version) VALUES (121) ON CONFLICT(version) DO NOTHING;
COMMIT;
