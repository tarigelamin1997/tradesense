-- Create test user
INSERT INTO users (email, username, hashed_password, is_active, is_verified, created_at, updated_at)
VALUES (
    'test@example.com',
    'test',
    '$2b$12$qVqPbqW8LXYvErSvMPqxqOavq.1HqYGjP7hNEqYDHrMnacI4jG3K2', -- TestPass123\!
    true,
    true,
    NOW(),
    NOW()
) ON CONFLICT (email) DO NOTHING;
