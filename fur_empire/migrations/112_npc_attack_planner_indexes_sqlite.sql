BEGIN IMMEDIATE;
CREATE INDEX npc_attack_plans_recent_owner
  ON npc_attack_plans(world_id,created,target_owner);
CREATE INDEX npc_attack_plans_recent_camp
  ON npc_attack_plans(world_id,created,camp_id);
INSERT INTO schema_versions(version) VALUES (112) ON CONFLICT(version) DO NOTHING;
COMMIT;
