CREATE TABLE game_event_preferences(
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  category TEXT NOT NULL CHECK(category IN ('economy','research','military','social','system')),
  muted INTEGER NOT NULL DEFAULT 0 CHECK(muted IN (0,1)),
  updated BIGINT NOT NULL,
  PRIMARY KEY(user_id,category)
);
CREATE TABLE game_event_delivery_failures(
  id TEXT PRIMARY KEY,
  recipient TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  world_id INTEGER NOT NULL REFERENCES world(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  attempts INTEGER NOT NULL CHECK(attempts > 0),
  failed_at BIGINT NOT NULL
);
CREATE INDEX game_event_delivery_failures_owner
  ON game_event_delivery_failures(recipient,world_id,failed_at DESC,id DESC);
