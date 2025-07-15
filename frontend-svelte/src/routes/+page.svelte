<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
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
	
	let loading = true;
	let error = '';
	let usingSampleData = false;
	let dateRange = '30d';
	let userPlan: 'free' | 'pro' | 'enterprise' = 'free';
	
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
			
			// Check if authenticated
			if (!get(isAuthenticated)) {
				console.log('Not authenticated, redirecting to login');
				goto('/login');
				return;
			}
			
			console.log('Fetching analytics data...');
			
			// Try to get summary and subscription data
			try {
				const [summaryData, subscription] = await Promise.all([
					analyticsApi.getSummary({ period: dateRange as any }),
					billingApi.getSubscription()
				]);
				console.log('Summary data:', summaryData);
				
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
				console.error('Failed to fetch summary:', summaryError);
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
				console.error('Failed to fetch trades:', tradesError);
				// Continue with empty trades if this fails
				recentTrades = [];
			}
			
		} catch (err: any) {
			console.error('Failed to fetch data:', err);
			
			// Use sample data as fallback
			const { sampleStats, sampleEquityData, samplePnlData, sampleTrades } = generateSampleData();
			stats = sampleStats;
			equityData = sampleEquityData;
			pnlData = samplePnlData;
			recentTrades = sampleTrades;
			tradeStore.setTrades(sampleTrades);
			usingSampleData = true;
			
			if (err.status === 401) {
				goto('/login');
			} else {
				error = 'Failed to load data. Using sample data.';
			}
		} finally {
			loading = false;
		}
	}
	
	onMount(() => {
		fetchData();
	});
	
	// Handle date range change
	$: if (dateRange) {
		fetchData();
	}
</script>

<svelte:head>
	<title>Dashboard - TradeSense</title>
</svelte:head>

{#if loading}
	<div class="loading">Loading dashboard...</div>
{:else if error}
	<div class="error">{error}</div>
{:else if stats.totalTrades === 0 && !usingSampleData}
	<!-- Welcome message for new users -->
	<div class="dashboard">
		<div class="welcome-container">
			<h1>Welcome to TradeSense! 🎉</h1>
			<p>Start tracking your trades to see analytics and insights.</p>
			<div class="welcome-actions">
				<a href="/trades" class="primary-button">Add Your First Trade</a>
				<button on:click={() => {
					const { sampleStats, sampleEquityData, samplePnlData, sampleTrades } = generateSampleData();
					stats = sampleStats;
					equityData = sampleEquityData;
					pnlData = samplePnlData;
					recentTrades = sampleTrades;
					usingSampleData = true;
				}} class="secondary-button">View Demo Data</button>
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
			<h1>Trading Dashboard</h1>
			<p>{usingSampleData ? 'Demo Data' : `Last ${dateRange}`}</p>
		</header>
		
		<!-- Date Range Selector -->
		<div class="controls">
			<select bind:value={dateRange} class="date-range-select">
				<option value="7d">Last 7 days</option>
				<option value="30d">Last 30 days</option>
				<option value="90d">Last 90 days</option>
				<option value="1y">Last year</option>
			</select>
			<button on:click={fetchData} class="refresh-button" disabled={loading}>
				{loading ? 'Loading...' : 'Refresh'}
			</button>
		</div>
		
		<!-- Metrics Grid -->
		<div class="grid grid-cols-4">
			<MetricCard 
				title="Total P&L" 
				value={stats.totalPnl} 
				format="currency"
				trend={stats.totalPnlPercent}
			/>
			<MetricCard 
				title="Win Rate" 
				value={stats.winRate} 
				format="percent"
				trend={stats.winRateChange}
			/>
			<MetricCard 
				title="Total Trades" 
				value={stats.totalTrades} 
				format="number"
			/>
			<MetricCard 
				title="Current Streak" 
				value={stats.currentStreak.count} 
				format="streak"
				streakType={stats.currentStreak.type}
			/>
		</div>
		
		<!-- Charts Grid -->
		<div class="grid grid-cols-2">
			<div class="card">
				<h2>Equity Curve</h2>
				<EquityChart data={equityData} />
			</div>
			<div class="card">
				<h2>Daily P&L</h2>
				<PnLChart data={pnlData} />
			</div>
		</div>
		
		<!-- AI Insights -->
		<TradeInsights trades={recentTrades} {userPlan} />
		
		<!-- Recent Trades -->
		<div class="card">
			<h2>Recent Trades</h2>
			<TradeList trades={recentTrades} />
		</div>
	</div>
{/if}

<style>
	.dashboard {
		max-width: 1200px;
		margin: 0 auto;
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