CREATE TABLE world_rule_rollouts(
  id TEXT PRIMARY KEY,
  world_id BIGINT NOT NULL REFERENCES world(id) ON DELETE CASCADE,
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
CREATE UNIQUE INDEX world_rule_rollouts_one_pending
  ON world_rule_rollouts(world_id,rule_key) WHERE status='pending';
CREATE INDEX world_rule_rollouts_due ON world_rule_rollouts(status,active_at,id);
INSERT INTO schema_versions(version) VALUES (104) ON CONFLICT(version) DO NOTHING;
