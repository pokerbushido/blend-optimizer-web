-- Blend Optimizer Database Schema
-- Version: 1.0.0
-- Created: 2025-11-04

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User Roles Enum
CREATE TYPE user_role AS ENUM ('admin', 'operatore', 'visualizzatore');

-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role user_role NOT NULL DEFAULT 'visualizzatore',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create index on username and email for faster lookups
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Inventory Uploads Table (tracking CSV uploads)
CREATE TABLE inventory_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_lots INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'completed',
    notes TEXT,
    CONSTRAINT fk_uploaded_by FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

CREATE INDEX idx_uploads_timestamp ON inventory_uploads(upload_timestamp DESC);
CREATE INDEX idx_uploads_user ON inventory_uploads(uploaded_by);

-- Inventory Lots Table
CREATE TABLE inventory_lots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id UUID REFERENCES inventory_uploads(id) ON DELETE CASCADE,

    -- Identificazione
    article_code VARCHAR(50) NOT NULL,
    lot_code VARCHAR(100) NOT NULL,
    description TEXT,

    -- Valori Reali (Real Values)
    dc_real NUMERIC(5,2),  -- Down Cluster %
    fp_real NUMERIC(6,1),  -- Fill Power cuin/oz
    duck_real NUMERIC(5,2),  -- Duck %
    oe_real NUMERIC(5,2),  -- OE (Other Elements) %
    feather_real NUMERIC(5,2),  -- Feather %
    oxygen_real NUMERIC(6,2),  -- Oxygen mg/100g
    turbidity_real NUMERIC(6,2),  -- Turbidity mm

    -- Valori Nominali (Target/Nominal Values)
    dc_nominal NUMERIC(5,2),
    fp_nominal NUMERIC(6,1),

    -- Qualità Aggiuntiva
    total_fibres NUMERIC(5,2),
    broken NUMERIC(5,2),
    landfowl NUMERIC(5,2),

    -- Business Data
    available_kg NUMERIC(10,2) NOT NULL,
    cost_per_kg NUMERIC(10,2),

    -- Metadata
    group_code VARCHAR(10),  -- '3', 'G', etc.
    species VARCHAR(10),  -- 'O', 'A', 'OA', 'C'
    color VARCHAR(10),  -- 'B', 'G', 'PW', 'NPW'
    state VARCHAR(10),  -- 'P', 'M', 'S', 'O'
    certification VARCHAR(20),  -- 'GWR', 'NWR', etc.
    quality_nominal TEXT,  -- Full quality description
    lab_notes TEXT,

    -- Flags
    is_estimated BOOLEAN DEFAULT FALSE,
    dc_was_imputed BOOLEAN DEFAULT FALSE,
    fp_was_imputed BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(article_code, lot_code),
    CHECK (available_kg >= 0),
    CHECK (dc_real >= 0 AND dc_real <= 100),
    CHECK (duck_real >= 0 AND duck_real <= 100)
);

-- Create indexes for common queries
CREATE INDEX idx_lots_article_code ON inventory_lots(article_code);
CREATE INDEX idx_lots_lot_code ON inventory_lots(lot_code);
CREATE INDEX idx_lots_species ON inventory_lots(species);
CREATE INDEX idx_lots_dc_real ON inventory_lots(dc_real);
CREATE INDEX idx_lots_fp_real ON inventory_lots(fp_real);
CREATE INDEX idx_lots_duck_real ON inventory_lots(duck_real);
CREATE INDEX idx_lots_available_kg ON inventory_lots(available_kg);
CREATE INDEX idx_lots_is_active ON inventory_lots(is_active);
CREATE INDEX idx_lots_upload_id ON inventory_lots(upload_id);

-- Full-text search index for description and notes
CREATE INDEX idx_lots_description_fts ON inventory_lots USING gin(to_tsvector('italian', description));
CREATE INDEX idx_lots_lab_notes_fts ON inventory_lots USING gin(to_tsvector('italian', COALESCE(lab_notes, '')));

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for inventory_lots table
CREATE TRIGGER update_inventory_lots_updated_at
    BEFORE UPDATE ON inventory_lots
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for active inventory with computed fields
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

-- Comments for documentation
COMMENT ON TABLE users IS 'Sistema utenti con ruoli (admin, operatore, visualizzatore)';
COMMENT ON TABLE inventory_uploads IS 'Tracking uploads CSV inventario';
COMMENT ON TABLE inventory_lots IS 'Lotti materiale piumino con parametri qualità e disponibilità';
COMMENT ON VIEW active_inventory IS 'Vista inventario attivo con campi calcolati';

COMMENT ON COLUMN inventory_lots.dc_real IS 'Down Cluster % - valore misurato reale';
COMMENT ON COLUMN inventory_lots.fp_real IS 'Fill Power cuin/oz - valore misurato reale';
COMMENT ON COLUMN inventory_lots.duck_real IS 'Duck % - percentuale anatra';
COMMENT ON COLUMN inventory_lots.oe_real IS 'Other Elements % - elementi estranei';
