-- Migration script to add batch_id to all relevant tables
-- and ensure we're using a single schema approach rather than tenant schemas

-- 1. Ensure we're in public schema
SET search_path TO public;

-- 2. Add batch_id to contexts table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'contexts' AND column_name = 'batch_id'
    ) THEN
        ALTER TABLE contexts ADD COLUMN batch_id VARCHAR(100);
        CREATE INDEX idx_contexts_batch_id ON contexts(batch_id);
        RAISE NOTICE 'Added batch_id column to contexts table';
    ELSE
        RAISE NOTICE 'batch_id column already exists in contexts table';
    END IF;
END $$;

-- 3. Add batch_id to templates table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'templates' AND column_name = 'batch_id'
    ) THEN
        ALTER TABLE templates ADD COLUMN batch_id VARCHAR(100);
        RAISE NOTICE 'Added batch_id column to templates table';
    ELSE
        RAISE NOTICE 'batch_id column already exists in templates table';
    END IF;
END $$;

-- 4. Add batch_id to results table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'generation_results' AND column_name = 'batch_id'
    ) THEN
        ALTER TABLE generation_results ADD COLUMN batch_id VARCHAR(100);
        CREATE INDEX idx_generation_results_batch_id ON generation_results(batch_id);
        RAISE NOTICE 'Added batch_id column to generation_results table';
    ELSE
        RAISE NOTICE 'batch_id column already exists in generation_results table';
    END IF;
END $$;

-- 5. Preserve tenant_id as a reference field (but don't use it for schema switching)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'contexts' AND column_name = 'tenant_id'
    ) THEN
        ALTER TABLE contexts ADD COLUMN tenant_id VARCHAR(100);
        RAISE NOTICE 'Added tenant_id reference column to contexts table';
    ELSE
        RAISE NOTICE 'tenant_id column already exists in contexts table';
    END IF;
END $$; 