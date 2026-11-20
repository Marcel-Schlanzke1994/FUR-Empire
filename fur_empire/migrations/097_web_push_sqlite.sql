CREATE TABLE web_push_subscriptions(
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  endpoint TEXT NOT NULL UNIQUE,
  p256dh TEXT NOT NULL,
  auth TEXT NOT NULL,
  created BIGINT NOT NULL,
  updated BIGINT NOT NULL,
  failures INTEGER NOT NULL DEFAULT 0 CHECK(failures >= 0),
  last_sequence BIGINT NOT NULL DEFAULT 0
);
CREATE INDEX web_push_subscriptions_user ON web_push_subscriptions(user_id,updated DESC,id);
CREATE TABLE web_push_outbox(
  id TEXT PRIMARY KEY,
  subscription_id TEXT NOT NULL REFERENCES web_push_subscriptions(id) ON DELETE CASCADE,
  event_id TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts >= 0),
  available_at BIGINT NOT NULL,
  lease_until BIGINT NOT NULL DEFAULT 0,
  created BIGINT NOT NULL,
  UNIQUE(subscription_id,event_id)
);
CREATE INDEX web_push_outbox_due ON web_push_outbox(available_at,created,id);
