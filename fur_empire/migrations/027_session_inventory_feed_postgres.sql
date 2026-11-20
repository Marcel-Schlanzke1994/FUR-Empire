CREATE INDEX IF NOT EXISTS sessions_owner_feed
  ON sessions(user_id,created DESC,session_id DESC,expires);
