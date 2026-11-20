CREATE TABLE IF NOT EXISTS war_score_ledger(
  id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL,
  world_id INTEGER NOT NULL REFERENCES world(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  category TEXT NOT NULL CHECK(category IN ('attack','defense','support')),
  points INTEGER NOT NULL CHECK(points >= 0),
  rules_version TEXT NOT NULL,
  created BIGINT NOT NULL,
  UNIQUE(mission_id,user_id,category)
);
CREATE INDEX IF NOT EXISTS war_score_world_user ON war_score_ledger(world_id,user_id,category);
CREATE TRIGGER IF NOT EXISTS war_score_ledger_no_update
  BEFORE UPDATE ON war_score_ledger
  BEGIN SELECT RAISE(ABORT,'war score ledger is immutable'); END;
CREATE TRIGGER IF NOT EXISTS war_score_ledger_no_delete
  BEFORE DELETE ON war_score_ledger
  BEGIN SELECT RAISE(ABORT,'war score ledger is immutable'); END;
INSERT INTO schema_versions(version) VALUES (82) ON CONFLICT(version) DO NOTHING;
