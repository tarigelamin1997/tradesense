<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$lib/api/auth';
	import { tradeStore, type Trade } from '$lib/stores/trades';
	import { tradesApi } from '$lib/api/trades';
	import { get } from 'svelte/store';
	
	// Import chart components
	import CumulativePnLChart from '$lib/components/charts/CumulativePnLChart.svelte';
	import WinRateChart from '$lib/components/charts/WinRateChart.svelte';
	import ProfitDistributionChart from '$lib/components/charts/ProfitDistributionChart.svelte';
	import DailyPnLChart from '$lib/components/charts/DailyPnLChart.svelte';
	import StrategyPerformanceChart from '$lib/components/charts/StrategyPerformanceChart.svelte';
	import FeatureGate from '$lib/components/FeatureGate.svelte';
	import { billingApi } from '$lib/api/billing';
	
	let loading = true;
	let trades: Trade[] = [];
	let activeTab = 'overview';
	let userPlan: 'free' | 'pro' | 'enterprise' = 'free';
	
	// Statistics
	let stats = {
		totalTrades: 0,
		totalPnL: 0,
		winRate: 0,
		avgWin: 0,
		avgLoss: 0,
		profitFactor: 0,
		sharpeRatio: 0,
		maxDrawdown: 0,
		bestTrade: 0,
		worstTrade: 0,
		avgTradeDuration: '',
		consecutiveWins: 0,
		consecutiveLosses: 0
	};
	
	async function fetchTrades() {
		try {
			loading = true;
			
			// Check if authenticated
			if (!get(isAuthenticated)) {
				goto('/login');
				return;
			}
			
			// Fetch trades and subscription data
			const [apiTrades, subscription] = await Promise.all([
				tradesApi.getTrades(),
				billingApi.getSubscription()
			]);
			
			// Determine user plan
			if (subscription) {
				if (subscription.plan_id.includes('enterprise')) userPlan = 'enterprise';
				else if (subscription.plan_id.includes('pro')) userPlan = 'pro';
				else userPlan = 'free';
			}
			
			// Convert API trades to UI format
			trades = apiTrades.map(t => ({
				id: t.id,
				symbol: t.symbol,
				side: t.side,
				entryPrice: t.entry_price,
				exitPrice: t.exit_price,
				quantity: t.quantity,
				pnl: t.pnl || 0,
				entryDate: t.entry_date,
				exitDate: t.exit_date,
				strategy: t.strategy,
				notes: t.notes
			}));
			
			tradeStore.setTrades(trades);
			calculateStats();
			
		} catch (err: any) {
			console.error('Failed to fetch trades:', err);
			
			if (err.status === 401) {
				goto('/login');
			} else {
				// Use sample data as fallback
				useSampleData();
			}
		} finally {
			loading = false;
		}
	}
	
	function calculateStats() {
		if (trades.length === 0) {
			stats = {
				totalTrades: 0,
				totalPnL: 0,
				winRate: 0,
				avgWin: 0,
				avgLoss: 0,
				profitFactor: 0,
				sharpeRatio: 0,
				maxDrawdown: 0,
				bestTrade: 0,
				worstTrade: 0,
				avgTradeDuration: '0h 0m',
				consecutiveWins: 0,
				consecutiveLosses: 0
			};
			return;
		}
		
		const wins = trades.filter(t => t.pnl > 0);
		const losses = trades.filter(t => t.pnl < 0);
		
		// Basic stats
		stats.totalTrades = trades.length;
		stats.totalPnL = trades.reduce((sum, t) => sum + t.pnl, 0);
		stats.winRate = (wins.length / trades.length) * 100;
		stats.avgWin = wins.length > 0 ? wins.reduce((sum, t) => sum + t.pnl, 0) / wins.length : 0;
		stats.avgLoss = losses.length > 0 ? Math.abs(losses.reduce((sum, t) => sum + t.pnl, 0) / losses.length) : 0;
		stats.profitFactor = stats.avgLoss > 0 ? stats.avgWin / stats.avgLoss : 0;
		
		// Best and worst trades
		const pnlValues = trades.map(t => t.pnl);
		stats.bestTrade = Math.max(...pnlValues);
		stats.worstTrade = Math.min(...pnlValues);
		
		// Calculate average trade duration
		const durations = trades
			.filter(t => t.entryDate && t.exitDate)
			.map(t => new Date(t.exitDate).getTime() - new Date(t.entryDate).getTime());
		
		if (durations.length > 0) {
			const avgDuration = durations.reduce((sum, d) => sum + d, 0) / durations.length;
			const hours = Math.floor(avgDuration / (1000 * 60 * 60));
			const minutes = Math.floor((avgDuration % (1000 * 60 * 60)) / (1000 * 60));
			stats.avgTradeDuration = `${hours}h ${minutes}m`;
		}
		
		// Calculate consecutive wins/losses
		let currentWinStreak = 0;
		let currentLossStreak = 0;
		let maxWinStreak = 0;
		let maxLossStreak = 0;
		
		// Sort trades by exit date
		const sortedTrades = [...trades]
			.filter(t => t.exitDate)
			.sort((a, b) => new Date(a.exitDate).getTime() - new Date(b.exitDate).getTime());
		
		sortedTrades.forEach(trade => {
			if (trade.pnl > 0) {
				currentWinStreak++;
				currentLossStreak = 0;
				maxWinStreak = Math.max(maxWinStreak, currentWinStreak);
			} else if (trade.pnl < 0) {
				currentLossStreak++;
				currentWinStreak = 0;
				maxLossStreak = Math.max(maxLossStreak, currentLossStreak);
			}
		});
		
		stats.consecutiveWins = maxWinStreak;
		stats.consecutiveLosses = maxLossStreak;
		
		// Calculate max drawdown
		let peak = 0;
		let maxDrawdown = 0;
		let cumulative = 0;
		
		sortedTrades.forEach(trade => {
			cumulative += trade.pnl;
			if (cumulative > peak) {
				peak = cumulative;
			}
			const drawdown = peak - cumulative;
			if (drawdown > maxDrawdown) {
				maxDrawdown = drawdown;
			}
		});
		
		stats.maxDrawdown = maxDrawdown;
		
		// Calculate Sharpe Ratio (simplified)
		if (trades.length > 1) {
			const returns = trades.map(t => t.pnl);
			const avgReturn = stats.totalPnL / trades.length;
			const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / trades.length;
			const stdDev = Math.sqrt(variance);
			stats.sharpeRatio = stdDev > 0 ? (avgReturn / stdDev) * Math.sqrt(252) : 0; // Annualized
		}
	}
	
	function useSampleData() {
		const sampleTrades: Trade[] = [
			{
				id: 1,
				symbol: 'AAPL',
				side: 'long',
				entryPrice: 185.50,
				exitPrice: 187.25,
				quantity: 100,
				pnl: 175.00,
				entryDate: '2024-01-14 09:30',
				exitDate: '2024-01-14 14:45',
				strategy: 'Momentum',
				notes: 'Strong breakout pattern'
			},
			{
				id: 2,
				symbol: 'TSLA',
				side: 'short',
				entryPrice: 242.80,
				exitPrice: 244.50,
				quantity: 50,
				pnl: -85.00,
				entryDate: '2024-01-14 10:15',
				exitDate: '2024-01-14 15:30',
				strategy: 'Mean Reversion',
				notes: 'Stop loss hit'
			},
			{
				id: 3,
				symbol: 'NVDA',
				side: 'long',
				entryPrice: 495.00,
				exitPrice: 498.50,
				quantity: 50,
				pnl: 175.00,
				entryDate: '2024-01-13 11:00',
				exitDate: '2024-01-13 15:00',
				strategy: 'Breakout',
				notes: 'Earnings play'
			},
			{
				id: 4,
				symbol: 'SPY',
				side: 'long',
				entryPrice: 475.25,
				exitPrice: 476.80,
				quantity: 200,
				pnl: 310.00,
				entryDate: '2024-01-12 09:45',
				exitDate: '2024-01-12 14:30',
				strategy: 'Scalping',
				notes: 'Quick intraday trade'
			},
			{
				id: 5,
				symbol: 'META',
				side: 'short',
				entryPrice: 358.90,
				exitPrice: 357.20,
				quantity: 75,
				pnl: 127.50,
				entryDate: '2024-01-12 10:30',
				exitDate: '2024-01-12 13:15',
				strategy: 'News Trading',
				notes: 'Negative news reaction'
			}
		];
		
		trades = sampleTrades;
		tradeStore.setTrades(sampleTrades);
		calculateStats();
	}
	
	function formatCurrency(value: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD'
		}).format(value);
	}
	
	onMount(() => {
		fetchTrades();
	});
