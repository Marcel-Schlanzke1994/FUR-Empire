CREATE TABLE IF NOT EXISTS alliance_role_permissions(
  alliance_id TEXT NOT NULL REFERENCES alliances(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK(role IN ('officer','member')),
  permission TEXT NOT NULL CHECK(permission IN (
    'applications','invitations','description','member_removal',
    'diplomacy','bulletin','forum_moderation'
  )),
  PRIMARY KEY(alliance_id,role,permission)
);
CREATE INDEX IF NOT EXISTS alliance_role_permissions_lookup
  ON alliance_role_permissions(alliance_id,role);
INSERT OR IGNORE INTO alliance_role_permissions(alliance_id,role,permission)
SELECT a.id,'officer',permission
FROM alliances a
CROSS JOIN (SELECT 'applications' AS permission UNION ALL SELECT 'invitations'
  UNION ALL SELECT 'description' UNION ALL SELECT 'member_removal'
  UNION ALL SELECT 'diplomacy' UNION ALL SELECT 'bulletin'
  UNION ALL SELECT 'forum_moderation') defaults;
INSERT INTO schema_versions(version) VALUES (83) ON CONFLICT(version) DO NOTHING;
