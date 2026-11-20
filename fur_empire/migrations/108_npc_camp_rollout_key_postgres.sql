ALTER TABLE world_rule_rollouts DROP CONSTRAINT world_rule_rollouts_rule_key_check;
ALTER TABLE world_rule_rollouts ADD CONSTRAINT world_rule_rollouts_rule_key_check
  CHECK(rule_key IN ('terra_combat_ruleset','crafting_ruleset','hero_ruleset','hero_doctrine_ruleset','hero_respec_ruleset','npc_camps_ruleset'));
INSERT INTO schema_versions(version) VALUES (108) ON CONFLICT(version) DO NOTHING;
