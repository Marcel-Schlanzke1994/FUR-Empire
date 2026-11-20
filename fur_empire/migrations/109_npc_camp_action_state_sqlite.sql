BEGIN IMMEDIATE;
ALTER TABLE npc_camps ADD COLUMN fortification_level INTEGER NOT NULL DEFAULT 0 CHECK(fortification_level BETWEEN 0 AND 10);
ALTER TABLE npc_camps ADD COLUMN scout_actions INTEGER NOT NULL DEFAULT 0 CHECK(scout_actions>=0);
ALTER TABLE npc_camps ADD COLUMN maneuver_actions INTEGER NOT NULL DEFAULT 0 CHECK(maneuver_actions>=0);
INSERT INTO schema_versions(version) VALUES (109) ON CONFLICT(version) DO NOTHING;
COMMIT;
