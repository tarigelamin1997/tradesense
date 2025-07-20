<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$lib/api/auth';
	import { get } from 'svelte/store';
	import { logger } from '$lib/utils/logger';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import DataExport from '$lib/components/DataExport.svelte';
	import { Filter, ChevronDown, ArrowUpDown, X } from 'lucide-svelte';
	
	let loading = true;
	let error = '';
	let trades: any[] = [];
	let filteredTrades: any[] = [];
	let showFilters = false;
	
	// Filter state
	let filters = {
		symbol: '',
		side: 'all',
		profitability: 'all',
		dateFrom: '',
		dateTo: '',
		minPnL: '',
		maxPnL: ''
	};
	
	// Sort state
	let sortBy = 'entryDate';
	let sortOrder: 'asc' | 'desc' = 'desc';
	
	const sortOptions = [
		{ value: 'entryDate', label: 'Entry Date' },
		{ value: 'symbol', label: 'Symbol' },
		{ value: 'pnl', label: 'P&L' },
		{ value: 'exitDate', label: 'Exit Date' },
		{ value: 'quantity', label: 'Quantity' }
	];

	async function fetchTrades() {
		try {
			loading = true;
			error = '';
			
			// Check if authenticated
			if (!get(isAuthenticated)) {
				goto('/login');
				return;
			}
			
			// For now, just use sample data
			trades = [
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
				}
			];
			
			trades = sampleTrades;
			applyFiltersAndSort();
		} catch (err: any) {
			logger.error('Failed to fetch trades:', err);
			error = 'Failed to load trades.';
		} finally {
			loading = false;
		}
	}
	
	function applyFiltersAndSort() {
		// Start with all trades
		let result = [...trades];
		
		// Apply filters
		if (filters.symbol) {
			result = result.filter(t => 
				t.symbol.toLowerCase().includes(filters.symbol.toLowerCase())
			);
		}
		
		if (filters.side !== 'all') {
			result = result.filter(t => t.side === filters.side);
		}
		
		if (filters.profitability !== 'all') {
			result = result.filter(t => 
				filters.profitability === 'profit' ? t.pnl > 0 : t.pnl <= 0
			);
		}
		
		if (filters.dateFrom) {
			result = result.filter(t => t.entryDate >= filters.dateFrom);
		}
		
		if (filters.dateTo) {
			result = result.filter(t => t.entryDate <= filters.dateTo);
		}
		
		if (filters.minPnL) {
			result = result.filter(t => t.pnl >= parseFloat(filters.minPnL));
		}
		
		if (filters.maxPnL) {
			result = result.filter(t => t.pnl <= parseFloat(filters.maxPnL));
		}
		
		// Apply sorting
		result.sort((a, b) => {
			let aVal = a[sortBy];
			let bVal = b[sortBy];
			
			// Handle numeric vs string comparison
			if (typeof aVal === 'number' && typeof bVal === 'number') {
				return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
			} else {
				// String comparison
				if (sortOrder === 'asc') {
					return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
				} else {
					return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
				}
			}
		});
		
		filteredTrades = result;
	}
	
	function clearFilters() {
		filters = {
			symbol: '',
			side: 'all',
			profitability: 'all',
			dateFrom: '',
			dateTo: '',
			minPnL: '',
			maxPnL: ''
		};
		applyFiltersAndSort();
	}
	
	function toggleSort(field: string) {
		if (sortBy === field) {
			sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
		} else {
			sortBy = field;
			sortOrder = 'desc';
		}
		applyFiltersAndSort();
	}
	
	// Reactive statement to reapply filters when they change
	$: if (trades.length > 0) {
		applyFiltersAndSort();
	}

	onMount(() => {
		fetchTrades();
	});
</script>

<svelte:head>
	<title>Trade Log - TradeSense</title>
</svelte:head>

