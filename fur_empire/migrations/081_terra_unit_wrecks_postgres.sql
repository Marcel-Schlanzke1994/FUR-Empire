CREATE TABLE terra_unit_wrecks (
    id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    colony_id TEXT NOT NULL REFERENCES colonies(colony_id) ON DELETE CASCADE,
    world_id INTEGER NOT NULL REFERENCES world(id) ON DELETE CASCADE,
    unit_id TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK(amount>=0),
    expires BIGINT NOT NULL,
    created BIGINT NOT NULL,
    rule_version TEXT NOT NULL REFERENCES rule_catalogs(version),
    rule_digest TEXT NOT NULL,
    UNIQUE(mission_id,colony_id,unit_id)
);
CREATE INDEX terra_unit_wrecks_owner_expiry
    ON terra_unit_wrecks(owner_id,world_id,colony_id,expires,id) WHERE amount>0;
INSERT INTO schema_versions(version) VALUES (81);
