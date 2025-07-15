<script lang="ts">
	import { onMount } from 'svelte';
	import { tradeStore, type Trade } from '$lib/stores/trades';
	import TradeListWithSelection from '$lib/components/TradeListWithSelection.svelte';
	import TradeFiltersAdvanced from '$lib/components/TradeFiltersAdvanced.svelte';
	import TradeStats from '$lib/components/TradeStats.svelte';
	import TradeForm from '$lib/components/TradeFormEnhanced.svelte';
	import ExportDialog from '$lib/components/ExportDialog.svelte';
	import BulkActions from '$lib/components/BulkActions.svelte';
	import { tradesApi, type Trade as ApiTrade, type TradeFilters } from '$lib/api/trades';
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$lib/api/auth';
	import { get } from 'svelte/store';
	import { useBulkSelection } from '$lib/hooks/useBulkSelection';
	import { TradeExporter } from '$lib/utils/exporters';
	import { tradeUpdates } from '$lib/stores/websocket';
	import { billingApi, type Usage } from '$lib/api/billing';
	import UsageLimiter from '$lib/components/UsageLimiter.svelte';
	import FeatureGate from '$lib/components/FeatureGate.svelte';
	
	let loading = true;
	let error = '';
	let trades: Trade[] = [];
	let filteredTrades: Trade[] = [];
	let selectedTrade: ApiTrade | null = null;
	let showTradeForm = false;
	let showExportDialog = false;
	let usage: Usage | null = null;
	let userPlan: 'free' | 'pro' | 'enterprise' = 'free';
	let stats = {
		totalTrades: 0,
		totalPnl: 0,
		winRate: 0,
		avgWin: 0,
		avgLoss: 0,
		profitFactor: 0
	};
	
	// Bulk selection
	let selection = useBulkSelection<Trade>([]);
	
	async function handleAddTrade() {
		// Check usage limits
		if (usage && usage.trades_limit !== -1 && usage.trades_count >= usage.trades_limit) {
			error = 'You have reached your monthly trade limit. Please upgrade your plan to add more trades.';
			return;
		}
		
		selectedTrade = null;
		showTradeForm = true;
	}
	
	function handleEditTrade(event: CustomEvent<{ trade: any }>) {
		const trade = event.detail.trade;
		selectedTrade = {
			id: trade.id,
			symbol: trade.symbol,
			side: trade.side,
			entry_price: trade.entryPrice,
			exit_price: trade.exitPrice,
			quantity: trade.quantity,
			entry_date: trade.entryDate,
			exit_date: trade.exitDate,
			strategy: trade.strategy,
			notes: trade.notes
		};
		showTradeForm = true;
	}
	
	async function handleSaveTrade(event: CustomEvent<{ type: string; trade: ApiTrade }>) {
		await fetchTrades();
		selection.deselectAll();
	}
	
	async function handleDeleteTrade(event: CustomEvent<{ id: number }>) {
		if (confirm('Are you sure you want to delete this trade?')) {
			try {
				await tradesApi.deleteTrade(event.detail.id);
				await fetchTrades();
				selection.deselectAll();
			} catch (err: any) {
				error = err.message || 'Failed to delete trade';
			}
		}
	}
	
	// Subscribe to trade store
	tradeStore.subscribe(value => {
		trades = value;
		// Update selection items when trades change
		const selectedIds = selection.getSelectedIds();
		selection = useBulkSelection(trades);
		// Restore selection
		selectedIds.forEach(id => {
			const trade = trades.find(t => t.id === id);
			if (trade) selection.select(trade);
		});
		applyFilters();
	});
	
	function calculateStats() {
		const wins = filteredTrades.filter(t => t.pnl > 0);
		const losses = filteredTrades.filter(t => t.pnl < 0);
		
		stats = {
			totalTrades: filteredTrades.length,
			totalPnl: filteredTrades.reduce((sum, t) => sum + t.pnl, 0),
			winRate: filteredTrades.length > 0 ? (wins.length / filteredTrades.length) * 100 : 0,
			avgWin: wins.length > 0 ? wins.reduce((sum, t) => sum + t.pnl, 0) / wins.length : 0,
			avgLoss: losses.length > 0 ? Math.abs(losses.reduce((sum, t) => sum + t.pnl, 0) / losses.length) : 0,
			profitFactor: losses.length > 0 ? 
				wins.reduce((sum, t) => sum + t.pnl, 0) / Math.abs(losses.reduce((sum, t) => sum + t.pnl, 0)) : 0
		};
	}
	
	let currentFilters: TradeFilters = {};
	
	function handleFilter(event: CustomEvent<TradeFilters>) {
		currentFilters = event.detail;
		applyFilters();
	}
	
	function applyFilters() {
		filteredTrades = trades.filter(trade => {
			// Search filter (searches across symbol, strategy, notes)
			if (currentFilters.search) {
				const search = currentFilters.search.toLowerCase();
				const matchesSearch = 
					trade.symbol.toLowerCase().includes(search) ||
					(trade.strategy?.toLowerCase().includes(search) || false) ||
					(trade.notes?.toLowerCase().includes(search) || false);
				if (!matchesSearch) return false;
			}
			
			// Other filters
			if (currentFilters.symbol && !trade.symbol.includes(currentFilters.symbol)) return false;
			if (currentFilters.side && trade.side !== currentFilters.side) return false;
			if (currentFilters.strategy && trade.strategy !== currentFilters.strategy) return false;
			
			// Date filters
			if (currentFilters.date_from && new Date(trade.entryDate) < new Date(currentFilters.date_from)) return false;
			if (currentFilters.date_to && new Date(trade.entryDate) > new Date(currentFilters.date_to)) return false;
			
			// P&L filters
			if (currentFilters.min_pnl !== undefined && trade.pnl < currentFilters.min_pnl) return false;
			if (currentFilters.max_pnl !== undefined && trade.pnl > currentFilters.max_pnl) return false;
			
			// Quantity filters
			if (currentFilters.min_quantity !== undefined && trade.quantity < currentFilters.min_quantity) return false;
			if (currentFilters.max_quantity !== undefined && trade.quantity > currentFilters.max_quantity) return false;
			
			return true;
		});
		
		calculateStats();
	}
	
	async function fetchTrades() {
		try {
			loading = true;
			error = '';
			
			// Check if authenticated
			if (!get(isAuthenticated)) {
				goto('/login');
				return;
			}
			
			// Fetch trades and usage data
			const [apiTrades, usageData, subscription] = await Promise.all([
				tradesApi.getTrades(),
				billingApi.getUsage(),
				billingApi.getSubscription()
			]);
			
			usage = usageData;
			
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
			
		} catch (err: any) {
			console.error('Failed to fetch trades:', err);
			
			if (err.status === 401) {
				goto('/login');
			} else {
				// Use sample data as fallback
				useSampleData();
				error = 'Failed to load trades. Using sample data.';
			}
		} finally {
			loading = false;
		}
	}
	
	// Bulk operations
	async function handleBulkDelete() {
		const selectedIds = selection.getSelectedIds();
		if (selectedIds.length === 0) return;
		
		try {
			loading = true;
			await tradesApi.bulkDelete(selectedIds);
			await fetchTrades();
			selection.deselectAll();
		} catch (err: any) {
			error = err.message || 'Failed to delete trades';
		} finally {
			loading = false;
		}
	}
	
	function handleBulkExport() {
		const selectedTrades = selection.getSelectedItems();
		if (selectedTrades.length === 0) return;
		
		showExportDialog = true;
	}
	
	async function handleBulkEdit(event: CustomEvent<{ updates: any }>) {
		const selectedIds = selection.getSelectedIds();
		if (selectedIds.length === 0) return;
		
		try {
			loading = true;
			// In a real app, we'd have a bulk update endpoint
			for (const id of selectedIds) {
				await tradesApi.updateTrade(id, event.detail.updates);
			}
			await fetchTrades();
			selection.deselectAll();
		} catch (err: any) {
			error = err.message || 'Failed to update trades';
		} finally {
			loading = false;
		}
	}
	
	async function handleBulkTag(event: CustomEvent<{ tag: string }>) {
		const selectedIds = selection.getSelectedIds();
		if (selectedIds.length === 0) return;
		
		try {
			loading = true;
			const tag = event.detail.tag;
			
			// Update each selected trade with the new tag
			for (const id of selectedIds) {
				const trade = trades.find(t => t.id === id);
				if (trade) {
					const currentNotes = trade.notes || '';
					const newNotes = currentNotes ? `${currentNotes} #${tag}` : `#${tag}`;
					await tradesApi.updateTrade(id, { notes: newNotes });
				}
			}
			
			await fetchTrades();
			selection.deselectAll();
		} catch (err: any) {
			error = err.message || 'Failed to tag trades';
		} finally {
			loading = false;
		}
	}
	
	function useSampleData() {
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
				exitDate: '2024-01-14 14:45',
				strategy: 'Momentum',
				notes: 'Strong breakout pattern'
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
				exitDate: '2024-01-14 15:30',
				strategy: 'Mean Reversion',
				notes: 'Stop loss hit'
			},
			{
				id: 3,
				symbol: 'NVDA',
				side: 'long' as const,
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
				side: 'long' as const,
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
				side: 'short' as const,
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
	}
	
	// Handle selection changes
	function handleToggleSelect(event: CustomEvent<{ id: number }>) {
		const trade = trades.find(t => t.id === event.detail.id);
		if (trade) {
			selection.toggle(trade);
		}
	}
	
	function handleSelectAll() {
		selection.selectAll();
	}
	
	function handleDeselectAll() {
		selection.deselectAll();
	}
	
	// Subscribe to real-time trade updates
	$: if ($tradeUpdates) {
		handleRealtimeUpdate($tradeUpdates);
	}
	
	function handleRealtimeUpdate(update: any) {
		console.log('Received real-time update:', update);
		
		if (update.action === 'create') {
			// Add new trade
			const newTrade = {
				id: update.trade.id,
				symbol: update.trade.symbol,
				side: update.trade.side,
				entryPrice: update.trade.entry_price,
				exitPrice: update.trade.exit_price,
				quantity: update.trade.quantity,
				pnl: update.trade.pnl || 0,
				entryDate: update.trade.entry_date,
				exitDate: update.trade.exit_date,
				strategy: update.trade.strategy,
				notes: update.trade.notes
			};
			trades = [newTrade, ...trades];
			tradeStore.setTrades(trades);
		} else if (update.action === 'update') {
			// Update existing trade
			trades = trades.map(t => {
				if (t.id === update.trade.id) {
					return {
						...t,
						symbol: update.trade.symbol,
						side: update.trade.side,
						entryPrice: update.trade.entry_price,
						exitPrice: update.trade.exit_price,
						quantity: update.trade.quantity,
						pnl: update.trade.pnl || 0,
						entryDate: update.trade.entry_date,
						exitDate: update.trade.exit_date,
						strategy: update.trade.strategy,
						notes: update.trade.notes
					};
				}
				return t;
			});
			tradeStore.setTrades(trades);
		} else if (update.action === 'delete') {
			// Remove deleted trade
			trades = trades.filter(t => t.id !== update.trade_id);
			tradeStore.setTrades(trades);
		}
		
		applyFilters();
		calculateStats();
	}
	
	onMount(() => {
		fetchTrades();
	});
