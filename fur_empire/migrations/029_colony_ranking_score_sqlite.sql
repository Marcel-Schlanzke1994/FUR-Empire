ALTER TABLE colonies ADD COLUMN ranking_score BIGINT NOT NULL DEFAULT 0;
CREATE INDEX colonies_world_ranking ON colonies(world_id,user_id,ranking_score);
