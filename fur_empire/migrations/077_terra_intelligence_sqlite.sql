CREATE TABLE terra_intel_missions(
  mission_id TEXT PRIMARY KEY,
  world_id INTEGER NOT NULL REFERENCES world(id) ON DELETE CASCADE,
  attacker_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  defender_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  rules_version TEXT NOT NULL REFERENCES rule_catalogs(version),
  rules_digest TEXT NOT NULL CHECK(length(rules_digest)=71),
  seed TEXT NOT NULL CHECK(length(seed)=64),
  seed_commitment TEXT NOT NULL CHECK(length(seed_commitment)=64),
  interception_percent INTEGER NOT NULL CHECK(interception_percent BETWEEN 0 AND 50),
  detection_percent INTEGER NOT NULL CHECK(detection_percent BETWEEN 0 AND 60),
  created BIGINT NOT NULL,
  resolved BIGINT,
  outcome TEXT,
  CHECK((resolved IS NULL AND outcome IS NULL) OR (resolved IS NOT NULL AND outcome IS NOT NULL))
);
CREATE INDEX terra_intel_missions_world ON terra_intel_missions(world_id,created,mission_id);
CREATE INDEX terra_intel_missions_defender ON terra_intel_missions(defender_id,created,mission_id);
INSERT INTO schema_versions(version) VALUES (77);
