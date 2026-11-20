CREATE TABLE player_profile_settings(
  user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  visibility TEXT NOT NULL DEFAULT 'private' CHECK(visibility IN ('private','public')),
  title_id TEXT NOT NULL DEFAULT 'none' CHECK(title_id IN (
    'none','pathfinder','settler','architect','diplomat','quartermaster'
  )),
  updated BIGINT NOT NULL DEFAULT 0
);
CREATE TABLE player_profile_badges(
  user_id TEXT NOT NULL REFERENCES player_profile_settings(user_id) ON DELETE CASCADE,
  badge_id TEXT NOT NULL CHECK(badge_id IN (
    'frontier','builder','scholar','envoy','merchant','guardian'
  )),
  position INTEGER NOT NULL CHECK(position BETWEEN 0 AND 2),
  PRIMARY KEY(user_id,badge_id),
  UNIQUE(user_id,position)
);
INSERT INTO player_profile_settings(user_id,visibility,title_id,updated)
SELECT user_id,'private','none',0 FROM profiles WHERE true
ON CONFLICT(user_id) DO NOTHING;
INSERT INTO schema_versions(version) VALUES (89) ON CONFLICT(version) DO NOTHING;
