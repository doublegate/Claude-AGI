-- Phase 2 Database Schema Extensions
-- Claude-AGI Learning and Knowledge Management Tables

-- Learning goals table
CREATE TABLE learning_goals (
    id UUID PRIMARY KEY,
    goal_type VARCHAR(50),
    description TEXT,
    status VARCHAR(20),
    progress FLOAT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Knowledge graph nodes
CREATE TABLE knowledge_nodes (
    id UUID PRIMARY KEY,
    concept VARCHAR(255),
    definition TEXT,
    embedding VECTOR(768),
    confidence FLOAT,
    source_id UUID
);

-- Skills table
CREATE TABLE skills (
    id UUID PRIMARY KEY,
    skill_name VARCHAR(255),
    proficiency_level FLOAT,
    practice_hours FLOAT,
    last_practiced TIMESTAMP
);