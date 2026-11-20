-- Earlier share projections used the attacker's side for every report and
-- cannot be repaired from their redacted summaries. Revoke them before exposing
-- new owner-perspective projections.
DELETE FROM alliance_shared_reports;
INSERT INTO schema_versions(version) VALUES (105) ON CONFLICT(version) DO NOTHING;
