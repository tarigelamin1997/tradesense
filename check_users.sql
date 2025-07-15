-- Check existing users in the database
-- Run with: psql -U postgres -d tradesense -f check_users.sql

\echo '📊 Existing Users in Database:'
\echo '================================'

SELECT 
    email,
    username,
    SUBSTRING(id::text, 1, 8) || '...' as user_id,
    is_active,
    created_at::date as registered_on
FROM users
ORDER BY created_at DESC;

\echo ''
\echo '📈 User Trade Counts:'
\echo '================================'

SELECT 
    u.email,
    COUNT(t.id) as trade_count,
    COALESCE(SUM(t.pnl), 0)::numeric(10,2) as total_pnl
FROM users u
LEFT JOIN trades t ON u.id = t.user_id
GROUP BY u.id, u.email
ORDER BY trade_count DESC;