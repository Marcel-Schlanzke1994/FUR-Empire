ALTER TABLE world_settings RENAME TO world_settings_v78;
CREATE TABLE world_settings(
    world_id INTEGER PRIMARY KEY REFERENCES world(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    seed BIGINT NOT NULL,
    outpost_count INTEGER NOT NULL CHECK(outpost_count BETWEEN 0 AND 500),
    joinable INTEGER NOT NULL DEFAULT 1 CHECK(joinable IN (0,1)),
    created BIGINT NOT NULL,
    settings TEXT NOT NULL DEFAULT '{}',
    mode TEXT NOT NULL DEFAULT 'permanent' CHECK(mode IN ('permanent','season','sandbox')),
    terra_prestige_ruleset TEXT REFERENCES rule_catalogs(version),
    terra_combat_ruleset TEXT NOT NULL DEFAULT 'FUR-2'
      CHECK(terra_combat_ruleset IN ('FUR-2','FUR-3-TERRA-COMBAT-1','FUR-3-TERRA-COMBAT-2','FUR-3-TERRA-COMBAT-3')),
    terra_retreat_threshold_percent INTEGER NOT NULL DEFAULT 60
      CHECK(terra_retreat_threshold_percent BETWEEN 1 AND 100)
);
INSERT INTO world_settings(world_id,name,seed,outpost_count,joinable,created,settings,mode,terra_prestige_ruleset,terra_combat_ruleset,terra_retreat_threshold_percent)
SELECT world_id,name,seed,outpost_count,joinable,created,settings,mode,terra_prestige_ruleset,terra_combat_ruleset,terra_retreat_threshold_percent
FROM world_settings_v78;
DROP TABLE world_settings_v78;
CREATE UNIQUE INDEX world_settings_name_unique ON world_settings(lower(name));
ALTER TABLE terra_allied_garrisons ADD COLUMN travel_seconds INTEGER NOT NULL DEFAULT 0 CHECK(travel_seconds>=0);
INSERT INTO schema_versions(version) VALUES (79);
