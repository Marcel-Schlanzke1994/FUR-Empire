BEGIN IMMEDIATE;
ALTER TABLE colonies RENAME TO colonies_v4;
CREATE TABLE colonies(
    colony_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    world_id INTEGER NOT NULL DEFAULT 1 CHECK(world_id>0),
    is_home INTEGER NOT NULL DEFAULT 0 CHECK(is_home IN (0,1)),
    x INTEGER NOT NULL CHECK(x BETWEEN 0 AND 63),
    y INTEGER NOT NULL CHECK(y BETWEEN 0 AND 63),
    state TEXT NOT NULL
);
INSERT INTO colonies(colony_id,user_id,world_id,is_home,x,y,state)
    SELECT user_id,user_id,1,1,json_extract(state,'$.x'),json_extract(state,'$.y'),state
    FROM colonies_v4;
DROP TABLE colonies_v4;
CREATE INDEX colonies_owner_world ON colonies(user_id,world_id,colony_id);
CREATE UNIQUE INDEX colonies_one_home_per_world ON colonies(user_id,world_id) WHERE is_home=1;
CREATE UNIQUE INDEX colonies_unique_sector ON colonies(world_id,x,y);
ALTER TABLE profiles ADD COLUMN active_colony_id TEXT;
UPDATE profiles SET active_colony_id=(
    SELECT colony_id FROM colonies
    WHERE colonies.user_id=profiles.user_id AND colonies.is_home=1
);
INSERT INTO schema_versions(version) VALUES (5) ON CONFLICT(version) DO NOTHING;
COMMIT;
