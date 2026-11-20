ALTER TABLE events ADD COLUMN warning_hours INTEGER NOT NULL DEFAULT 0 CHECK(warning_hours BETWEEN 0 AND 168);
ALTER TABLE events ADD COLUMN end_starts BIGINT NOT NULL DEFAULT 0 CHECK(end_starts>=0);
ALTER TABLE events ADD COLUMN end_bonus INTEGER NOT NULL DEFAULT 0 CHECK(end_bonus BETWEEN 0 AND 100);
ALTER TABLE events ADD COLUMN goal_score BIGINT NOT NULL DEFAULT 0 CHECK(goal_score BETWEEN 0 AND 1000000000);
UPDATE events SET end_starts=ends,end_bonus=bonus;
CREATE TABLE live_event_rules(
  event_id TEXT PRIMARY KEY REFERENCES events(id),
  version TEXT NOT NULL,
  snapshot TEXT NOT NULL,
  digest TEXT NOT NULL CHECK(length(digest)=64),
  source TEXT NOT NULL CHECK(source IN ('admin_create','legacy_backfill'))
);
CREATE OR REPLACE FUNCTION prevent_live_event_rule_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'live event rules are immutable'; END; $$;
CREATE TRIGGER live_event_rules_no_update_delete BEFORE UPDATE OR DELETE ON live_event_rules
FOR EACH ROW EXECUTE FUNCTION prevent_live_event_rule_mutation();
