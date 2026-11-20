ALTER TABLE world DROP CONSTRAINT world_id_check;
ALTER TABLE world ADD CONSTRAINT world_id_positive CHECK(id>0);

ALTER TABLE profiles ADD COLUMN active_world_id INTEGER;
UPDATE profiles
SET active_world_id=(
    SELECT world_id FROM colonies
    WHERE colonies.colony_id=profiles.active_colony_id
);
CREATE TABLE world_settings(
    world_id INTEGER PRIMARY KEY REFERENCES world(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    seed BIGINT NOT NULL,
    outpost_count INTEGER NOT NULL CHECK(outpost_count BETWEEN 0 AND 500),
    joinable BOOLEAN NOT NULL DEFAULT TRUE,
    created BIGINT NOT NULL,
    settings TEXT NOT NULL DEFAULT '{}'
);
CREATE UNIQUE INDEX world_settings_name_unique ON world_settings(lower(name));
INSERT INTO world_settings(world_id,name,seed,outpost_count,joinable,created,settings)
SELECT id,'Genesis',504921,104,TRUE,0,'{}' FROM world;
INSERT INTO schema_versions(version) VALUES (10) ON CONFLICT(version) DO NOTHING;
