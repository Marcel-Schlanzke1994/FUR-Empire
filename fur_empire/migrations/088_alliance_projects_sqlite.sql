DROP INDEX IF EXISTS alliance_role_permissions_lookup;
ALTER TABLE alliance_role_permissions RENAME TO alliance_role_permissions_v87;
CREATE TABLE alliance_role_permissions(
  alliance_id TEXT NOT NULL REFERENCES alliances(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK(role IN ('officer','member')),
  permission TEXT NOT NULL CHECK(permission IN (
    'applications','invitations','description','member_removal',
    'diplomacy','bulletin','forum_moderation','treasury','projects'
  )),
  PRIMARY KEY(alliance_id,role,permission)
);
INSERT INTO alliance_role_permissions(alliance_id,role,permission)
  SELECT alliance_id,role,permission FROM alliance_role_permissions_v87;
INSERT INTO alliance_role_permissions(alliance_id,role,permission)
  SELECT id,'officer','projects' FROM alliances
  WHERE NOT EXISTS (
    SELECT 1 FROM alliance_role_permissions p
    WHERE p.alliance_id=alliances.id AND p.role='officer' AND p.permission='projects'
  );
DROP TABLE alliance_role_permissions_v87;
CREATE INDEX alliance_role_permissions_lookup ON alliance_role_permissions(alliance_id,role);
CREATE TABLE alliance_projects(
  id TEXT PRIMARY KEY,
  alliance_id TEXT NOT NULL REFERENCES alliances(id),
  world_id INTEGER NOT NULL REFERENCES world(id),
  project_key TEXT NOT NULL,
  title TEXT NOT NULL,
  record_reward TEXT NOT NULL,
  target_json TEXT NOT NULL,
  contributed_json TEXT NOT NULL,
  initiator_id TEXT NOT NULL REFERENCES users(id),
  rules_version TEXT NOT NULL,
  rules_digest TEXT NOT NULL CHECK(length(rules_digest)=71),
  status TEXT NOT NULL CHECK(status IN ('active','completed','cancelled','expired')),
  created BIGINT NOT NULL,
  deadline BIGINT NOT NULL CHECK(deadline>created),
  completed BIGINT
);
CREATE UNIQUE INDEX alliance_projects_one_active
  ON alliance_projects(alliance_id,world_id) WHERE status='active';
CREATE INDEX alliance_projects_history
  ON alliance_projects(alliance_id,world_id,created DESC,id DESC);
CREATE TABLE alliance_project_contributions(
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL REFERENCES alliance_projects(id),
  user_id TEXT NOT NULL REFERENCES users(id),
  world_id INTEGER NOT NULL REFERENCES world(id),
  source_colony_id TEXT NOT NULL,
  resources_json TEXT NOT NULL,
  refunded BOOLEAN NOT NULL DEFAULT FALSE,
  created BIGINT NOT NULL
);
CREATE INDEX alliance_project_contributions_refund
  ON alliance_project_contributions(project_id,refunded,created,id);
CREATE TABLE alliance_project_ledger(
  id TEXT PRIMARY KEY,
  entry_key TEXT NOT NULL,
  project_id TEXT NOT NULL REFERENCES alliance_projects(id),
  alliance_id TEXT NOT NULL REFERENCES alliances(id),
  world_id INTEGER NOT NULL REFERENCES world(id),
  actor_id TEXT NOT NULL,
  source_colony_id TEXT,
  resource_index INTEGER NOT NULL CHECK(resource_index BETWEEN 0 AND 2),
  event_type TEXT NOT NULL CHECK(event_type IN ('contribution','refund')),
  amount INTEGER NOT NULL CHECK(amount>0),
  created BIGINT NOT NULL,
  UNIQUE(entry_key,resource_index)
);
CREATE INDEX alliance_project_ledger_page
  ON alliance_project_ledger(alliance_id,world_id,created DESC,id DESC);
CREATE TRIGGER alliance_project_ledger_no_update BEFORE UPDATE ON alliance_project_ledger
  BEGIN SELECT RAISE(ABORT,'alliance project ledger is immutable'); END;
CREATE TRIGGER alliance_project_ledger_no_delete BEFORE DELETE ON alliance_project_ledger
  BEGIN SELECT RAISE(ABORT,'alliance project ledger is immutable'); END;
INSERT INTO schema_versions(version) VALUES (88) ON CONFLICT(version) DO NOTHING;
