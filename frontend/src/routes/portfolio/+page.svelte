<script lang="ts">
	import { onMount } from 'svelte';
	import { 
		TrendingUp, 
		TrendingDown, 
		DollarSign, 
		Percent, 
		Calendar,
		AlertCircle,
		Filter,
		Download
	} from 'lucide-svelte';
	import { api } from '$lib/api/client-safe';
	import { logger } from '$lib/utils/logger';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	
	let loading = true;
	let error = '';
	let selectedTimeframe = '30d';
	let selectedAssetClass = 'all';
	
	// Portfolio data
	let portfolio = {
		totalValue: 0,
		totalCost: 0,
		totalPnL: 0,
		totalPnLPercent: 0,
		positions: [] as Position[],
		allocations: [] as Allocation[],
		performance: [] as PerformanceData[]
	};
	
	interface Position {
		symbol: string;
		quantity: number;
		avgPrice: number;
		currentPrice: number;
		value: number;
		cost: number;
		pnl: number;
		pnlPercent: number;
		allocation: number;
		assetClass: string;
		lastTradeDate: string;
	}
	
	interface Allocation {
		assetClass: string;
		value: number;
		percentage: number;
		color: string;
	}
	
	interface PerformanceData {
		date: string;
		value: number;
		pnl: number;
	}
	
	const timeframes = [
		{ value: '7d', label: '7 Days' },
		{ value: '30d', label: '30 Days' },
		{ value: '90d', label: '90 Days' },
		{ value: '1y', label: '1 Year' },
		{ value: 'all', label: 'All Time' }
	];
	
	const assetClasses = [
		{ value: 'all', label: 'All Assets' },
		{ value: 'stocks', label: 'Stocks' },
		{ value: 'options', label: 'Options' },
		{ value: 'futures', label: 'Futures' },
		{ value: 'forex', label: 'Forex' },
		{ value: 'crypto', label: 'Crypto' }
	];
	
	const allocationColors = {
		stocks: '#10b981',
		options: '#3b82f6',
		futures: '#f59e0b',
		forex: '#8b5cf6',
		crypto: '#ef4444',
		other: '#6b7280'
	};
	
	async function fetchPortfolio() {
		loading = true;
		error = '';
		
		try {
			// Fetch portfolio data
			const response = await api.get('/api/v1/portfolio', {
				params: {
					timeframe: selectedTimeframe,
					assetClass: selectedAssetClass === 'all' ? undefined : selectedAssetClass
				}
			});
			
			portfolio = response;
			
			// Calculate allocations if not provided
			if (!portfolio.allocations || portfolio.allocations.length === 0) {
				calculateAllocations();
			}
			
		} catch (err: any) {
			logger.error('Failed to fetch portfolio:', err);
			
			// Generate sample data for demo
			generateSampleData();
		} finally {
			loading = false;
		}
	}
	
	function calculateAllocations() {
		const allocationMap = new Map<string, number>();
		
		portfolio.positions.forEach(position => {
			const assetClass = position.assetClass || 'other';
			const currentValue = allocationMap.get(assetClass) || 0;
			allocationMap.set(assetClass, currentValue + position.value);
		});
		
		portfolio.allocations = Array.from(allocationMap.entries()).map(([assetClass, value]) => ({
			assetClass,
			value,
			percentage: (value / portfolio.totalValue) * 100,
			color: allocationColors[assetClass] || allocationColors.other
		}));
	}
	
	function generateSampleData() {
		// Sample positions
		const samplePositions: Position[] = [
			{
				symbol: 'AAPL',
				quantity: 100,
				avgPrice: 150.00,
				currentPrice: 175.50,
				value: 17550,
				cost: 15000,
				pnl: 2550,
				pnlPercent: 17.0,
				allocation: 25.5,
				assetClass: 'stocks',
				lastTradeDate: '2024-01-15'
			},
			{
				symbol: 'TSLA',
				quantity: 50,
				avgPrice: 200.00,
				currentPrice: 185.25,
				value: 9262.50,
				cost: 10000,
				pnl: -737.50,
				pnlPercent: -7.38,
				allocation: 13.5,
				assetClass: 'stocks',
				lastTradeDate: '2024-01-10'
			},
			{
				symbol: 'BTC-USD',
				quantity: 0.5,
				avgPrice: 40000,
				currentPrice: 45000,
				value: 22500,
				cost: 20000,
				pnl: 2500,
				pnlPercent: 12.5,
				allocation: 32.7,
				assetClass: 'crypto',
				lastTradeDate: '2024-01-08'
			},
			{
				symbol: 'EUR/USD',
				quantity: 10000,
				avgPrice: 1.08,
				currentPrice: 1.095,
				value: 10950,
				cost: 10800,
				pnl: 150,
				pnlPercent: 1.39,
				allocation: 15.9,
				assetClass: 'forex',
				lastTradeDate: '2024-01-12'
			},
			{
				symbol: 'SPY 450C',
				quantity: 10,
				avgPrice: 5.50,
				currentPrice: 8.25,
				value: 8250,
				cost: 5500,
				pnl: 2750,
				pnlPercent: 50.0,
				allocation: 12.0,
				assetClass: 'options',
				lastTradeDate: '2024-01-14'
			}
		];
		
		const totalValue = samplePositions.reduce((sum, pos) => sum + pos.value, 0);
		const totalCost = samplePositions.reduce((sum, pos) => sum + pos.cost, 0);
		const totalPnL = totalValue - totalCost;
		const totalPnLPercent = (totalPnL / totalCost) * 100;
		
		// Sample performance data
		const performanceData: PerformanceData[] = [];
		const days = selectedTimeframe === '7d' ? 7 : selectedTimeframe === '30d' ? 30 : 90;
		let currentValue = totalCost;
		
		for (let i = days; i >= 0; i--) {
			const date = new Date();
			date.setDate(date.getDate() - i);
			
			// Simulate random walk
			const change = (Math.random() - 0.48) * 0.02 * currentValue;
			currentValue += change;
			
			performanceData.push({
				date: date.toISOString().split('T')[0],
				value: currentValue,
				pnl: currentValue - totalCost
			});
		}
		
		// Ensure last value matches current
		if (performanceData.length > 0) {
			performanceData[performanceData.length - 1].value = totalValue;
			performanceData[performanceData.length - 1].pnl = totalPnL;
		}
		
		portfolio = {
			totalValue,
			totalCost,
			totalPnL,
			totalPnLPercent,
			positions: samplePositions,
			allocations: [],
			performance: performanceData
		};
		
		calculateAllocations();
	}
	
	function formatCurrency(value: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(value);
	}
	
	function formatPercent(value: number): string {
		return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
	}
	
	async function exportPortfolio() {
		try {
			const response = await api.get('/api/v1/portfolio/export', {
				params: { format: 'csv' },
				responseType: 'blob'
			});
			
			const url = window.URL.createObjectURL(new Blob([response]));
			const link = document.createElement('a');
			link.href = url;
			link.setAttribute('download', `portfolio_${new Date().toISOString().split('T')[0]}.csv`);
			document.body.appendChild(link);
			link.click();
			link.remove();
		} catch (err) {
			logger.error('Failed to export portfolio:', err);
			// For demo, create sample CSV
			const csv = 'Symbol,Quantity,Avg Price,Current Price,Value,P&L,P&L %,Allocation\n' +
				portfolio.positions.map(p => 
					`${p.symbol},${p.quantity},${p.avgPrice},${p.currentPrice},${p.value},${p.pnl},${p.pnlPercent},${p.allocation}`
				).join('\n');
			
			const blob = new Blob([csv], { type: 'text/csv' });
			const url = window.URL.createObjectURL(blob);
			const link = document.createElement('a');
			link.href = url;
			link.setAttribute('download', `portfolio_${new Date().toISOString().split('T')[0]}.csv`);
			document.body.appendChild(link);
			link.click();
			link.remove();
		}
	}
	
	onMount(() => {
		fetchPortfolio();
	});
	
	// Refetch when filters change
	$: if (selectedTimeframe || selectedAssetClass) {
		fetchPortfolio();
	}
