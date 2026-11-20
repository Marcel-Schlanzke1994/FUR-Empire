ALTER TABLE npc_camps ADD COLUMN x INTEGER CHECK(x BETWEEN 0 AND 63);
ALTER TABLE npc_camps ADD COLUMN y INTEGER CHECK(y BETWEEN 0 AND 63);
ALTER TABLE npc_camps ADD COLUMN target_outpost_id TEXT;
ALTER TABLE npc_camps ADD CONSTRAINT npc_camps_coordinates_pair
  CHECK((x IS NULL AND y IS NULL) OR (x IS NOT NULL AND y IS NOT NULL));
CREATE TABLE npc_camp_intel(
  world_id BIGINT NOT NULL,
  camp_id TEXT NOT NULL,
  target_id TEXT NOT NULL,
  x INTEGER NOT NULL CHECK(x BETWEEN 0 AND 63),
  y INTEGER NOT NULL CHECK(y BETWEEN 0 AND 63),
  observed_owner BOOLEAN NOT NULL,
  tier INTEGER NOT NULL CHECK(tier BETWEEN 0 AND 8),
  defense INTEGER NOT NULL CHECK(defense>=0),
  observed_at BIGINT NOT NULL,
  PRIMARY KEY(world_id,camp_id,target_id),
  FOREIGN KEY(world_id,camp_id) REFERENCES npc_camps(world_id,camp_id) ON DELETE CASCADE
);
CREATE INDEX npc_camp_intel_recent
  ON npc_camp_intel(world_id,camp_id,observed_at DESC,target_id);
INSERT INTO schema_versions(version) VALUES (110) ON CONFLICT(version) DO NOTHING;
