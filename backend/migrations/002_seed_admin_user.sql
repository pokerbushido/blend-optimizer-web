-- Seed Admin User
-- Version: 1.0.0
-- Created: 2025-11-04

-- Insert default admin user
-- Password: changeme123 (hashed with bcrypt)
-- IMPORTANT: Change password after first login!

INSERT INTO users (
    username,
    email,
    hashed_password,
    full_name,
    role,
    is_active
) VALUES (
    'admin',
    'admin@company.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eDYKpXq5x5Oa', -- changeme123
    'Administrator',
    'admin',
    TRUE
) ON CONFLICT (username) DO NOTHING;

-- Insert demo users for testing (optional - comment out for production)
INSERT INTO users (
    username,
    email,
    hashed_password,
    full_name,
    role,
    is_active
) VALUES
    (
        'operatore1',
        'operatore1@company.local',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eDYKpXq5x5Oa', -- changeme123
        'Operatore Demo',
        'operatore',
        TRUE
    ),
    (
        'viewer1',
        'viewer1@company.local',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eDYKpXq5x5Oa', -- changeme123
        'Visualizzatore Demo',
        'visualizzatore',
        TRUE
    )
ON CONFLICT (username) DO NOTHING;

-- Log creation
DO $$
BEGIN
    RAISE NOTICE 'Admin user created successfully';
    RAISE NOTICE 'Username: admin';
    RAISE NOTICE 'Password: changeme123';
    RAISE NOTICE '⚠️  IMPORTANT: Change password after first login!';
END $$;
