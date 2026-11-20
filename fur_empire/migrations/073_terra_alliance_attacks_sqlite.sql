CREATE TABLE terra_alliance_attacks (
  id TEXT PRIMARY KEY,
  world_id INTEGER NOT NULL REFERENCES world(id),
  alliance_id TEXT NOT NULL REFERENCES alliances(id),
  leader_id TEXT NOT NULL REFERENCES users(id),
  target_kind TEXT NOT NULL CHECK(target_kind IN ('outpost','player')),
  target_id TEXT NOT NULL,
  capture BOOLEAN NOT NULL DEFAULT FALSE,
  status TEXT NOT NULL CHECK(status IN ('assembling','resolved','cancelled')),
  created BIGINT NOT NULL,
  join_until BIGINT NOT NULL,
  due BIGINT NOT NULL,
  max_travel INTEGER NOT NULL CHECK(max_travel>0),
  rule_version TEXT NOT NULL REFERENCES rule_catalogs(version),
  resolved_at BIGINT,
  CHECK(due>=join_until)
);
CREATE INDEX terra_alliance_attacks_due ON terra_alliance_attacks(status,due,id);
CREATE INDEX terra_alliance_attacks_open ON terra_alliance_attacks(alliance_id,world_id,status,join_until);
CREATE TABLE terra_alliance_attack_wings (
  attack_id TEXT NOT NULL REFERENCES terra_alliance_attacks(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES users(id),
  colony_id TEXT NOT NULL REFERENCES colonies(colony_id),
  army TEXT NOT NULL,
  tactics INTEGER NOT NULL CHECK(tactics>=0),
  logistics INTEGER NOT NULL CHECK(logistics>=0),
  travel_seconds INTEGER NOT NULL CHECK(travel_seconds>0),
  status TEXT NOT NULL CHECK(status IN ('active','withdrawn','returning','returned','excluded')),
  joined_at BIGINT NOT NULL,
  PRIMARY KEY(attack_id,user_id),
  UNIQUE(attack_id,colony_id)
);
CREATE INDEX terra_alliance_attack_wings_user ON terra_alliance_attack_wings(user_id,status,attack_id);
