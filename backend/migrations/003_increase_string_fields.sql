-- Increase string field lengths in inventory_lots table
-- Version: 1.0.1
-- Created: 2025-11-05
-- Reason: Fix CSV import errors due to values exceeding VARCHAR(10) limit

-- Step 1: Drop the dependent view
DROP VIEW IF EXISTS active_inventory;

-- Step 2: Increase metadata string field lengths from VARCHAR(10) to VARCHAR(50)
ALTER TABLE inventory_lots
    ALTER COLUMN group_code TYPE VARCHAR(50),
    ALTER COLUMN species TYPE VARCHAR(50),
    ALTER COLUMN color TYPE VARCHAR(50),
    ALTER COLUMN state TYPE VARCHAR(50);

-- Step 3: Recreate the view with the same definition
CREATE VIEW active_inventory AS
SELECT
    l.*,
    u.username as uploaded_by_username,
    u.full_name as uploaded_by_name,
    iu.upload_timestamp,
    iu.filename as source_filename,
    -- Computed fields
    CASE
        WHEN l.dc_real IS NOT NULL THEN l.dc_real
        ELSE l.dc_nominal
    END as dc_effective,
    CASE
        WHEN l.fp_real IS NOT NULL THEN l.fp_real
        ELSE l.fp_nominal
    END as fp_effective,
    -- Quality score (simple metric for sorting)
    (COALESCE(l.dc_real, l.dc_nominal, 0) * 0.4 +
     COALESCE(l.fp_real, l.fp_nominal, 0) * 0.1 +
     (100 - COALESCE(l.oe_real, 0)) * 0.3 +
     (100 - COALESCE(l.feather_real, 0)) * 0.2) as quality_score
FROM
    inventory_lots l
    LEFT JOIN inventory_uploads iu ON l.upload_id = iu.id
    LEFT JOIN users u ON iu.uploaded_by = u.id
WHERE
    l.is_active = TRUE
    AND l.available_kg > 0;

-- Add comment for documentation
COMMENT ON TABLE inventory_lots IS 'Lotti materiale piumino con parametri qualità e disponibilità - Updated 2025-11-05: Increased metadata field lengths';
COMMENT ON VIEW active_inventory IS 'Vista inventario attivo con campi calcolati';
