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
CREATE OR REPLACE FUNCTION reject_war_score_ledger_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'war score ledger is immutable';
END;
$$;
CREATE TRIGGER war_score_ledger_no_update
  BEFORE UPDATE OR DELETE ON war_score_ledger
  FOR EACH ROW EXECUTE FUNCTION reject_war_score_ledger_mutation();
INSERT INTO schema_versions(version) VALUES (82) ON CONFLICT(version) DO NOTHING;
