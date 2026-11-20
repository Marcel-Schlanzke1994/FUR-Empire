CREATE TABLE npc_attack_plans(
  id TEXT PRIMARY KEY,
  world_id BIGINT NOT NULL,
  cycle BIGINT NOT NULL,
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
CREATE FUNCTION reject_npc_attack_plan_mutation() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'npc attack plans are immutable'; END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER npc_attack_plans_no_update BEFORE UPDATE OR DELETE ON npc_attack_plans
  FOR EACH ROW EXECUTE FUNCTION reject_npc_attack_plan_mutation();
INSERT INTO schema_versions(version) VALUES (111) ON CONFLICT(version) DO NOTHING;
