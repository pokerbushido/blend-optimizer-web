-- Migration: Add standard_nominal field to inventory_lots table
-- Date: 2025-11-09
-- Description: Adds the missing standard_nominal field which was referenced in code
--              but not present in the database schema

-- Add standard_nominal column
ALTER TABLE inventory_lots
ADD COLUMN IF NOT EXISTS standard_nominal TEXT;

-- Add comment for documentation
COMMENT ON COLUMN inventory_lots.standard_nominal IS 'Nominal standard specification (e.g., EN, USA, JIS)';