</script>

<svelte:head>
	<title>Trade Log - TradeSense</title>
</svelte:head>

<div class="trade-log">
	<header class="page-header">
		<div>
			<h1>Trade Log</h1>
			<p>Track and analyze all your trades</p>
		</div>
		<div class="actions">
			<button on:click={handleAddTrade} class="primary">Add Trade</button>
			<button on:click={() => showExportDialog = true}>Export</button>
		</div>
	</header>
	
	{#if loading}
		<div class="loading">Loading trades...</div>
	{:else}
		{#if error}
			<div class="error">{error}</div>
		{/if}
		
		<!-- Usage Limiter -->
		{#if usage}
			<UsageLimiter 
				current={usage.trades_count} 
				limit={usage.trades_limit} 
				type="trades"
				on:upgrade={() => goto('/pricing')}
			/>
		{/if}
		
		<!-- Statistics Overview -->
		<TradeStats {stats} />
		
		<!-- Advanced Filters -->
		<TradeFiltersAdvanced on:filter={handleFilter} />
		
		<!-- Bulk Actions -->
		<BulkActions
			selectedCount={$selection.selectionState.count}
			totalCount={filteredTrades.length}
			isAllSelected={$selection.selectionState.isAllSelected}
			isPartiallySelected={$selection.selectionState.isPartiallySelected}
			on:selectAll={handleSelectAll}
			on:deselectAll={handleDeselectAll}
			on:bulkDelete={handleBulkDelete}
			on:bulkExport={handleBulkExport}
			on:bulkEdit={handleBulkEdit}
			on:bulkTag={handleBulkTag}
		/>
		
		<!-- Trade List -->
		<div class="card">
			<div class="card-header">
				<h2>All Trades ({filteredTrades.length})</h2>
			</div>
			<TradeListWithSelection 
				trades={filteredTrades}
				selectedIds={$selection.selectedIds}
				on:edit={handleEditTrade}
				on:delete={handleDeleteTrade}
				on:toggleSelect={handleToggleSelect}
				on:selectAll={handleSelectAll}
				on:deselectAll={handleDeselectAll}
			/>
		</div>
	{/if}
	
	<!-- Trade Form Modal -->
	<TradeForm 
		trade={selectedTrade} 
		show={showTradeForm} 
		on:save={handleSaveTrade}
		on:close={() => showTradeForm = false}
	/>
	
	<!-- Export Dialog -->
	<ExportDialog
		bind:show={showExportDialog}
		trades={$selection.selectionState.hasSelection ? $selection.selectedItems : trades}
		{filteredTrades}
		on:export={(e) => console.log('Exported', e.detail)}
	/>
</div>

<style>
	.trade-log {
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
	
	.actions {
		display: flex;
		gap: 1rem;
	}
	
	.primary {
		background: #10b981;
	}
	
	.primary:hover {
		background: #059669;
	}
	
	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}
	
	.card-header h2 {
		font-size: 1.25rem;
		color: #333;
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
	
	@media (max-width: 768px) {
		.trade-log {
			padding: 0 1rem 4rem;
		}
		
		.page-header {
			flex-direction: column;
			align-items: stretch;
		}
		
		.actions {
			flex-direction: column;
		}
		
		.actions button {
			width: 100%;
		}
	}
</style>