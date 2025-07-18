-- Performance optimization for TradeSense

-- Indexes for trades table
CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_user_symbol ON trades(user_id, symbol);
CREATE INDEX IF NOT EXISTS idx_trades_user_date ON trades(user_id, entry_time);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time);
CREATE INDEX IF NOT EXISTS idx_trades_exit_time ON trades(exit_time);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_pnl ON trades(pnl);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_trades_user_date_symbol ON trades(user_id, entry_time, symbol);

-- Indexes for other tables
CREATE INDEX IF NOT EXISTS idx_portfolio_user_date ON portfolios(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_trade_notes_trade_id ON trade_notes(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_tags_trade_id ON trade_tags(trade_id);
CREATE INDEX IF NOT EXISTS idx_journal_entries_user_id ON journal_entries(user_id);

-- Full text search index for journal entries
CREATE INDEX IF NOT EXISTS idx_journal_entries_content_gin 
ON journal_entries USING gin(to_tsvector('english', content));

-- Partial indexes for common filters
CREATE INDEX IF NOT EXISTS idx_trades_winning ON trades(user_id, pnl) WHERE pnl > 0;
CREATE INDEX IF NOT EXISTS idx_trades_losing ON trades(user_id, pnl) WHERE pnl < 0;

-- Update table statistics
ANALYZE;
