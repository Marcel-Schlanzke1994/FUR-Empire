DROP INDEX IF EXISTS alliance_role_permissions_lookup;
ALTER TABLE alliance_role_permissions RENAME TO alliance_role_permissions_v83;
CREATE TABLE alliance_role_permissions(
  alliance_id TEXT NOT NULL REFERENCES alliances(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK(role IN ('officer','member')),
  permission TEXT NOT NULL CHECK(permission IN (
    'applications','invitations','description','member_removal',
    'diplomacy','bulletin','forum_moderation','treasury'
  )),
  PRIMARY KEY(alliance_id,role,permission)
);
INSERT INTO alliance_role_permissions(alliance_id,role,permission)
  SELECT alliance_id,role,permission FROM alliance_role_permissions_v83;
INSERT INTO alliance_role_permissions(alliance_id,role,permission)
  SELECT id,'officer','treasury' FROM alliances
  WHERE NOT EXISTS (
    SELECT 1 FROM alliance_role_permissions p
    WHERE p.alliance_id=alliances.id AND p.role='officer' AND p.permission='treasury'
  );
DROP TABLE alliance_role_permissions_v83;
CREATE INDEX alliance_role_permissions_lookup ON alliance_role_permissions(alliance_id,role);
CREATE TABLE alliance_treasury_balances(
  alliance_id TEXT NOT NULL REFERENCES alliances(id) ON DELETE CASCADE,
  world_id INTEGER NOT NULL REFERENCES world(id),
  resource_index INTEGER NOT NULL CHECK(resource_index BETWEEN 0 AND 2),
  available BIGINT NOT NULL DEFAULT 0 CHECK(available>=0),
  reserved BIGINT NOT NULL DEFAULT 0 CHECK(reserved>=0),
  PRIMARY KEY(alliance_id,world_id,resource_index)
);
CREATE TABLE alliance_treasury_requests(
  id TEXT PRIMARY KEY,
  alliance_id TEXT NOT NULL REFERENCES alliances(id),
  world_id INTEGER NOT NULL REFERENCES world(id),
  requester_id TEXT NOT NULL REFERENCES users(id),
  destination_colony_id TEXT NOT NULL REFERENCES colonies(colony_id),
  gross_json TEXT NOT NULL,
  fee_json TEXT NOT NULL,
  net_json TEXT NOT NULL,
  required_approvals INTEGER NOT NULL CHECK(required_approvals IN (1,2)),
  rules_version TEXT NOT NULL,
  rules_digest TEXT NOT NULL CHECK(length(rules_digest)=71),
  status TEXT NOT NULL CHECK(status IN ('pending','paid','declined','cancelled','expired','void_membership')),
  created BIGINT NOT NULL,
  expires BIGINT NOT NULL CHECK(expires>created),
  completed BIGINT
);
CREATE INDEX alliance_treasury_request_page
  ON alliance_treasury_requests(alliance_id,world_id,status,created DESC,id DESC);
CREATE TABLE alliance_treasury_approvals(
  request_id TEXT NOT NULL REFERENCES alliance_treasury_requests(id),
  approver_id TEXT NOT NULL REFERENCES users(id),
  approved_at BIGINT NOT NULL,
  PRIMARY KEY(request_id,approver_id)
);
CREATE TABLE alliance_treasury_ledger(
  id TEXT PRIMARY KEY,
  entry_key TEXT NOT NULL,
  alliance_id TEXT NOT NULL REFERENCES alliances(id),
  world_id INTEGER NOT NULL REFERENCES world(id),
  actor_id TEXT NOT NULL,
  request_id TEXT REFERENCES alliance_treasury_requests(id),
  resource_index INTEGER NOT NULL CHECK(resource_index BETWEEN 0 AND 2),
  event_type TEXT NOT NULL CHECK(event_type IN (
    'donation','withdrawal_reserved','withdrawal_paid','withdrawal_refund'
  )),
  delta_available BIGINT NOT NULL,
  delta_reserved BIGINT NOT NULL,
  details TEXT NOT NULL,
  rules_version TEXT NOT NULL,
  created BIGINT NOT NULL,
  UNIQUE(entry_key,resource_index)
);
CREATE INDEX alliance_treasury_ledger_page
  ON alliance_treasury_ledger(alliance_id,world_id,created DESC,id DESC);
CREATE TRIGGER alliance_treasury_ledger_no_update BEFORE UPDATE ON alliance_treasury_ledger
  BEGIN SELECT RAISE(ABORT,'alliance treasury ledger is immutable'); END;
CREATE TRIGGER alliance_treasury_ledger_no_delete BEFORE DELETE ON alliance_treasury_ledger
  BEGIN SELECT RAISE(ABORT,'alliance treasury ledger is immutable'); END;
CREATE TRIGGER alliance_treasury_approvals_no_update BEFORE UPDATE ON alliance_treasury_approvals
  BEGIN SELECT RAISE(ABORT,'alliance treasury approvals are immutable'); END;
CREATE TRIGGER alliance_treasury_approvals_no_delete BEFORE DELETE ON alliance_treasury_approvals
  BEGIN SELECT RAISE(ABORT,'alliance treasury approvals are immutable'); END;
INSERT INTO schema_versions(version) VALUES (87) ON CONFLICT(version) DO NOTHING;
