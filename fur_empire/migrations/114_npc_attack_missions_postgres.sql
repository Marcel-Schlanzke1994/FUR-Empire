CREATE TABLE npc_attack_missions(
  id TEXT PRIMARY KEY,
  world_id BIGINT NOT NULL REFERENCES world(id) ON DELETE CASCADE,
  plan_id TEXT NOT NULL UNIQUE REFERENCES npc_attack_plans(id),
  camp_id TEXT NOT NULL,
  target_owner TEXT NOT NULL,
  arrival BIGINT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('warning','resolving','resolved','cancelled')),
  attacker_units TEXT NOT NULL,
  seed TEXT NOT NULL,
  seed_commitment TEXT NOT NULL,
  combat_version TEXT NOT NULL,
  combat_digest TEXT NOT NULL,
  created BIGINT NOT NULL,
  resolved BIGINT,
  outcome TEXT,
  replay TEXT,
  loot TEXT,
  cancel_reason TEXT,
  CHECK(length(camp_id)>0),
  CHECK(length(target_owner)>0),
  CHECK(arrival>=created),
  CHECK((status IN ('warning','resolving') AND resolved IS NULL AND outcome IS NULL)
     OR (status IN ('resolved','cancelled') AND resolved IS NOT NULL))
);
CREATE INDEX npc_attack_missions_due
  ON npc_attack_missions(world_id,status,arrival,id);
CREATE INDEX npc_attack_missions_owner_recent
  ON npc_attack_missions(world_id,target_owner,created,status);
INSERT INTO schema_versions(version) VALUES (114) ON CONFLICT(version) DO NOTHING;
