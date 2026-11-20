CREATE TABLE IF NOT EXISTS alliance_wars(
  id TEXT PRIMARY KEY,
  alliance_a TEXT NOT NULL REFERENCES alliances(id),
  alliance_b TEXT NOT NULL REFERENCES alliances(id),
  rules_version TEXT NOT NULL,
  rules_digest TEXT NOT NULL CHECK(length(rules_digest)=71),
  target_points INTEGER NOT NULL CHECK(target_points>0),
  score_a BIGINT NOT NULL DEFAULT 0 CHECK(score_a>=0),
  score_b BIGINT NOT NULL DEFAULT 0 CHECK(score_b>=0),
  status TEXT NOT NULL CHECK(status IN ('active','peace_offered','ended')),
  peace_offered_by TEXT REFERENCES alliances(id),
  winner TEXT REFERENCES alliances(id),
  end_reason TEXT CHECK(end_reason IS NULL OR end_reason IN ('peace','objective','objective_draw')),
  started BIGINT NOT NULL,
  ended BIGINT,
  CHECK(alliance_a<alliance_b),
  CHECK(peace_offered_by IS NULL OR peace_offered_by IN (alliance_a,alliance_b)),
  CHECK(winner IS NULL OR winner IN (alliance_a,alliance_b)),
  CHECK((status='ended' AND ended IS NOT NULL AND end_reason IS NOT NULL) OR
        (status<>'ended' AND ended IS NULL AND end_reason IS NULL))
);
CREATE INDEX alliance_wars_public ON alliance_wars(started DESC,id DESC);
CREATE INDEX alliance_wars_pair_active ON alliance_wars(alliance_a,alliance_b,status,started DESC);
CREATE TABLE IF NOT EXISTS alliance_war_battles(
  id TEXT PRIMARY KEY,
  war_id TEXT NOT NULL REFERENCES alliance_wars(id),
  mission_id TEXT NOT NULL,
  world_id INTEGER NOT NULL REFERENCES world(id),
  attacker_alliance TEXT NOT NULL REFERENCES alliances(id),
  defender_alliance TEXT NOT NULL REFERENCES alliances(id),
  attacker_losses INTEGER NOT NULL CHECK(attacker_losses>=0),
  defender_losses INTEGER NOT NULL CHECK(defender_losses>=0),
  rules_version TEXT NOT NULL,
  created BIGINT NOT NULL,
  UNIQUE(war_id,mission_id),
  CHECK(attacker_alliance<>defender_alliance)
);
CREATE TABLE IF NOT EXISTS alliance_war_score_ledger(
  war_id TEXT NOT NULL REFERENCES alliance_wars(id),
  mission_id TEXT NOT NULL,
  alliance_id TEXT NOT NULL REFERENCES alliances(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  category TEXT NOT NULL CHECK(category IN ('attack','defense')),
  points INTEGER NOT NULL CHECK(points>0),
  created BIGINT NOT NULL,
  PRIMARY KEY(war_id,mission_id,alliance_id,user_id,category)
);
CREATE INDEX alliance_war_score_feed ON alliance_war_score_ledger(war_id,created,alliance_id);
CREATE TRIGGER alliance_war_battles_no_update BEFORE UPDATE ON alliance_war_battles
  BEGIN SELECT RAISE(ABORT,'alliance war battles are immutable'); END;
CREATE TRIGGER alliance_war_battles_no_delete BEFORE DELETE ON alliance_war_battles
  BEGIN SELECT RAISE(ABORT,'alliance war battles are immutable'); END;
CREATE TABLE IF NOT EXISTS alliance_war_events(
  id TEXT PRIMARY KEY,
  war_id TEXT NOT NULL REFERENCES alliance_wars(id),
  event_type TEXT NOT NULL CHECK(event_type IN (
    'declared','battle_score','peace_offered','peace_declined','peace_cancelled',
    'ended_peace','ended_objective'
  )),
  actor_alliance TEXT REFERENCES alliances(id),
  details TEXT NOT NULL,
  created BIGINT NOT NULL
);
CREATE INDEX alliance_war_events_feed ON alliance_war_events(war_id,created DESC,id DESC);
CREATE TRIGGER alliance_war_events_no_update BEFORE UPDATE ON alliance_war_events
  BEGIN SELECT RAISE(ABORT,'alliance war events are immutable'); END;
CREATE TRIGGER alliance_war_events_no_delete BEFORE DELETE ON alliance_war_events
  BEGIN SELECT RAISE(ABORT,'alliance war events are immutable'); END;
CREATE TRIGGER alliance_war_score_no_update BEFORE UPDATE ON alliance_war_score_ledger
  BEGIN SELECT RAISE(ABORT,'alliance war score is immutable'); END;
CREATE TRIGGER alliance_war_score_no_delete BEFORE DELETE ON alliance_war_score_ledger
  BEGIN SELECT RAISE(ABORT,'alliance war score is immutable'); END;
INSERT INTO schema_versions(version) VALUES (85) ON CONFLICT(version) DO NOTHING;
