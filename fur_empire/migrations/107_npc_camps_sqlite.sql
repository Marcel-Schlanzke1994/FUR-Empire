BEGIN IMMEDIATE;
CREATE TABLE npc_camps(
    world_id INTEGER NOT NULL REFERENCES world(id) ON DELETE CASCADE,
    camp_id TEXT NOT NULL,
    profile_id TEXT NOT NULL CHECK(profile_id IN ('ash_covenant','iron_compact','thorn_conclave','dawn_accord','tide_syndicate')),
    position INTEGER NOT NULL CHECK(position BETWEEN 0 AND 4),
    resources TEXT NOT NULL,
    units TEXT NOT NULL,
    movement_quota INTEGER NOT NULL CHECK(movement_quota BETWEEN 0 AND 4),
    deployment_quota INTEGER NOT NULL CHECK(deployment_quota BETWEEN 0 AND 8),
    quota_checked_at BIGINT NOT NULL,
    created BIGINT NOT NULL,
    PRIMARY KEY(world_id,camp_id),
    UNIQUE(world_id,profile_id),
    UNIQUE(world_id,position)
);
CREATE TABLE npc_camp_events(
    event_id TEXT PRIMARY KEY,
    world_id INTEGER NOT NULL,
    camp_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('resupply','scout','reinforce','fortify','maneuver','deploy')),
    payload TEXT NOT NULL,
    created BIGINT NOT NULL,
    FOREIGN KEY(world_id,camp_id) REFERENCES npc_camps(world_id,camp_id) ON DELETE CASCADE
);
CREATE INDEX npc_camp_events_page ON npc_camp_events(world_id,camp_id,created DESC,event_id);
INSERT INTO schema_versions(version) VALUES (107) ON CONFLICT(version) DO NOTHING;
COMMIT;
