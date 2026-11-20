ALTER TABLE world_settings
ADD COLUMN terra_combat_ruleset TEXT NOT NULL DEFAULT 'FUR-2'
CHECK(terra_combat_ruleset IN ('FUR-2','FUR-3-TERRA-COMBAT-1'));

CREATE TABLE terra_combat_missions (
  mission_id TEXT PRIMARY KEY,
  world_id INTEGER NOT NULL REFERENCES world(id) ON DELETE CASCADE,
  rules_version TEXT NOT NULL REFERENCES rule_catalogs(version),
  rules_digest TEXT NOT NULL CHECK(length(rules_digest)=71),
  seed TEXT NOT NULL CHECK(length(seed)=64),
  seed_commitment TEXT NOT NULL CHECK(length(seed_commitment)=64),
  retreat_threshold_percent INTEGER NOT NULL CHECK(retreat_threshold_percent BETWEEN 1 AND 100),
  created BIGINT NOT NULL,
  resolved BIGINT,
  replay TEXT,
  CHECK((resolved IS NULL AND replay IS NULL) OR (resolved IS NOT NULL AND replay IS NOT NULL))
);
CREATE INDEX terra_combat_missions_world ON terra_combat_missions(world_id,created,mission_id);
INSERT INTO schema_versions(version) VALUES (75);
