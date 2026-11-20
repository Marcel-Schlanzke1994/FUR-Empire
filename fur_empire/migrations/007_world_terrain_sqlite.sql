CREATE TABLE world_terrain(
    world_id INTEGER NOT NULL REFERENCES world(id) ON DELETE CASCADE,
    x INTEGER NOT NULL CHECK(x BETWEEN 0 AND 63),
    y INTEGER NOT NULL CHECK(y BETWEEN 0 AND 63),
    terrain TEXT NOT NULL CHECK(terrain IN ('plain','forest','water','mountain','pass')),
    PRIMARY KEY(world_id,x,y)
);
CREATE INDEX world_terrain_kind ON world_terrain(world_id,terrain,x,y);
INSERT INTO schema_versions(version) VALUES (7) ON CONFLICT(version) DO NOTHING;
