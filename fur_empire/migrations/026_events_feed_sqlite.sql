CREATE INDEX IF NOT EXISTS events_feed
  ON events(starts DESC,id DESC,ends);
