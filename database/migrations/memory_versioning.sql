-- Memory Versioning Tables for Synchronization
-- This migration adds version tracking for memory synchronization

-- Create memory versions table
CREATE TABLE IF NOT EXISTS memory_versions (
    memory_id VARCHAR(255) PRIMARY KEY,
    version INTEGER NOT NULL DEFAULT 1,
    checksum VARCHAR(64) NOT NULL,
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    store_versions JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create sync transactions table for tracking sync operations
CREATE TABLE IF NOT EXISTS sync_transactions (
    transaction_id VARCHAR(255) PRIMARY KEY,
    memory_ids TEXT[] NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    rollback_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create conflict resolutions table for audit trail
CREATE TABLE IF NOT EXISTS conflict_resolutions (
    resolution_id SERIAL PRIMARY KEY,
    memory_id VARCHAR(255) NOT NULL,
    conflict_type VARCHAR(50) NOT NULL,
    conflicting_stores TEXT[] NOT NULL,
    resolution_strategy VARCHAR(50) NOT NULL,
    original_data JSONB,
    resolved_data JSONB,
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create sync queue table for pending synchronizations
CREATE TABLE IF NOT EXISTS sync_queue (
    queue_id SERIAL PRIMARY KEY,
    memory_id VARCHAR(255) NOT NULL,
    operation VARCHAR(20) NOT NULL, -- 'create', 'update', 'delete'
    priority INTEGER DEFAULT 5,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_attempt TIMESTAMP WITH TIME ZONE,
    next_retry TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_memory_versions_last_modified ON memory_versions(last_modified);
CREATE INDEX IF NOT EXISTS idx_sync_transactions_status ON sync_transactions(status);
CREATE INDEX IF NOT EXISTS idx_sync_transactions_created ON sync_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_conflict_resolutions_memory ON conflict_resolutions(memory_id);
CREATE INDEX IF NOT EXISTS idx_sync_queue_scheduled ON sync_queue(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_sync_queue_memory ON sync_queue(memory_id);

-- Add version column to episodic_memory if it doesn't exist
ALTER TABLE episodic_memory ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
ALTER TABLE episodic_memory ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'synced';
ALTER TABLE episodic_memory ADD COLUMN IF NOT EXISTS last_sync TIMESTAMP WITH TIME ZONE;

-- Create trigger to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to memory_versions
DROP TRIGGER IF EXISTS update_memory_versions_updated_at ON memory_versions;
CREATE TRIGGER update_memory_versions_updated_at 
    BEFORE UPDATE ON memory_versions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to check memory consistency
CREATE OR REPLACE FUNCTION check_memory_consistency(p_memory_id VARCHAR)
RETURNS TABLE (
    is_consistent BOOLEAN,
    version_mismatch BOOLEAN,
    missing_stores TEXT[],
    version_details JSONB
) AS $$
DECLARE
    v_version_info RECORD;
    v_stores_present TEXT[] := '{}';
    v_expected_stores TEXT[] := ARRAY['redis', 'postgres', 'faiss'];
    v_missing TEXT[] := '{}';
BEGIN
    -- Get version info
    SELECT * INTO v_version_info 
    FROM memory_versions 
    WHERE memory_id = p_memory_id;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT 
            FALSE AS is_consistent,
            FALSE AS version_mismatch,
            v_expected_stores AS missing_stores,
            NULL::JSONB AS version_details;
        RETURN;
    END IF;
    
    -- Check which stores have this memory
    v_stores_present := ARRAY(SELECT jsonb_object_keys(v_version_info.store_versions));
    
    -- Find missing stores
    v_missing := ARRAY(
        SELECT unnest(v_expected_stores)
        EXCEPT
        SELECT unnest(v_stores_present)
    );
    
    -- Check version consistency
    RETURN QUERY SELECT
        CASE 
            WHEN array_length(v_missing, 1) > 0 THEN FALSE
            WHEN EXISTS (
                SELECT 1 
                FROM jsonb_each_text(v_version_info.store_versions) 
                WHERE value::INTEGER != v_version_info.version
            ) THEN FALSE
            ELSE TRUE
        END AS is_consistent,
        EXISTS (
            SELECT 1 
            FROM jsonb_each_text(v_version_info.store_versions) 
            WHERE value::INTEGER != v_version_info.version
        ) AS version_mismatch,
        v_missing AS missing_stores,
        jsonb_build_object(
            'current_version', v_version_info.version,
            'store_versions', v_version_info.store_versions,
            'last_modified', v_version_info.last_modified
        ) AS version_details;
END;
$$ LANGUAGE plpgsql;

-- Create function to get sync statistics
CREATE OR REPLACE FUNCTION get_sync_statistics(p_hours INTEGER DEFAULT 24)
RETURNS TABLE (
    total_syncs BIGINT,
    successful_syncs BIGINT,
    failed_syncs BIGINT,
    conflicts_resolved BIGINT,
    avg_sync_time_ms NUMERIC,
    memories_out_of_sync BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH sync_stats AS (
        SELECT 
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'completed') AS successful,
            COUNT(*) FILTER (WHERE status = 'failed') AS failed,
            AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) * 1000) 
                FILTER (WHERE status = 'completed') AS avg_time_ms
        FROM sync_transactions
        WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour' * p_hours
    ),
    conflict_stats AS (
        SELECT COUNT(*) AS conflicts
        FROM conflict_resolutions
        WHERE resolved_at > CURRENT_TIMESTAMP - INTERVAL '1 hour' * p_hours
    ),
    consistency_stats AS (
        SELECT COUNT(*) AS out_of_sync
        FROM memory_versions mv
        WHERE EXISTS (
            SELECT 1 
            FROM jsonb_each_text(mv.store_versions) 
            WHERE value::INTEGER != mv.version
        )
    )
    SELECT 
        sync_stats.total,
        sync_stats.successful,
        sync_stats.failed,
        conflict_stats.conflicts,
        ROUND(sync_stats.avg_time_ms, 2),
        consistency_stats.out_of_sync
    FROM sync_stats, conflict_stats, consistency_stats;
END;
$$ LANGUAGE plpgsql;

-- Create view for monitoring
CREATE OR REPLACE VIEW v_memory_sync_status AS
SELECT 
    mv.memory_id,
    mv.version,
    mv.last_modified,
    mv.store_versions,
    em.sync_status,
    em.last_sync,
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 
            FROM jsonb_each_text(mv.store_versions) 
            WHERE value::INTEGER != mv.version
        ) AND jsonb_object_keys(mv.store_versions) @> ARRAY['redis', 'postgres', 'faiss']
        THEN 'synced'
        WHEN EXISTS (
            SELECT 1 
            FROM jsonb_each_text(mv.store_versions) 
            WHERE value::INTEGER != mv.version
        ) THEN 'version_mismatch'
        ELSE 'missing_stores'
    END AS sync_health
FROM memory_versions mv
LEFT JOIN episodic_memory em ON mv.memory_id = em.memory_id;