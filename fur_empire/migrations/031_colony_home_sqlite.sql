BEGIN IMMEDIATE;
CREATE TABLE colony_home_changes (
    owner TEXT NOT NULL REFERENCES users(id),
    world_id INTEGER NOT NULL REFERENCES world(id),
    changed BIGINT NOT NULL CHECK(changed >= 0),
    next_change BIGINT NOT NULL CHECK(next_change > changed),
    rule_version TEXT NOT NULL,
    rule_hash TEXT NOT NULL,
    PRIMARY KEY(owner, world_id)
);
INSERT INTO schema_versions(version) VALUES (31) ON CONFLICT(version) DO NOTHING;
COMMIT;
