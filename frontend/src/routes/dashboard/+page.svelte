<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import MetricCard from '$lib/components/MetricCard.svelte';
	import EquityChart from '$lib/components/EquityChart.svelte';
	import PnLChart from '$lib/components/PnLChart.svelte';
	import TradeList from '$lib/components/TradeList.svelte';
	import PriceTicker from '$lib/components/PriceTicker.svelte';
	import TradeInsights from '$lib/components/TradeInsights.svelte';
	import { tradeStore } from '$lib/stores/trades';
	import { analyticsApi } from '$lib/api/analytics';
	import { tradesApi } from '$lib/api/trades';
	import { billingApi } from '$lib/api/billing';
	import { isAuthenticated } from '$lib/api/auth';
	import { get } from 'svelte/store';
	import { logger } from '$lib/utils/logger';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import { _ } from 'svelte-i18n';
	
	let loading = true;
	let error = '';
	let usingSampleData = false;
	let dateRange = '30d';
	let userPlan: 'free' | 'pro' | 'enterprise' = 'free';
	let isNewUser = false;
	
	// Data from API
	let stats = {
		totalPnl: 0,
		totalPnlPercent: 0,
		winRate: 0,
		winRateChange: 0,
		totalTrades: 0,
		currentStreak: { type: 'win' as const, count: 0 }
	};
	
	let equityData: Array<{ date: string; value: number }> = [];
	let pnlData: Array<{ date: string; pnl: number }> = [];
	let recentTrades: any[] = [];
	
	// Generate sample data as fallback
	function generateSampleData() {
		const sampleStats = {
			totalPnl: 15176.89,
			totalPnlPercent: 51.8,
			winRate: 64.8,
			winRateChange: 0.2,
			totalTrades: 245,
			currentStreak: { type: 'win' as const, count: 5 }
		};
		
		const sampleEquityData = Array.from({ length: 30 }, (_, i) => {
			const date = new Date();
			date.setDate(date.getDate() - 30 + i);
			return {
				date: date.toISOString().split('T')[0],
				value: 10000 + Math.random() * 5000 + i * 100
			};
		});
		
		const samplePnlData = Array.from({ length: 14 }, (_, i) => {
			const date = new Date();
			date.setDate(date.getDate() - 14 + i);
			return {
				date: date.toISOString().split('T')[0],
				pnl: (Math.random() - 0.45) * 500
			};
		});
		
		const sampleTrades = [
			{
				id: 1,
				symbol: 'AAPL',
				side: 'long' as const,
				entryPrice: 185.50,
				exitPrice: 187.25,
				quantity: 100,
				pnl: 175.00,
				entryDate: '2024-01-14 09:30',
				exitDate: '2024-01-14 14:45'
			},
			{
				id: 2,
				symbol: 'TSLA',
				side: 'short' as const,
				entryPrice: 242.80,
				exitPrice: 244.50,
				quantity: 50,
				pnl: -85.00,
				entryDate: '2024-01-14 10:15',
				exitDate: '2024-01-14 15:30'
			}
		];
		
		return { sampleStats, sampleEquityData, samplePnlData, sampleTrades };
	}
	
	async function fetchData() {
		try {
			loading = true;
			error = '';
			
			// Check if authenticated - only redirect on client side
			if (!get(isAuthenticated)) {
				logger.log('Not authenticated, redirecting to login');
				if (browser) {
					goto('/login');
				}
				return;
			}
			
			logger.log('Fetching analytics data...');
			
			// Try to get summary and subscription data
			try {
				const [summaryData, subscription] = await Promise.all([
					analyticsApi.getSummary({ period: dateRange as any }),
					billingApi.getSubscription()
				]);
				logger.log('Summary data:', summaryData);
				
				// Determine user plan
				if (subscription) {
					if (subscription.plan_id.includes('enterprise')) userPlan = 'enterprise';
					else if (subscription.plan_id.includes('pro')) userPlan = 'pro';
					else userPlan = 'free';
				}
				
				// Update stats with available data
				stats = {
					totalPnl: summaryData.total_pnl || 0,
					totalPnlPercent: 0, // Calculate if needed
					winRate: summaryData.overall_win_rate || 0,
					winRateChange: 0,
					totalTrades: summaryData.total_trades || 0,
					currentStreak: { type: 'win' as const, count: 0 }
				};
				
				// For now, use empty arrays for charts
				equityData = [];
				pnlData = [];
			} catch (summaryError) {
				logger.error('Failed to fetch summary:', summaryError);
				throw summaryError;
			}
			
			// Fetch recent trades
			try {
				const trades = await tradesApi.getTrades({ limit: 10 });
				recentTrades = trades.map(trade => ({
					id: trade.id,
					symbol: trade.symbol,
					side: trade.side,
					entryPrice: trade.entry_price,
					exitPrice: trade.exit_price,
					quantity: trade.quantity,
					pnl: trade.pnl || 0,
					entryDate: trade.entry_date,
					exitDate: trade.exit_date
				}));
				
				tradeStore.setTrades(recentTrades);
				usingSampleData = false;
			} catch (tradesError) {
				logger.error('Failed to fetch trades:', tradesError);
				// Continue with empty trades if this fails
				recentTrades = [];
			}
			
		} catch (err: any) {
			logger.error('Failed to fetch data:', err);
			
			if (err.status === 401 && browser) {
				goto('/login');
			} else {
				// Only use sample data if user explicitly requests it
				error = 'Failed to load data. Please try again or check your connection.';
			}
		} finally {
			loading = false;
		}
	}
	
	onMount(() => {
		fetchData();
	});
	
	// Handle date range change - only on client side
	$: if (dateRange && browser) {
		fetchData();
	}
