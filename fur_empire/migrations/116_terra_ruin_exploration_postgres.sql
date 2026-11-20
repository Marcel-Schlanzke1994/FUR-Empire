BEGIN;
CREATE TABLE terra_ruin_explorations(
  mission_id TEXT PRIMARY KEY,
  world_id BIGINT NOT NULL REFERENCES world(id) ON DELETE CASCADE,
  owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  ruin_id TEXT NOT NULL,
  x INTEGER NOT NULL CHECK(x BETWEEN 0 AND 63),
  y INTEGER NOT NULL CHECK(y BETWEEN 0 AND 63),
  rules_version TEXT NOT NULL REFERENCES rule_catalogs(version),
  rules_digest TEXT NOT NULL CHECK(length(rules_digest)=71),
  seed TEXT NOT NULL CHECK(length(seed)=64),
  seed_commitment TEXT NOT NULL CHECK(length(seed_commitment)=64),
  created BIGINT NOT NULL,
  expires BIGINT NOT NULL CHECK(expires>created),
  resolved BIGINT,
  outcome TEXT,
  CHECK((resolved IS NULL AND outcome IS NULL) OR (resolved IS NOT NULL AND outcome IS NOT NULL))
);
CREATE INDEX terra_ruin_explorations_owner ON terra_ruin_explorations(owner_id,world_id,created,mission_id);
CREATE TABLE terra_ruin_intel(
  observer_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  world_id BIGINT NOT NULL REFERENCES world(id) ON DELETE CASCADE,
  ruin_id TEXT NOT NULL,
  x INTEGER NOT NULL CHECK(x BETWEEN 0 AND 63),
  y INTEGER NOT NULL CHECK(y BETWEEN 0 AND 63),
  observed_at BIGINT NOT NULL,
  expires_at BIGINT NOT NULL CHECK(expires_at>observed_at),
  outcome TEXT NOT NULL,
  PRIMARY KEY(observer_id,world_id,ruin_id)
);
CREATE INDEX terra_ruin_intel_expiry ON terra_ruin_intel(observer_id,world_id,expires_at);
INSERT INTO schema_versions(version) VALUES (116) ON CONFLICT(version) DO NOTHING;
COMMIT;
