interface ExportData {
  stats: {
    totalPnl: number;
    winRate: number;
    totalTrades: number;
    avgHoldTime: string;
  };
  strategyPerformance?: Array<{
    name: string;
    trades: number;
    pnl: number;
    winRate?: number;
  }>;
  monthlyData?: Array<{
    month: string;
    pnl: number;
    trades: number;
  }>;
  dateRange: {
    start: Date;
    end: Date;
  };
}

export const exportToCSV = (data: ExportData, filename?: string) => {
  const { stats, strategyPerformance = [], monthlyData = [], dateRange } = data;
  
  // Create CSV content
  let csvContent = 'TradeSense Analytics Export\n';
  csvContent += `Date Range: ${dateRange.start.toLocaleDateString()} - ${dateRange.end.toLocaleDateString()}\n`;
  csvContent += `Generated: ${new Date().toLocaleString()}\n\n`;
  
  // Summary Stats
  csvContent += 'SUMMARY STATISTICS\n';
  csvContent += 'Metric,Value\n';
  csvContent += `Total P&L,$${stats.totalPnl.toFixed(2)}\n`;
  csvContent += `Win Rate,${stats.winRate.toFixed(1)}%\n`;
  csvContent += `Total Trades,${stats.totalTrades}\n`;
  csvContent += `Avg Hold Time,${stats.avgHoldTime}\n\n`;
  
  // Strategy Performance
  if (strategyPerformance.length > 0) {
    csvContent += 'STRATEGY PERFORMANCE\n';
    csvContent += 'Strategy,Trades,P&L,Win Rate\n';
    strategyPerformance.forEach(strategy => {
      csvContent += `${strategy.name},${strategy.trades},$${strategy.pnl.toFixed(2)},${strategy.winRate ? strategy.winRate.toFixed(1) + '%' : 'N/A'}\n`;
    });
    csvContent += '\n';
  }
  
  // Monthly Performance
  if (monthlyData.length > 0) {
    csvContent += 'MONTHLY PERFORMANCE\n';
    csvContent += 'Month,P&L,Trades\n';
    monthlyData.forEach(month => {
      csvContent += `${month.month},$${month.pnl.toFixed(2)},${month.trades}\n`;
    });
  }
  
  // Create blob and download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  const defaultFilename = `tradesense_analytics_${dateRange.start.toISOString().split('T')[0]}_to_${dateRange.end.toISOString().split('T')[0]}.csv`;
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename || defaultFilename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

export const formatDataForExport = (
  stats: any,
  chartData: any,
  dateRange: number
): ExportData => {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - dateRange);
  
  return {
    stats,
    strategyPerformance: chartData.strategyBreakdown?.map((s: any) => ({
      name: s.name,
      trades: s.value,
      pnl: s.pnl
    })),
    monthlyData: chartData.monthlyPnl,
    dateRange: {
      start: startDate,
      end: endDate
    }
  };
};