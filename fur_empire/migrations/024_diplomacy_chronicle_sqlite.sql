CREATE TABLE alliance_diplomacy_events(
  id TEXT PRIMARY KEY,
  alliance_a TEXT NOT NULL REFERENCES alliances(id),
  alliance_b TEXT NOT NULL REFERENCES alliances(id),
  actor_alliance TEXT NOT NULL REFERENCES alliances(id),
  event_type TEXT NOT NULL CHECK(event_type IN ('nap_proposed','nap_accepted','war_declared','neutralized')),
  created BIGINT NOT NULL,
  CHECK(alliance_a < alliance_b),
  CHECK(actor_alliance IN (alliance_a,alliance_b))
);
CREATE INDEX alliance_diplomacy_events_feed
  ON alliance_diplomacy_events(created DESC,id DESC);
CREATE TRIGGER alliance_diplomacy_events_no_update
  BEFORE UPDATE ON alliance_diplomacy_events
  BEGIN SELECT RAISE(ABORT,'alliance diplomacy events are immutable'); END;
CREATE TRIGGER alliance_diplomacy_events_no_delete
  BEFORE DELETE ON alliance_diplomacy_events
  BEGIN SELECT RAISE(ABORT,'alliance diplomacy events are immutable'); END;
INSERT INTO schema_versions(version) VALUES (24) ON CONFLICT(version) DO NOTHING;
