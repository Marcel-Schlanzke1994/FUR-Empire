BEGIN IMMEDIATE;
CREATE TABLE world_rule_rollouts_new(
  id TEXT PRIMARY KEY,
  world_id INTEGER NOT NULL REFERENCES world(id) ON DELETE CASCADE,
  rule_key TEXT NOT NULL CHECK(rule_key IN ('terra_combat_ruleset','crafting_ruleset','hero_ruleset','hero_doctrine_ruleset','hero_respec_ruleset','npc_camps_ruleset')),
  target_version TEXT NOT NULL,
  active_at BIGINT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','applied','cancelled','failed')),
  failure_code TEXT,
  created_by TEXT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  created BIGINT NOT NULL,
  completed BIGINT,
  UNIQUE(world_id,rule_key,id)
);
INSERT INTO world_rule_rollouts_new(id,world_id,rule_key,target_version,active_at,status,failure_code,created_by,created,completed)
SELECT id,world_id,rule_key,target_version,active_at,status,failure_code,created_by,created,completed
FROM world_rule_rollouts;
DROP TABLE world_rule_rollouts;
ALTER TABLE world_rule_rollouts_new RENAME TO world_rule_rollouts;
CREATE UNIQUE INDEX world_rule_rollouts_one_pending
  ON world_rule_rollouts(world_id,rule_key) WHERE status='pending';
CREATE INDEX world_rule_rollouts_due ON world_rule_rollouts(status,active_at,id);
INSERT INTO schema_versions(version) VALUES (108) ON CONFLICT(version) DO NOTHING;
COMMIT;