</script>

<svelte:head>
	<title>Portfolio - TradeSense</title>
</svelte:head>

<div class="portfolio-page">
	<header class="page-header">
		<div>
			<h1>Portfolio Overview</h1>
			<p>Track your positions and overall performance</p>
		</div>
		<div class="header-actions">
			<button class="export-button" on:click={exportPortfolio}>
				<Download size={18} />
				Export
			</button>
		</div>
	</header>
	
	{#if loading}
		<div class="portfolio-skeleton">
			<!-- Summary Cards -->
			<div class="summary-cards">
				{#each Array(4) as _}
					<LoadingSkeleton type="stat" />
				{/each}
			</div>
			
			<!-- Chart -->
			<LoadingSkeleton type="chart" height="400px" />
			
			<!-- Positions Table -->
			<LoadingSkeleton type="table" lines={5} />
		</div>
	{:else if error}
		<div class="error">
			<AlertCircle size={20} />
			{error}
		</div>
	{:else}
		<!-- Filters -->
		<div class="filters">
			<select bind:value={selectedTimeframe} class="filter-select">
				{#each timeframes as timeframe}
					<option value={timeframe.value}>{timeframe.label}</option>
				{/each}
			</select>
			
			<select bind:value={selectedAssetClass} class="filter-select">
				{#each assetClasses as assetClass}
					<option value={assetClass.value}>{assetClass.label}</option>
				{/each}
			</select>
		</div>
		
		<!-- Summary Cards -->
		<div class="summary-cards">
			<div class="summary-card">
				<div class="card-label">Total Value</div>
				<div class="card-value">{formatCurrency(portfolio.totalValue)}</div>
				<div class="card-change">
					<DollarSign size={16} />
					Portfolio Value
				</div>
			</div>
			
			<div class="summary-card">
				<div class="card-label">Total P&L</div>
				<div class="card-value" class:positive={portfolio.totalPnL >= 0} class:negative={portfolio.totalPnL < 0}>
					{formatCurrency(portfolio.totalPnL)}
				</div>
				<div class="card-change" class:positive={portfolio.totalPnL >= 0} class:negative={portfolio.totalPnL < 0}>
					{#if portfolio.totalPnL >= 0}
						<TrendingUp size={16} />
					{:else}
						<TrendingDown size={16} />
					{/if}
					{formatPercent(portfolio.totalPnLPercent)}
				</div>
			</div>
			
			<div class="summary-card">
				<div class="card-label">Positions</div>
				<div class="card-value">{portfolio.positions.length}</div>
				<div class="card-change">
					<Calendar size={16} />
					Active Positions
				</div>
			</div>
			
			<div class="summary-card">
				<div class="card-label">Win Rate</div>
				<div class="card-value">
					{((portfolio.positions.filter(p => p.pnl > 0).length / portfolio.positions.length) * 100).toFixed(0)}%
				</div>
				<div class="card-change">
					<Percent size={16} />
					Profitable Positions
				</div>
			</div>
		</div>
		
		<!-- Portfolio Chart -->
		<div class="portfolio-chart card">
			<h2>Portfolio Performance</h2>
			<div class="chart-container">
				<!-- Simple line chart using SVG -->
				{#if portfolio.performance.length > 0}
					{@const maxValue = Math.max(...portfolio.performance.map(p => p.value))}
					{@const minValue = Math.min(...portfolio.performance.map(p => p.value))}
					{@const range = maxValue - minValue || 1}
					{@const points = portfolio.performance.map((p, i) => {
						const x = (i / (portfolio.performance.length - 1)) * 780 + 10;
						const y = 290 - ((p.value - minValue) / range) * 280;
						return `${x},${y}`;
					}).join(' ')}
					<svg viewBox="0 0 800 300" class="performance-chart">
						
						<!-- Grid lines -->
						{#each Array(5) as _, i}
							<line 
								x1="10" 
								x2="790" 
								y1={10 + i * 70} 
								y2={10 + i * 70} 
								stroke="#e5e7eb" 
								stroke-width="1"
							/>
						{/each}
						
						<!-- Area fill -->
						<polygon 
							points={`10,290 ${points} 790,290`}
							fill="url(#gradient)"
							opacity="0.1"
						/>
						
						<!-- Line -->
						<polyline
							points={points}
							fill="none"
							stroke={portfolio.totalPnL >= 0 ? '#10b981' : '#ef4444'}
							stroke-width="2"
						/>
						
						<!-- Gradient definition -->
						<defs>
							<linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
								<stop offset="0%" style="stop-color:{portfolio.totalPnL >= 0 ? '#10b981' : '#ef4444'}" />
								<stop offset="100%" style="stop-color:{portfolio.totalPnL >= 0 ? '#10b981' : '#ef4444'};stop-opacity:0" />
							</linearGradient>
						</defs>
					</svg>
				{/if}
			</div>
		</div>
		
		<!-- Asset Allocation -->
		<div class="allocation-section">
			<div class="allocation-chart card">
				<h2>Asset Allocation</h2>
				<div class="donut-chart">
					<svg viewBox="0 0 200 200" class="donut">
						{#each portfolio.allocations as allocation, i}
							{@const radius = 80}
							{@const circumference = 2 * Math.PI * radius}
							{@const offset = portfolio.allocations
								.slice(0, i)
								.reduce((sum, a) => sum + a.percentage, 0) / 100 * circumference}
							{@const length = allocation.percentage / 100 * circumference}
							<circle
								cx="100"
								cy="100"
								r={radius}
								fill="none"
								stroke={allocation.color}
								stroke-width="40"
								stroke-dasharray={`${length} ${circumference - length}`}
								stroke-dashoffset={-offset}
								transform="rotate(-90 100 100)"
							/>
						{/each}
						<text x="100" y="100" text-anchor="middle" dominant-baseline="middle" class="donut-center">
							{portfolio.allocations.length}
							<tspan x="100" dy="20" font-size="12">Asset Classes</tspan>
						</text>
					</svg>
				</div>
				<div class="allocation-legend">
					{#each portfolio.allocations as allocation}
						<div class="legend-item">
							<div class="legend-color" style="background: {allocation.color}"></div>
							<span class="legend-label">{allocation.assetClass}</span>
							<span class="legend-value">{allocation.percentage.toFixed(1)}%</span>
						</div>
					{/each}
				</div>
			</div>
			
			<!-- Top Performers -->
			<div class="top-performers card">
				<h2>Top Performers</h2>
				<div class="performers-list">
					{#each portfolio.positions.sort((a, b) => b.pnlPercent - a.pnlPercent).slice(0, 5) as position}
						<div class="performer-item">
							<div class="performer-info">
								<span class="performer-symbol">{position.symbol}</span>
								<span class="performer-class">{position.assetClass}</span>
							</div>
							<div class="performer-pnl" class:positive={position.pnl > 0} class:negative={position.pnl < 0}>
								{formatPercent(position.pnlPercent)}
							</div>
						</div>
					{/each}
				</div>
			</div>
		</div>
		
		<!-- Positions Table -->
		<div class="positions-section">
			<h2>Current Positions</h2>
			
			<!-- Desktop Table -->
			<div class="positions-table card desktop-only">
				<table>
					<thead>
						<tr>
							<th>Symbol</th>
							<th>Quantity</th>
							<th>Avg Price</th>
							<th>Current Price</th>
							<th>Value</th>
							<th>P&L</th>
							<th>P&L %</th>
							<th>Allocation</th>
						</tr>
					</thead>
					<tbody>
						{#each portfolio.positions as position}
							<tr>
								<td>
									<div class="symbol-cell">
										<span class="symbol">{position.symbol}</span>
										<span class="asset-class">{position.assetClass}</span>
									</div>
								</td>
								<td>{position.quantity}</td>
								<td>${position.avgPrice.toFixed(2)}</td>
								<td>${position.currentPrice.toFixed(2)}</td>
								<td>{formatCurrency(position.value)}</td>
								<td class:positive={position.pnl > 0} class:negative={position.pnl < 0}>
									{formatCurrency(position.pnl)}
								</td>
								<td class:positive={position.pnl > 0} class:negative={position.pnl < 0}>
									{formatPercent(position.pnlPercent)}
								</td>
								<td>{position.allocation.toFixed(1)}%</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
			
			<!-- Mobile Cards -->
			<div class="positions-cards mobile-only">
				{#each portfolio.positions as position}
					<div class="position-card">
						<div class="position-header">
							<div class="position-symbol">
								<span class="symbol">{position.symbol}</span>
								<span class="asset-class">{position.assetClass}</span>
							</div>
							<div class="position-pnl" class:positive={position.pnl > 0} class:negative={position.pnl < 0}>
								{formatCurrency(position.pnl)}
								<span class="pnl-percent">{formatPercent(position.pnlPercent)}</span>
							</div>
						</div>
						
						<div class="position-details">
							<div class="detail-row">
								<span class="label">Quantity</span>
								<span class="value">{position.quantity}</span>
							</div>
							<div class="detail-row">
								<span class="label">Avg Price</span>
								<span class="value">${position.avgPrice.toFixed(2)}</span>
							</div>
							<div class="detail-row">
								<span class="label">Current Price</span>
								<span class="value">${position.currentPrice.toFixed(2)}</span>
							</div>
							<div class="detail-row">
								<span class="label">Value</span>
								<span class="value">{formatCurrency(position.value)}</span>
							</div>
							<div class="detail-row">
								<span class="label">Allocation</span>
								<span class="value">{position.allocation.toFixed(1)}%</span>
							</div>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.portfolio-page {
		max-width: 1400px;
		margin: 0 auto;
		padding-bottom: 4rem;
	}
	
	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		flex-wrap: wrap;
		gap: 1rem;
	}
	
	.page-header h1 {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}
	
	.page-header p {
		color: #666;
	}
	
	.header-actions {
		display: flex;
		gap: 1rem;
	}
	
	.export-button {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1.5rem;
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.export-button:hover {
		background: #f9fafb;
		border-color: #d1d5db;
	}
	
	/* Filters */
	.filters {
		display: flex;
		gap: 1rem;
		margin-bottom: 2rem;
		flex-wrap: wrap;
	}
	
	.filter-select {
		padding: 0.5rem 1rem;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		background: white;
		font-size: 0.875rem;
		color: #374151;
		cursor: pointer;
		transition: border-color 0.2s;
	}
	
	.filter-select:focus {
		outline: none;
		border-color: #10b981;
	}
	
	/* Summary Cards */
	.summary-cards {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.summary-card {
		background: white;
		padding: 1.5rem;
		border-radius: 8px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
	
	.card-label {
		font-size: 0.875rem;
		color: #6b7280;
		margin-bottom: 0.5rem;
	}
	
	.card-value {
		font-size: 2rem;
		font-weight: 600;
		color: #1a1a1a;
		margin-bottom: 0.5rem;
	}
	
	.card-value.positive {
		color: #10b981;
	}
	
	.card-value.negative {
		color: #ef4444;
	}
	
	.card-change {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		font-size: 0.875rem;
		color: #6b7280;
	}
	
	.card-change.positive {
		color: #10b981;
	}
	
	.card-change.negative {
		color: #ef4444;
	}
	
	/* Common Card Styles */
	.card {
		background: white;
		padding: 1.5rem;
		border-radius: 8px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
	
	.card h2 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
		color: #1a1a1a;
	}
	
	/* Portfolio Chart */
	.portfolio-chart {
		margin-bottom: 2rem;
	}
	
	.chart-container {
		height: 300px;
		position: relative;
	}
	
	.performance-chart {
		width: 100%;
		height: 100%;
	}
	
	/* Allocation Section */
	.allocation-section {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 2rem;
		margin-bottom: 2rem;
	}
	
	.donut-chart {
		width: 200px;
		height: 200px;
		margin: 0 auto 1.5rem;
	}
	
	.donut {
		width: 100%;
		height: 100%;
	}
	
	.donut-center {
		font-size: 24px;
		font-weight: 600;
		fill: #1a1a1a;
	}
	
	.donut-center tspan {
		fill: #6b7280;
		font-weight: 400;
	}
	
	.allocation-legend {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	
	.legend-color {
		width: 16px;
		height: 16px;
		border-radius: 4px;
	}
	
	.legend-label {
		flex: 1;
		font-size: 0.875rem;
		color: #4b5563;
		text-transform: capitalize;
	}
	
	.legend-value {
		font-size: 0.875rem;
		font-weight: 600;
		color: #1a1a1a;
	}
	
	/* Top Performers */
	.performers-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.performer-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem;
		background: #f9fafb;
		border-radius: 6px;
	}
	
	.performer-info {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	
	.performer-symbol {
		font-weight: 600;
		color: #1a1a1a;
	}
	
	.performer-class {
		font-size: 0.75rem;
		color: #6b7280;
		text-transform: capitalize;
	}
	
	.performer-pnl {
		font-size: 1.125rem;
		font-weight: 600;
	}
	
	/* Positions Section */
	.positions-section {
		margin-top: 2rem;
	}
	
	.positions-section h2 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
		color: #1a1a1a;
	}
	
	/* Desktop Table */
	.positions-table {
		overflow-x: auto;
	}
	
	table {
		width: 100%;
		border-collapse: collapse;
	}
	
	th, td {
		text-align: left;
		padding: 0.75rem;
		border-bottom: 1px solid #e5e7eb;
	}
	
	th {
		font-weight: 600;
		color: #6b7280;
		font-size: 0.875rem;
		text-transform: uppercase;
	}
	
	tr:hover {
		background: #f9fafb;
	}
	
	.symbol-cell {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
	}
	
	.symbol {
		font-weight: 600;
		color: #1a1a1a;
	}
	
	.asset-class {
		font-size: 0.75rem;
		color: #6b7280;
		text-transform: capitalize;
	}
	
	.positive {
		color: #10b981;
		font-weight: 500;
	}
	
	.negative {
		color: #ef4444;
		font-weight: 500;
	}
	
	/* Mobile Cards */
	.position-card {
		background: white;
		border-radius: 8px;
		padding: 1rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		margin-bottom: 1rem;
	}
	
	.position-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid #e5e7eb;
	}
	
	.position-symbol {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
	}
	
	.position-pnl {
		text-align: right;
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
	}
	
	.position-pnl .pnl-percent {
		font-size: 0.875rem;
	}
	
	.position-details {
		display: grid;
		gap: 0.75rem;
	}
	
	.detail-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.875rem;
	}
	
	.detail-row .label {
		color: #6b7280;
	}
	
	.detail-row .value {
		color: #1a1a1a;
		font-weight: 500;
	}
	
	/* Loading Skeleton */
	.portfolio-skeleton {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}
	
	/* Error State */
	.error {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: #fee;
		color: #dc2626;
		padding: 1rem;
		border-radius: 6px;
		margin-bottom: 1rem;
	}
	
	/* Visibility Classes */
	.desktop-only {
		display: block;
	}
	
	.mobile-only {
		display: none;
	}
	
	/* Mobile Styles */
	@media (max-width: 768px) {
		.portfolio-page {
			padding: 0 1rem 4rem;
		}
		
		.page-header {
			flex-direction: column;
			align-items: flex-start;
		}
		
		.page-header h1 {
			font-size: 1.75rem;
		}
		
		.summary-cards {
			grid-template-columns: repeat(2, 1fr);
			gap: 1rem;
		}
		
		.allocation-section {
			grid-template-columns: 1fr;
		}
		
		.desktop-only {
			display: none;
		}
		
		.mobile-only {
			display: block;
		}
		
		.positions-cards {
			display: flex;
			flex-direction: column;
			gap: 1rem;
		}
	}
</style>