</script>

<svelte:head>
	<title>Dashboard - TradeSense</title>
</svelte:head>

{#if loading}
	<div class="dashboard-skeleton">
		<div class="page-header">
			<LoadingSkeleton type="text" lines={2} width="200px" />
		</div>
		
		<!-- Metrics Skeleton -->
		<div class="metrics-grid">
			{#each Array(4) as _}
				<LoadingSkeleton type="stat" />
			{/each}
		</div>
		
		<!-- Charts Skeleton -->
		<div class="charts-grid">
			<div class="chart-wrapper">
				<LoadingSkeleton type="chart" height="300px" />
			</div>
			<div class="chart-wrapper">
				<LoadingSkeleton type="chart" height="300px" />
			</div>
		</div>
		
		<!-- Recent Trades Skeleton -->
		<div class="recent-trades-skeleton">
			<LoadingSkeleton type="text" lines={1} width="150px" />
			<div style="margin-top: 1rem">
				<LoadingSkeleton type="card" height="80px" />
				<LoadingSkeleton type="card" height="80px" />
				<LoadingSkeleton type="card" height="80px" />
			</div>
		</div>
	</div>
{:else if error}
	<div class="error">{error}</div>
{:else if stats.totalTrades === 0 && !usingSampleData}
	<!-- Welcome message for new users -->
	<div class="dashboard">
		<div class="welcome-container">
			<h1>{$_('dashboard.welcome', { values: { name: 'TradeSense' } })} 🎉</h1>
			<p>Start tracking your trades to see analytics and insights.</p>
			<div class="welcome-actions">
				<a href="/tradelog" class="primary-button">{$_('trades.newTrade')}</a>
				<button on:click={() => {
					const { sampleStats, sampleEquityData, samplePnlData, sampleTrades } = generateSampleData();
					stats = sampleStats;
					equityData = sampleEquityData;
					pnlData = samplePnlData;
					recentTrades = sampleTrades;
					tradeStore.setTrades(sampleTrades);
					isNewUser = true;
					usingSampleData = true;
				}} class="secondary-button">{$_('dashboard.viewDemo', { default: 'View Demo Dashboard' })}</button>
			</div>
		</div>
	</div>
{:else}
	<div class="dashboard">
		<!-- Price Ticker -->
		<div class="ticker-section">
			<PriceTicker />
		</div>
		
		<header class="dashboard-header">
			<h1>{$_('dashboard.title')}</h1>
			<p>{usingSampleData ? '🎭 Demo Data' : `Last ${dateRange}`}</p>
		</header>
		
		{#if usingSampleData}
			<div class="demo-banner">
				<strong>⚠️ Demo Mode:</strong> You're viewing sample data. 
				<a href="/tradelog">Add real trades</a> or <a href="/upload">import from CSV</a> to see your actual performance.
			</div>
		{/if}
		
		<!-- Date Range Selector -->
		<div class="controls">
			<select bind:value={dateRange} class="date-range-select">
				<option value="7d">{$_('dashboard.timeframes.1w')}</option>
				<option value="30d">{$_('dashboard.timeframes.1m')}</option>
				<option value="90d">{$_('dashboard.timeframes.3m')}</option>
				<option value="1y">{$_('dashboard.timeframes.1y')}</option>
			</select>
			<button on:click={fetchData} class="refresh-button" disabled={loading}>
				{loading ? $_('common.actions.loading') : $_('common.actions.refresh')}
			</button>
		</div>
		
		<!-- Metrics Grid -->
		<div class="grid grid-cols-4">
			<MetricCard 
				title={$_('dashboard.metrics.profitLoss')} 
				value={stats.totalPnl} 
				format="currency"
				trend={stats.totalPnlPercent}
			/>
			<MetricCard 
				title={$_('dashboard.metrics.winRate')} 
				value={stats.winRate} 
				format="percent"
				trend={stats.winRateChange}
			/>
			<MetricCard 
				title={$_('dashboard.metrics.totalTrades')} 
				value={stats.totalTrades} 
				format="number"
			/>
			<MetricCard 
				title={$_('dashboard.currentStreak', { default: 'Current Streak' })} 
				value={stats.currentStreak.count} 
				format="streak"
				streakType={stats.currentStreak.type}
			/>
		</div>
		
		<!-- Charts Grid -->
		<div class="grid grid-cols-2">
			<div class="card">
				<h2>{$_('dashboard.charts.equityCurve', { default: 'Equity Curve' })}</h2>
				<EquityChart data={equityData} />
			</div>
			<div class="card">
				<h2>{$_('dashboard.charts.dailyPL', { default: 'Daily P&L' })}</h2>
				<PnLChart data={pnlData} />
			</div>
		</div>
		
		<!-- AI Insights -->
		<TradeInsights trades={recentTrades} {userPlan} />
		
		<!-- Recent Trades -->
		<div class="card">
			<h2>{$_('dashboard.widgets.recentTrades')}</h2>
			<TradeList trades={recentTrades} />
		</div>
	</div>
{/if}

<style>
	.dashboard {
		max-width: 1200px;
		margin: 0 auto;
	}
	
	.dashboard-skeleton {
		max-width: 1200px;
		margin: 0 auto;
	}
	
	.dashboard-skeleton .page-header {
		margin-bottom: 2rem;
	}
	
	.dashboard-skeleton .metrics-grid,
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.dashboard-skeleton .charts-grid,
	.charts-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.chart-wrapper {
		background: white;
		border-radius: 8px;
		overflow: hidden;
	}
	
	.recent-trades-skeleton {
		margin-top: 2rem;
	}
	
	.dashboard-header {
		margin-bottom: 2rem;
	}
	
	.dashboard-header h1 {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}
	
	.dashboard-header p {
		color: #666;
	}
	
	.demo-banner {
		background: #fef3c7;
		border: 1px solid #f59e0b;
		color: #92400e;
		padding: 1rem;
		border-radius: 8px;
		margin-bottom: 2rem;
		text-align: center;
		font-size: 0.875rem;
	}
	
	.demo-banner a {
		color: #dc2626;
		text-decoration: underline;
		margin: 0 0.25rem;
	}
	
	h2 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
		color: #333;
	}
	
	.controls {
		display: flex;
		gap: 1rem;
		margin-bottom: 2rem;
	}
	
	.date-range-select {
		padding: 0.5rem 1rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		background: white;
		font-size: 0.875rem;
	}
	
	.refresh-button {
		padding: 0.5rem 1rem;
		background: #10b981;
		color: white;
		border: none;
		border-radius: 6px;
		font-size: 0.875rem;
		cursor: pointer;
		transition: background 0.2s;
	}
	
	.refresh-button:hover:not(:disabled) {
		background: #059669;
	}
	
	.refresh-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	.welcome-container {
		text-align: center;
		padding: 4rem 2rem;
		max-width: 600px;
		margin: 0 auto;
	}
	
	.welcome-container h1 {
		font-size: 2.5rem;
		margin-bottom: 1rem;
		color: #1a1a1a;
	}
	
	.welcome-container p {
		font-size: 1.25rem;
		color: #666;
		margin-bottom: 2rem;
	}
	
	.welcome-actions {
		display: flex;
		gap: 1rem;
		justify-content: center;
		flex-wrap: wrap;
	}
	
	.primary-button, .secondary-button {
		padding: 1rem 2rem;
		border-radius: 8px;
		font-size: 1.125rem;
		text-decoration: none;
		display: inline-block;
		transition: all 0.2s;
		cursor: pointer;
		border: none;
	}
	
	.primary-button {
		background: #10b981;
		color: white;
	}
	
	.primary-button:hover {
		background: #059669;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
	}
	
	.secondary-button {
		background: #f3f4f6;
		color: #1a1a1a;
		border: 2px solid #e5e7eb;
	}
	
	.secondary-button:hover {
		background: #e5e7eb;
		transform: translateY(-1px);
	}
	
	.ticker-section {
		margin: -2rem -2rem 2rem -2rem;
	}
	
	/* Mobile Styles */
	@media (max-width: 768px) {
		.dashboard {
			padding: 0 1rem;
		}
		
		.dashboard-header h1 {
			font-size: 1.5rem;
		}
		
		.grid-cols-2 {
			grid-template-columns: 1fr;
		}
		
		.card {
			margin-bottom: 1rem;
		}
		
		.controls {
			flex-direction: column;
		}
		
		.date-range-select,
		.refresh-button {
			width: 100%;
		}
		
		.ticker-section {
			margin: -1rem -1rem 1rem -1rem;
		}
	}
	
	@media (max-width: 640px) {
		.dashboard-header {
			text-align: center;
			margin-bottom: 1.5rem;
		}
		
		.dashboard-header h1 {
			font-size: 1.25rem;
		}
		
		.dashboard-header p {
			font-size: 0.875rem;
		}
		
		h2 {
			font-size: 1rem;
			margin-bottom: 0.75rem;
		}
		
		.welcome-container h1 {
			font-size: 2rem;
		}
		
		.welcome-container p {
			font-size: 1rem;
		}
		
		.welcome-actions {
			flex-direction: column;
		}
		
		.primary-button,
		.secondary-button {
			width: 100%;
			padding: 0.875rem 1.5rem;
			font-size: 1rem;
		}
		
		.controls {
			gap: 0.5rem;
			margin-bottom: 1.5rem;
		}
		
		.date-range-select,
		.refresh-button {
			padding: 0.625rem 1rem;
		}
	}
</style>