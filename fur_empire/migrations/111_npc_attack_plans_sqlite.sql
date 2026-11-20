BEGIN IMMEDIATE;
CREATE TABLE npc_attack_plans(
  id TEXT PRIMARY KEY,
  world_id INTEGER NOT NULL,
  cycle INTEGER NOT NULL,
  camp_id TEXT NOT NULL,
  target_id TEXT NOT NULL,
  target_owner TEXT NOT NULL,
  target_name TEXT NOT NULL,
  target_x INTEGER NOT NULL CHECK(target_x BETWEEN 0 AND 63),
  target_y INTEGER NOT NULL CHECK(target_y BETWEEN 0 AND 63),
  units TEXT NOT NULL,
  rules_version TEXT NOT NULL,
  rules_digest TEXT NOT NULL,
  created BIGINT NOT NULL,
  UNIQUE(world_id,cycle),
  CHECK(length(camp_id)>0)
);
CREATE INDEX npc_attack_plans_target_feed
  ON npc_attack_plans(world_id,target_owner,created DESC,id);
CREATE TRIGGER npc_attack_plans_no_update
BEFORE UPDATE ON npc_attack_plans
BEGIN SELECT RAISE(ABORT,'npc attack plans are immutable'); END;
CREATE TRIGGER npc_attack_plans_no_delete
BEFORE DELETE ON npc_attack_plans
BEGIN SELECT RAISE(ABORT,'npc attack plans are immutable'); END;
INSERT INTO schema_versions(version) VALUES (111) ON CONFLICT(version) DO NOTHING;
COMMIT;