<div class="tradelog-page">
	<header class="page-header">
		<div>
			<h1>Trade Log</h1>
			<p>Track and analyze all your trades</p>
		</div>
		<div class="header-actions">
			<DataExport 
				data={filteredTrades}
				filename="trades"
				buttonText="Export Trades"
			/>
			<button on:click={() => goto('/trades/new')} class="add-trade-button">
				Add Trade
			</button>
		</div>
	</header>
	
	<!-- Filter and Sort Bar -->
	<div class="filter-bar">
		<div class="filter-controls">
			<button class="filter-toggle" on:click={() => showFilters = !showFilters}>
				<Filter size={18} />
				Filters
				{#if Object.values(filters).some(v => v && v !== 'all')}
					<span class="filter-badge">Active</span>
				{/if}
			</button>
			
			<div class="sort-control">
				<label>Sort by:</label>
				<select bind:value={sortBy} on:change={() => applyFiltersAndSort()}>
					{#each sortOptions as option}
						<option value={option.value}>{option.label}</option>
					{/each}
				</select>
				<button class="sort-order" on:click={() => toggleSort(sortBy)}>
					<ArrowUpDown size={16} />
					{sortOrder === 'asc' ? 'Asc' : 'Desc'}
				</button>
			</div>
		</div>
		
		<div class="filter-summary">
			Showing {filteredTrades.length} of {trades.length} trades
			{#if Object.values(filters).some(v => v && v !== 'all')}
				<button class="clear-filters" on:click={clearFilters}>
					<X size={14} />
					Clear filters
				</button>
			{/if}
		</div>
	</div>
	
	<!-- Expandable Filters -->
	{#if showFilters}
		<div class="filters-panel">
			<div class="filters-grid">
				<div class="filter-group">
					<label for="symbol-filter">Symbol</label>
					<input
						id="symbol-filter"
						type="text"
						bind:value={filters.symbol}
						on:input={() => applyFiltersAndSort()}
						placeholder="e.g. AAPL"
					/>
				</div>
				
				<div class="filter-group">
					<label for="side-filter">Side</label>
					<select id="side-filter" bind:value={filters.side} on:change={() => applyFiltersAndSort()}>
						<option value="all">All</option>
						<option value="long">Long</option>
						<option value="short">Short</option>
					</select>
				</div>
				
				<div class="filter-group">
					<label for="profit-filter">Profitability</label>
					<select id="profit-filter" bind:value={filters.profitability} on:change={() => applyFiltersAndSort()}>
						<option value="all">All</option>
						<option value="profit">Profit</option>
						<option value="loss">Loss</option>
					</select>
				</div>
				
				<div class="filter-group">
					<label for="date-from">Date From</label>
					<input
						id="date-from"
						type="datetime-local"
						bind:value={filters.dateFrom}
						on:change={() => applyFiltersAndSort()}
					/>
				</div>
				
				<div class="filter-group">
					<label for="date-to">Date To</label>
					<input
						id="date-to"
						type="datetime-local"
						bind:value={filters.dateTo}
						on:change={() => applyFiltersAndSort()}
					/>
				</div>
				
				<div class="filter-group">
					<label for="min-pnl">Min P&L</label>
					<input
						id="min-pnl"
						type="number"
						bind:value={filters.minPnL}
						on:input={() => applyFiltersAndSort()}
						placeholder="0"
					/>
				</div>
				
				<div class="filter-group">
					<label for="max-pnl">Max P&L</label>
					<input
						id="max-pnl"
						type="number"
						bind:value={filters.maxPnL}
						on:input={() => applyFiltersAndSort()}
						placeholder="0"
					/>
				</div>
			</div>
		</div>
	{/if}
	
	{#if loading}
		<!-- Desktop Loading Skeleton -->
		<div class="desktop-only">
			<LoadingSkeleton type="table" lines={8} />
		</div>
		
		<!-- Mobile Loading Skeleton -->
		<div class="mobile-only">
			<div class="mobile-skeleton">
				{#each Array(5) as _}
					<LoadingSkeleton type="card" height="140px" />
				{/each}
			</div>
		</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else}
		<!-- Desktop Table View -->
		<div class="trades-table card desktop-only">
			<table>
				<thead>
					<tr>
						<th>Symbol</th>
						<th>Side</th>
						<th>Entry Price</th>
						<th>Exit Price</th>
						<th>Quantity</th>
						<th>P&L</th>
						<th>Entry Date</th>
						<th>Exit Date</th>
						<th>Strategy</th>
						<th>Notes</th>
					</tr>
				</thead>
				<tbody>
					{#each filteredTrades as trade}
						<tr>
							<td>{trade.symbol}</td>
							<td class="side-{trade.side}">{trade.side}</td>
							<td>${trade.entryPrice.toFixed(2)}</td>
							<td>${trade.exitPrice.toFixed(2)}</td>
							<td>{trade.quantity}</td>
							<td class:profit={trade.pnl > 0} class:loss={trade.pnl < 0}>
								${trade.pnl.toFixed(2)}
							</td>
							<td>{trade.entryDate}</td>
							<td>{trade.exitDate}</td>
							<td>{trade.strategy || '-'}</td>
							<td>{trade.notes || '-'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		
		<!-- Mobile Card View -->
		<div class="mobile-trades mobile-only">
			{#each filteredTrades as trade}
				<div class="trade-card">
					<div class="trade-header">
						<div class="trade-symbol">
							<span class="symbol">{trade.symbol}</span>
							<span class="side side-{trade.side}">{trade.side}</span>
						</div>
						<div class="trade-pnl" class:profit={trade.pnl > 0} class:loss={trade.pnl < 0}>
							${trade.pnl.toFixed(2)}
						</div>
					</div>
					
					<div class="trade-details">
						<div class="detail-row">
							<span class="label">Entry</span>
							<span class="value">${trade.entryPrice.toFixed(2)} @ {trade.entryDate}</span>
						</div>
						<div class="detail-row">
							<span class="label">Exit</span>
							<span class="value">${trade.exitPrice.toFixed(2)} @ {trade.exitDate}</span>
						</div>
						<div class="detail-row">
							<span class="label">Quantity</span>
							<span class="value">{trade.quantity}</span>
						</div>
						{#if trade.strategy}
							<div class="detail-row">
								<span class="label">Strategy</span>
								<span class="value">{trade.strategy}</span>
							</div>
						{/if}
						{#if trade.notes}
							<div class="detail-row full-width">
								<span class="label">Notes</span>
								<span class="value">{trade.notes}</span>
							</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.tradelog-page {
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
		align-items: center;
	}
	
	.add-trade-button {
		background: #10b981;
		color: white;
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 1rem;
		font-weight: 500;
		transition: background 0.2s;
	}
	
	.add-trade-button:hover {
		background: #059669;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
	}
	
	.loading {
		text-align: center;
		padding: 2rem;
		color: #666;
	}
	
	.error {
		background: #fee;
		color: #c00;
		padding: 1rem;
		border-radius: 6px;
		margin-bottom: 1rem;
	}
	
	.card {
		background: white;
		border-radius: 8px;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		padding: 1.5rem;
	}
	
	.trades-table {
		overflow-x: auto;
	}
	
	table {
		width: 100%;
		border-collapse: collapse;
	}
	
	th, td {
		text-align: left;
		padding: 0.75rem;
		border-bottom: 1px solid #e0e0e0;
	}
	
	th {
		font-weight: 600;
		color: #666;
		font-size: 0.875rem;
		text-transform: uppercase;
	}
	
	tr:hover {
		background: #f9f9f9;
	}
	
	table .side-long {
		color: #10b981;
		font-weight: 500;
	}
	
	table .side-short {
		color: #ef4444;
		font-weight: 500;
	}
	
	.profit {
		color: #10b981;
		font-weight: 500;
	}
	
	.loss {
		color: #ef4444;
		font-weight: 500;
	}
	
	/* Desktop/Mobile Visibility */
	.desktop-only {
		display: block;
	}
	
	.mobile-only {
		display: none;
	}
	
	/* Mobile Card View */
	.mobile-trades {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.trade-card {
		background: white;
		border-radius: 8px;
		padding: 1rem;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
		transition: transform 0.2s, box-shadow 0.2s;
	}
	
	.trade-card:active {
		transform: scale(0.98);
	}
	
	.trade-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid #e5e7eb;
	}
	
	.trade-symbol {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.symbol {
		font-size: 1.125rem;
		font-weight: 600;
		color: #1a1a1a;
	}
	
	.side {
		font-size: 0.75rem;
		font-weight: 600;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		text-transform: uppercase;
	}
	
	.side-long {
		background: #d1fae5;
		color: #065f46;
	}
	
	.side-short {
		background: #fee;
		color: #991b1b;
	}
	
	.trade-pnl {
		font-size: 1.25rem;
		font-weight: 600;
	}
	
	.trade-details {
		display: grid;
		gap: 0.75rem;
	}
	
	.detail-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.875rem;
	}
	
	.detail-row.full-width {
		flex-direction: column;
		align-items: flex-start;
		gap: 0.25rem;
	}
	
	.label {
		color: #6b7280;
		font-weight: 500;
	}
	
	.value {
		color: #1a1a1a;
		text-align: right;
	}
	
	.detail-row.full-width .value {
		text-align: left;
		color: #4b5563;
	}
	
	@media (max-width: 768px) {
		.tradelog-page {
			padding: 0 1rem 4rem;
		}
		
		.desktop-only {
			display: none;
		}
		
		.mobile-only {
			display: block;
		}
		
		.page-header {
			flex-direction: column;
			align-items: stretch;
		}
		
		.page-header h1 {
			font-size: 1.75rem;
		}
		
		.add-trade-button {
			width: 100%;
		}
		
		.header-actions {
			width: 100%;
			flex-direction: column;
			gap: 1rem;
		}
		
		.mobile-skeleton {
			display: flex;
			flex-direction: column;
			gap: 1rem;
		}
	}
	
	/* Filter and Sort Styles */
	.filter-bar {
		background: white;
		padding: 1rem 1.5rem;
		border-radius: 8px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		margin-bottom: 1.5rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-wrap: wrap;
		gap: 1rem;
	}
	
	.filter-controls {
		display: flex;
		align-items: center;
		gap: 2rem;
	}
	
	.filter-toggle {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: #f3f4f6;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.filter-toggle:hover {
		background: #e5e7eb;
		border-color: #d1d5db;
	}
	
	.filter-badge {
		background: #10b981;
		color: white;
		padding: 0.125rem 0.5rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 600;
	}
	
	.sort-control {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
	}
	
	.sort-control label {
		color: #6b7280;
		font-weight: 500;
	}
	
	.sort-control select {
		padding: 0.375rem 0.75rem;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		background: white;
		font-size: 0.875rem;
		color: #374151;
		cursor: pointer;
	}
	
	.sort-order {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.375rem 0.75rem;
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		font-size: 0.875rem;
		color: #374151;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.sort-order:hover {
		background: #f9fafb;
		border-color: #d1d5db;
	}
	
	.filter-summary {
		display: flex;
		align-items: center;
		gap: 1rem;
		font-size: 0.875rem;
		color: #6b7280;
	}
	
	.clear-filters {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.25rem 0.75rem;
		background: #fee;
		color: #dc2626;
		border: 1px solid #fecaca;
		border-radius: 6px;
		font-size: 0.75rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.clear-filters:hover {
		background: #fecaca;
		border-color: #f87171;
	}
	
	/* Filters Panel */
	.filters-panel {
		background: white;
		padding: 1.5rem;
		border-radius: 8px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		margin-bottom: 1.5rem;
		animation: slideDown 0.2s ease-out;
	}
	
	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	
	.filters-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}
	
	.filter-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.filter-group label {
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
	}
	
	.filter-group input,
	.filter-group select {
		padding: 0.5rem 0.75rem;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		font-size: 0.875rem;
		transition: border-color 0.2s;
	}
	
	.filter-group input:focus,
	.filter-group select:focus {
		outline: none;
		border-color: #10b981;
	}
	
	/* Mobile Filter Styles */
	@media (max-width: 768px) {
		.filter-bar {
			flex-direction: column;
			align-items: stretch;
			padding: 1rem;
		}
		
		.filter-controls {
			flex-direction: column;
			width: 100%;
			gap: 1rem;
		}
		
		.filter-toggle {
			width: 100%;
			justify-content: center;
		}
		
		.sort-control {
			width: 100%;
			justify-content: space-between;
		}
		
		.sort-control select {
			flex: 1;
		}
		
		.filter-summary {
			justify-content: center;
			text-align: center;
		}
		
		.filters-grid {
			grid-template-columns: 1fr;
		}
	}
</style>