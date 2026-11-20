CREATE TABLE prestige_records(
  user_id TEXT NOT NULL REFERENCES users(id),
  source_key TEXT NOT NULL,
  source_type TEXT NOT NULL CHECK(source_type IN ('campaign_victory','season_champion','season_goal_achieved')),
  world_id INTEGER NOT NULL REFERENCES world(id),
  prestige_level INTEGER NOT NULL CHECK(prestige_level BETWEEN 1 AND 3),
  rules_version TEXT NOT NULL,
  source_id TEXT NOT NULL,
  created BIGINT NOT NULL,
  PRIMARY KEY(user_id,source_key)
);
CREATE INDEX prestige_records_user ON prestige_records(user_id,created DESC,source_key);
CREATE TRIGGER prestige_records_no_update BEFORE UPDATE ON prestige_records
  BEGIN SELECT RAISE(ABORT,'prestige records are immutable'); END;
CREATE TRIGGER prestige_records_no_delete BEFORE DELETE ON prestige_records
  BEGIN SELECT RAISE(ABORT,'prestige records are immutable'); END;
INSERT INTO schema_versions(version) VALUES (102) ON CONFLICT(version) DO NOTHING;
