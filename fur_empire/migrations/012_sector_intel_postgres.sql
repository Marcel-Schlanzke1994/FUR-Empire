CREATE TABLE map_sector_intel(
    observer_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    world_id INTEGER NOT NULL REFERENCES world(id) ON DELETE CASCADE,
    x INTEGER NOT NULL CHECK(x BETWEEN 0 AND 63),
    y INTEGER NOT NULL CHECK(y BETWEEN 0 AND 63),
    observed_at BIGINT NOT NULL,
    PRIMARY KEY(observer_id,world_id,x,y)
);
CREATE INDEX map_sector_intel_world ON map_sector_intel(observer_id,world_id,observed_at);
INSERT INTO schema_versions(version) VALUES (12) ON CONFLICT(version) DO NOTHING;
