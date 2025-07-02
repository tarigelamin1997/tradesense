
export const SUPPORTED_FILE_TYPES = ['.csv', '.xlsx', '.xls'] as const;

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const REQUIRED_COLUMNS = [
  'symbol',
  'entry_time',
  'exit_time',
  'direction',
  'quantity',
  'entry_price',
  'exit_price',
  'pnl',
] as const;

export const TRADE_DIRECTIONS = ['long', 'short'] as const;

export const CHART_COLORS = {
  primary: '#3B82F6',
  success: '#10B981',
  danger: '#EF4444',
  warning: '#F59E0B',
  gray: '#6B7280',
} as const;
