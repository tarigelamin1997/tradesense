import type { ComponentType } from 'svelte';

// Import existing components
import MetricCard from '$lib/components/MetricCard.svelte';
import EquityChart from '$lib/components/EquityChart.svelte';
import PnLChart from '$lib/components/PnLChart.svelte';
import TradeList from '$lib/components/TradeList.svelte';

// Import new dashboard widgets
import PieChartWidget from './charts/PieChartWidget.svelte';
import GaugeWidget from './metrics/GaugeWidget.svelte';
import HeatmapWidget from './charts/HeatmapWidget.svelte';
import CandlestickWidget from './charts/CandlestickWidget.svelte';
import DrawdownChart from './charts/DrawdownChart.svelte';
import LiveMarketWidget from './special/LiveMarketWidget.svelte';
import PnLCalendarWidget from './special/PnLCalendarWidget.svelte';
import TextMarkdownWidget from './text/TextMarkdownWidget.svelte';

// Widget type to component mapping
export const widgetComponents: Record<string, ComponentType> = {
  // Metrics
  metric_card: MetricCard,
  gauge: GaugeWidget,
  
  // Charts
  line_chart: EquityChart,
  bar_chart: PnLChart,
  pie_chart: PieChartWidget,
  candlestick: CandlestickWidget,
  heatmap: HeatmapWidget,
  drawdown_chart: DrawdownChart,
  
  // Tables
  table: TradeList,
  
  // Special widgets
  live_market: LiveMarketWidget,
  pnl_calendar: PnLCalendarWidget,
  text_markdown: TextMarkdownWidget,
  
  // TODO: Add these widgets
  // win_rate_gauge: WinRateGaugeWidget,
  // trade_distribution_map: TradeDistributionMapWidget,
};

// Widget categories for organization
export const widgetCategories = {
  metrics: {
    name: 'Metrics',
    widgets: ['metric_card', 'gauge']
  },
  charts: {
    name: 'Charts',
    widgets: ['line_chart', 'bar_chart', 'pie_chart', 'candlestick', 'heatmap', 'drawdown_chart']
  },
  tables: {
    name: 'Tables',
    widgets: ['table']
  },
  special: {
    name: 'Special',
    widgets: ['live_market', 'pnl_calendar', 'text_markdown', 'win_rate_gauge', 'trade_distribution_map']
  }
};

// Default widget sizes
export const defaultWidgetSizes: Record<string, { width: number; height: number }> = {
  metric_card: { width: 3, height: 2 },
  gauge: { width: 3, height: 3 },
  line_chart: { width: 6, height: 4 },
  bar_chart: { width: 6, height: 4 },
  pie_chart: { width: 4, height: 4 },
  candlestick: { width: 8, height: 5 },
  heatmap: { width: 6, height: 4 },
  drawdown_chart: { width: 6, height: 4 },
  table: { width: 12, height: 6 },
  live_market: { width: 8, height: 3 },
  pnl_calendar: { width: 6, height: 5 },
  text_markdown: { width: 4, height: 3 },
  win_rate_gauge: { width: 3, height: 3 },
  trade_distribution_map: { width: 6, height: 4 },
};

// Sample data generators for widgets
export const sampleDataGenerators: Record<string, () => any> = {
  metric_card: () => ({
    title: 'Total P&L',
    value: 15234.56,
    format: 'currency',
    trend: 12.5
  }),
  
  gauge: () => ({
    value: 68.5,
    min: 0,
    max: 100,
    unit: '%',
    title: 'Win Rate'
  }),
  
  line_chart: () => ({
    data: Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      value: 10000 + Math.random() * 5000 + i * 100
    }))
  }),
  
  bar_chart: () => ({
    data: Array.from({ length: 14 }, (_, i) => ({
      date: new Date(Date.now() - (13 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      pnl: (Math.random() - 0.45) * 500
    }))
  }),
  
  pie_chart: () => ({
    data: {
      labels: ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'],
      datasets: [{
        data: [25, 20, 18, 15, 22],
        backgroundColor: ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6']
      }]
    }
  }),
  
  candlestick: () => ({
    data: Array.from({ length: 20 }, (_, i) => {
      const base = 100 + Math.random() * 50;
      const change = (Math.random() - 0.5) * 5;
      return {
        x: new Date(Date.now() - (19 - i) * 24 * 60 * 60 * 1000),
        o: base,
        h: base + Math.random() * 3,
        l: base - Math.random() * 3,
        c: base + change,
        v: Math.floor(Math.random() * 1000000)
      };
    })
  }),
  
  heatmap: () => ({
    xLabels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
    yLabels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    data: Array.from({ length: 20 }, (_, i) => ({
      x: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'][i % 5],
      y: ['Week 1', 'Week 2', 'Week 3', 'Week 4'][Math.floor(i / 5)],
      value: (Math.random() - 0.5) * 1000
    })),
    colorScale: 'diverging'
  }),
  
  drawdown_chart: () => ({
    data: Array.from({ length: 60 }, (_, i) => {
      const drawdown = -Math.random() * 15;
      return {
        date: new Date(Date.now() - (59 - i) * 24 * 60 * 60 * 1000),
        drawdown: drawdown,
        equity: 100000 * (1 + drawdown / 100)
      };
    })
  }),
  
  table: () => ({
    trades: [
      {
        id: 1,
        symbol: 'AAPL',
        side: 'long',
        entryPrice: 185.50,
        exitPrice: 187.25,
        quantity: 100,
        pnl: 175.00,
        entryDate: '2024-01-14 09:30',
        exitDate: '2024-01-14 14:45'
      }
    ]
  }),
  
  live_market: () => ({
    symbols: ['SPY', 'QQQ', 'IWM', 'DIA']
  }),
  
  pnl_calendar: () => ({
    data: Array.from({ length: 20 }, (_, i) => ({
      date: new Date(Date.now() - Math.floor(Math.random() * 30) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      value: (Math.random() - 0.45) * 500,
      trades: Math.floor(Math.random() * 5) + 1
    }))
  }),
  
  text_markdown: () => ({
    content: `# Trading Notes

## Today's Strategy
- Focus on **momentum plays** in tech sector
- Watch for breakouts above VWAP
- Set stop losses at -2%

## Key Levels
| Symbol | Support | Resistance |
|--------|---------|------------|
| SPY    | 485.50  | 492.00     |
| QQQ    | 420.00  | 428.50     |

> "The trend is your friend until the end." - Trading wisdom

### Remember:
1. Stick to the plan
2. Manage risk first
3. Let winners run`
  })
};