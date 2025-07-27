-- TradeSense Database Optimization Script
-- Generated: 2025-01-12
-- Purpose: Add missing indexes for performance optimization

-- Trades table indexes
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_user_symbol ON trades(user_id, symbol);
CREATE INDEX IF NOT EXISTS idx_trades_user_date ON trades(user_id, entry_time);
CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at);

-- Portfolios table indexes
CREATE INDEX IF NOT EXISTS idx_portfolios_user_id ON portfolios(user_id);
CREATE INDEX IF NOT EXISTS idx_portfolios_created_at ON portfolios(created_at);

-- Trade notes indexes
CREATE INDEX IF NOT EXISTS idx_trade_notes_trade_id ON trade_notes(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_notes_user_id ON trade_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_trade_notes_created_at ON trade_notes(created_at);

-- Trade reviews indexes
CREATE INDEX IF NOT EXISTS idx_trade_reviews_trade_id ON trade_reviews(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_reviews_user_id ON trade_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_trade_reviews_created_at ON trade_reviews(created_at);

-- Trading accounts indexes
CREATE INDEX IF NOT EXISTS idx_trading_accounts_user_id ON trading_accounts(user_id);

-- Playbooks indexes
CREATE INDEX IF NOT EXISTS idx_playbooks_user_id ON playbooks(user_id);

-- Tags indexes
CREATE INDEX IF NOT EXISTS idx_tags_user_id ON tags(user_id);
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

-- Strategies indexes
CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON strategies(user_id);

-- Feature requests indexes
CREATE INDEX IF NOT EXISTS idx_feature_requests_user_id ON feature_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_feature_requests_status ON feature_requests(status);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_trades_user_pnl ON trades(user_id, pnl);
CREATE INDEX IF NOT EXISTS idx_trades_user_strategy ON trades(user_id, strategy_id);

-- End of optimization script