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
INSERT INTO alliance_role_permissions(alliance_id,role,permission)
SELECT a.id,'officer',permission
FROM alliances a
CROSS JOIN (VALUES ('applications'),('invitations'),('description'),('member_removal'),
  ('diplomacy'),('bulletin'),('forum_moderation')) defaults(permission)
ON CONFLICT(alliance_id,role,permission) DO NOTHING;
INSERT INTO schema_versions(version) VALUES (83) ON CONFLICT(version) DO NOTHING;
