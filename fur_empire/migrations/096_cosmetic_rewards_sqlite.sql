ALTER TABLE player_profile_settings ADD COLUMN reward_title_id TEXT NOT NULL DEFAULT 'none'
  CHECK(reward_title_id IN ('none','frontier_founder','citadel_warden'));
ALTER TABLE player_profile_settings ADD COLUMN skin_id TEXT NOT NULL DEFAULT 'none'
  CHECK(skin_id IN ('none','ash_guard','citadel_guard'));
ALTER TABLE player_profile_settings ADD COLUMN banner_id TEXT NOT NULL DEFAULT 'none'
  CHECK(banner_id IN ('none','frontier_dawn','citadel_standard'));
CREATE TABLE player_cosmetic_unlocks(
  user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  cosmetic_id TEXT NOT NULL CHECK(cosmetic_id IN (
    'title:frontier_founder','title:citadel_warden',
    'skin:ash_guard','skin:citadel_guard',
    'banner:frontier_dawn','banner:citadel_standard'
  )),
  source_directive TEXT NOT NULL CHECK(source_directive IN ('army','expansion','victory')),
  rules_version TEXT NOT NULL CHECK(rules_version='FUR-3-COSMETIC-REWARDS-1'),
  created INTEGER NOT NULL,
  PRIMARY KEY(user_id,cosmetic_id)
);
INSERT INTO schema_versions(version) VALUES (96);
