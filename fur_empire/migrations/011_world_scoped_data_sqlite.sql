BEGIN IMMEDIATE;
ALTER TABLE messages ADD COLUMN world_id INTEGER NOT NULL DEFAULT 1 CHECK(world_id>0);
ALTER TABLE offers ADD COLUMN world_id INTEGER NOT NULL DEFAULT 1 CHECK(world_id>0);
ALTER TABLE offers ADD COLUMN colony_id TEXT REFERENCES colonies(colony_id);
UPDATE offers SET colony_id=(
    SELECT colony_id FROM colonies
    WHERE colonies.user_id=offers.owner
      AND colonies.world_id=offers.world_id
      AND colonies.is_home=1
) WHERE colony_id IS NULL;
ALTER TABLE player_intel ADD COLUMN world_id INTEGER NOT NULL DEFAULT 1 CHECK(world_id>0);
ALTER TABLE map_bookmarks ADD COLUMN world_id INTEGER NOT NULL DEFAULT 1 CHECK(world_id>0);
CREATE INDEX messages_world_feed ON messages(world_id,channel,created DESC,id);
CREATE INDEX offers_world_open ON offers(world_id,status,expires,id);
CREATE INDEX player_intel_world ON player_intel(observer_id,world_id,expires_at,target_id);
CREATE INDEX map_bookmarks_world_order ON map_bookmarks(user_id,world_id,created,target_id);
INSERT INTO schema_versions(version) VALUES (11) ON CONFLICT(version) DO NOTHING;
COMMIT;
