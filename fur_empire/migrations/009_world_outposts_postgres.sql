CREATE TABLE IF NOT EXISTS world_outposts(
    world_id INTEGER NOT NULL REFERENCES world(id),
    target_id TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    x INTEGER NOT NULL CHECK(x BETWEEN 0 AND 63),
    y INTEGER NOT NULL CHECK(y BETWEEN 0 AND 63),
    state TEXT NOT NULL,
    PRIMARY KEY(world_id,target_id),
    UNIQUE(world_id,x,y)
);
CREATE INDEX IF NOT EXISTS world_outposts_order ON world_outposts(world_id,sort_order,target_id);
