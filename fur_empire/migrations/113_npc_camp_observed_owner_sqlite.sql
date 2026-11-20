BEGIN IMMEDIATE;
ALTER TABLE npc_camp_intel ADD COLUMN observed_owner_id TEXT;
CREATE INDEX npc_camp_intel_observed_target
  ON npc_camp_intel(world_id,target_id,observed_at,observed_owner_id);
INSERT INTO schema_versions(version) VALUES (113) ON CONFLICT(version) DO NOTHING;
COMMIT;
