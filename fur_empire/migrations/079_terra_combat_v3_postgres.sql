ALTER TABLE world_settings DROP CONSTRAINT world_settings_terra_combat_ruleset_check;
ALTER TABLE world_settings ADD CONSTRAINT world_settings_terra_combat_ruleset_check
  CHECK(terra_combat_ruleset IN ('FUR-2','FUR-3-TERRA-COMBAT-1','FUR-3-TERRA-COMBAT-2','FUR-3-TERRA-COMBAT-3'));
ALTER TABLE terra_allied_garrisons ADD COLUMN travel_seconds INTEGER NOT NULL DEFAULT 0 CHECK(travel_seconds>=0);
INSERT INTO schema_versions(version) VALUES (79);
