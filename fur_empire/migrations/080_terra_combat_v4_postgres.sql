ALTER TABLE world_settings DROP CONSTRAINT world_settings_terra_combat_ruleset_check;
ALTER TABLE world_settings ADD CONSTRAINT world_settings_terra_combat_ruleset_check
  CHECK(terra_combat_ruleset IN ('FUR-2','FUR-3-TERRA-COMBAT-1','FUR-3-TERRA-COMBAT-2','FUR-3-TERRA-COMBAT-3','FUR-3-TERRA-COMBAT-4'));
INSERT INTO schema_versions(version) VALUES (80);