</script>

<svelte:head>
	<title>Analytics - TradeSense</title>
</svelte:head>

<div class="analytics-page">
	<header class="page-header">
		<h1>Trading Analytics</h1>
		<p>Comprehensive analysis of your trading performance</p>
	</header>
	
	{#if loading}
		<div class="loading">Loading analytics...</div>
	{:else}
		<!-- Stats Overview -->
		<div class="stats-grid">
			<div class="stat-card">
				<h3>Total P&L</h3>
				<p class="stat-value" class:positive={stats.totalPnL > 0} class:negative={stats.totalPnL < 0}>
					{formatCurrency(stats.totalPnL)}
				</p>
			</div>
			
			<div class="stat-card">
				<h3>Win Rate</h3>
				<p class="stat-value">{stats.winRate.toFixed(1)}%</p>
			</div>
			
			<div class="stat-card">
				<h3>Profit Factor</h3>
				<p class="stat-value">{stats.profitFactor.toFixed(2)}</p>
			</div>
			
			<div class="stat-card">
				<h3>Total Trades</h3>
				<p class="stat-value">{stats.totalTrades}</p>
			</div>
			
			<div class="stat-card">
				<h3>Average Win</h3>
				<p class="stat-value positive">{formatCurrency(stats.avgWin)}</p>
			</div>
			
			<div class="stat-card">
				<h3>Average Loss</h3>
				<p class="stat-value negative">{formatCurrency(-stats.avgLoss)}</p>
			</div>
			
			<div class="stat-card">
				<h3>Max Drawdown</h3>
				<p class="stat-value negative">{formatCurrency(-stats.maxDrawdown)}</p>
			</div>
			
			<div class="stat-card">
				<h3>Sharpe Ratio</h3>
				<p class="stat-value">{stats.sharpeRatio.toFixed(2)}</p>
			</div>
		</div>
		
		<!-- Tabs -->
		<div class="tabs">
			<button 
				class="tab" 
				class:active={activeTab === 'overview'}
				on:click={() => activeTab = 'overview'}
			>
				Overview
			</button>
			<FeatureGate feature="advanced-analytics" {userPlan} showLock={false}>
				<button 
					class="tab" 
					class:active={activeTab === 'performance'}
					on:click={() => activeTab = 'performance'}
				>
					Performance
				</button>
				<button 
					class="tab" 
					class:active={activeTab === 'distribution'}
					on:click={() => activeTab = 'distribution'}
				>
					Distribution
				</button>
				<button 
					class="tab" 
					class:active={activeTab === 'strategies'}
					on:click={() => activeTab = 'strategies'}
				>
					Strategies
				</button>
				<svelte:fragment slot="fallback">
					<button class="tab disabled" disabled>
						Performance 🔒
					</button>
					<button class="tab disabled" disabled>
						Distribution 🔒
					</button>
					<button class="tab disabled" disabled>
						Strategies 🔒
					</button>
				</svelte:fragment>
			</FeatureGate>
		</div>
		
		<!-- Tab Content -->
		<div class="tab-content">
			{#if activeTab === 'overview'}
				<div class="charts-grid">
					<div class="chart-container full-width">
						<CumulativePnLChart {trades} height={400} />
					</div>
					<div class="chart-container">
						<WinRateChart {trades} height={300} />
					</div>
					<div class="chart-container">
						<DailyPnLChart {trades} height={300} />
					</div>
				</div>
			{:else if activeTab === 'performance'}
				<div class="performance-metrics">
					<div class="metrics-grid">
						<div class="metric">
							<h4>Best Trade</h4>
							<p class="positive">{formatCurrency(stats.bestTrade)}</p>
						</div>
						<div class="metric">
							<h4>Worst Trade</h4>
							<p class="negative">{formatCurrency(stats.worstTrade)}</p>
						</div>
						<div class="metric">
							<h4>Avg Trade Duration</h4>
							<p>{stats.avgTradeDuration}</p>
						</div>
						<div class="metric">
							<h4>Consecutive Wins</h4>
							<p>{stats.consecutiveWins}</p>
						</div>
						<div class="metric">
							<h4>Consecutive Losses</h4>
							<p>{stats.consecutiveLosses}</p>
						</div>
					</div>
					<div class="chart-container full-width">
						<CumulativePnLChart {trades} height={400} />
					</div>
				</div>
			{:else if activeTab === 'distribution'}
				<div class="charts-grid">
					<div class="chart-container full-width">
						<ProfitDistributionChart {trades} height={400} />
					</div>
					<div class="chart-container full-width">
						<DailyPnLChart {trades} height={400} />
					</div>
				</div>
			{:else if activeTab === 'strategies'}
				<div class="chart-container full-width">
					<StrategyPerformanceChart {trades} height={500} />
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.analytics-page {
		max-width: 1400px;
		margin: 0 auto;
		padding-bottom: 4rem;
	}
	
	.page-header {
		margin-bottom: 2rem;
	}
	
	.page-header h1 {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}
	
	.page-header p {
		color: #666;
	}
	
	.loading {
		text-align: center;
		padding: 4rem;
		color: #666;
	}
	
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}
	
	.stat-card {
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		padding: 1.5rem;
	}
	
	.stat-card h3 {
		font-size: 0.875rem;
		color: #666;
		margin-bottom: 0.5rem;
		font-weight: 500;
	}
	
	.stat-value {
		font-size: 1.5rem;
		font-weight: 600;
		color: #333;
	}
	
	.stat-value.positive {
		color: #10b981;
	}
	
	.stat-value.negative {
		color: #ef4444;
	}
	
	.tabs {
		display: flex;
		gap: 1rem;
		margin-bottom: 2rem;
		border-bottom: 1px solid #e0e0e0;
		overflow-x: auto;
	}
	
	.tab {
		padding: 0.75rem 1.5rem;
		background: none;
		border: none;
		color: #666;
		font-weight: 500;
		cursor: pointer;
		position: relative;
		white-space: nowrap;
		transition: color 0.2s;
	}
	
	.tab:hover {
		color: #333;
	}
	
	.tab.active {
		color: #10b981;
	}
	
	.tab.active::after {
		content: '';
		position: absolute;
		bottom: -1px;
		left: 0;
		right: 0;
		height: 2px;
		background: #10b981;
	}
	
	.charts-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
		gap: 1.5rem;
	}
	
	.chart-container {
		background: white;
		border-radius: 8px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
	
	.chart-container.full-width {
		grid-column: 1 / -1;
	}
	
	.performance-metrics {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}
	
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin-bottom: 1rem;
	}
	
	.metric {
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		padding: 1.5rem;
		text-align: center;
	}
	
	.metric h4 {
		font-size: 0.875rem;
		color: #666;
		margin-bottom: 0.5rem;
		font-weight: 500;
	}
	
	.metric p {
		font-size: 1.25rem;
		font-weight: 600;
		color: #333;
	}
	
	.metric p.positive {
		color: #10b981;
	}
	
	.metric p.negative {
		color: #ef4444;
	}
	
	.tab.disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.tab.disabled:hover {
		color: #666;
	}
	
	@media (max-width: 768px) {
		.analytics-page {
			padding: 0 1rem 4rem;
		}
		
		.stats-grid {
			grid-template-columns: 1fr 1fr;
		}
		
		.charts-grid {
			grid-template-columns: 1fr;
		}
		
		.tabs {
			-webkit-overflow-scrolling: touch;
			padding-bottom: 0.5rem;
		}
		
		.tab {
			padding: 0.5rem 1rem;
			font-size: 0.875rem;
		}
		
		.metrics-grid {
			grid-template-columns: 1fr 1fr;
		}
	}
	
	@media (max-width: 640px) {
		.page-header h1 {
			font-size: 1.5rem;
		}
		
		.stats-grid {
			grid-template-columns: 1fr;
			gap: 0.75rem;
		}
		
		.stat-card {
			padding: 1rem;
		}
		
		.stat-value {
			font-size: 1.25rem;
		}
		
		.tabs {
			gap: 0.5rem;
		}
		
		.tab {
			padding: 0.5rem 0.75rem;
			font-size: 0.75rem;
		}
		
		.metrics-grid {
			grid-template-columns: 1fr;
		}
		
		.metric {
			padding: 1rem;
		}
		
		.metric p {
			font-size: 1rem;
		}
	}
</style>