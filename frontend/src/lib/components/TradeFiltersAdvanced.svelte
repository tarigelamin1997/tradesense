<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Search, Filter, X, ChevronDown, ChevronUp, Save, Trash2 } from 'lucide-svelte';
	import type { TradeFilters } from '$lib/api/trades';
	
	const dispatch = createEventDispatcher();
	
	// Filter values
	let searchQuery = '';
	let symbol = '';
	let side = '';
	let strategy = '';
	let dateFrom = '';
	let dateTo = '';
	let minPnl = '';
	let maxPnl = '';
	let minQuantity = '';
	let maxQuantity = '';
	let showAdvanced = false;
	
	// Quick filter presets
	let activeQuickFilter = '';
	const quickFilters = [
		{ id: 'today', label: 'Today', action: () => setDateRange('today') },
		{ id: 'week', label: 'This Week', action: () => setDateRange('week') },
		{ id: 'month', label: 'This Month', action: () => setDateRange('month') },
		{ id: 'winners', label: 'Winners', action: () => setPnlFilter('winners') },
		{ id: 'losers', label: 'Losers', action: () => setPnlFilter('losers') },
		{ id: 'longs', label: 'Longs', action: () => { side = 'long'; handleFilter(); } },
		{ id: 'shorts', label: 'Shorts', action: () => { side = 'short'; handleFilter(); } }
	];
	
	// Saved filter presets
	let savedPresets: Array<{ name: string; filters: any }> = [];
	let showSavePreset = false;
	let presetName = '';
	
	// Common strategies (should match the trade form)
	const strategies = [
		'Momentum',
		'Mean Reversion',
		'Breakout',
		'Scalping',
		'Swing Trading',
		'Position Trading',
		'Day Trading',
		'News Trading',
		'Pairs Trading'
	];
	
	// Initialize saved presets from localStorage
	if (typeof window !== 'undefined') {
		const saved = localStorage.getItem('tradeFilterPresets');
		if (saved) {
			savedPresets = JSON.parse(saved);
		}
	}
	
	// Debounce timer for search
	let debounceTimer: NodeJS.Timeout;
	
	function handleSearch() {
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => {
			handleFilter();
		}, 300);
	}
	
	function handleFilter() {
		const filters: TradeFilters = {};
		
		// Add non-empty filters
		if (searchQuery) filters.search = searchQuery;
		if (symbol) filters.symbol = symbol.toUpperCase();
		if (side) filters.side = side as 'long' | 'short';
		if (strategy) filters.strategy = strategy;
		if (dateFrom) filters.date_from = dateFrom;
		if (dateTo) filters.date_to = dateTo;
		if (minPnl) filters.min_pnl = parseFloat(minPnl);
		if (maxPnl) filters.max_pnl = parseFloat(maxPnl);
		if (minQuantity) filters.min_quantity = parseFloat(minQuantity);
		if (maxQuantity) filters.max_quantity = parseFloat(maxQuantity);
		
		dispatch('filter', filters);
	}
	
	function setDateRange(range: string) {
		const now = new Date();
		const today = now.toISOString().split('T')[0];
		
		activeQuickFilter = range;
		
		switch (range) {
			case 'today':
				dateFrom = today;
				dateTo = today;
				break;
			case 'week':
				const weekAgo = new Date(now);
				weekAgo.setDate(now.getDate() - 7);
				dateFrom = weekAgo.toISOString().split('T')[0];
				dateTo = today;
				break;
			case 'month':
				const monthAgo = new Date(now);
				monthAgo.setMonth(now.getMonth() - 1);
				dateFrom = monthAgo.toISOString().split('T')[0];
				dateTo = today;
				break;
		}
		
		handleFilter();
	}
	
	function setPnlFilter(type: string) {
		activeQuickFilter = type;
		
		if (type === 'winners') {
			minPnl = '0.01';
			maxPnl = '';
		} else if (type === 'losers') {
			minPnl = '';
			maxPnl = '-0.01';
		}
		
		handleFilter();
	}
	
	function resetFilters() {
		searchQuery = '';
		symbol = '';
		side = '';
		strategy = '';
		dateFrom = '';
		dateTo = '';
		minPnl = '';
		maxPnl = '';
		minQuantity = '';
		maxQuantity = '';
		activeQuickFilter = '';
		handleFilter();
	}
	
	function savePreset() {
		if (!presetName.trim()) return;
		
		const preset = {
			name: presetName,
			filters: {
				searchQuery,
				symbol,
				side,
				strategy,
				dateFrom,
				dateTo,
				minPnl,
				maxPnl,
				minQuantity,
				maxQuantity
			}
		};
		
		savedPresets = [...savedPresets, preset];
		localStorage.setItem('tradeFilterPresets', JSON.stringify(savedPresets));
		
		presetName = '';
		showSavePreset = false;
	}
	
	function loadPreset(preset: any) {
		searchQuery = preset.filters.searchQuery || '';
		symbol = preset.filters.symbol || '';
		side = preset.filters.side || '';
		strategy = preset.filters.strategy || '';
		dateFrom = preset.filters.dateFrom || '';
		dateTo = preset.filters.dateTo || '';
		minPnl = preset.filters.minPnl || '';
		maxPnl = preset.filters.maxPnl || '';
		minQuantity = preset.filters.minQuantity || '';
		maxQuantity = preset.filters.maxQuantity || '';
		
		handleFilter();
	}
	
	function deletePreset(index: number) {
		savedPresets = savedPresets.filter((_, i) => i !== index);
		localStorage.setItem('tradeFilterPresets', JSON.stringify(savedPresets));
	}
	
	// Count active filters
	$: activeFilterCount = [
		searchQuery,
		symbol,
		side,
		strategy,
		dateFrom,
		dateTo,
		minPnl,
		maxPnl,
		minQuantity,
		maxQuantity
	].filter(Boolean).length;
</script>

<div class="filters-container">
	<!-- Search Bar -->
	<div class="search-bar">
		<Search size={20} class="search-icon" />
		<input
			type="text"
			placeholder="Search trades..."
			bind:value={searchQuery}
			on:input={handleSearch}
			class="search-input"
		/>
		{#if activeFilterCount > 0}
			<div class="filter-count">{activeFilterCount}</div>
		{/if}
		<button
			type="button"
			class="toggle-filters"
			on:click={() => showAdvanced = !showAdvanced}
		>
			<Filter size={16} />
			{showAdvanced ? 'Hide' : 'Show'} Filters
			{#if showAdvanced}
				<ChevronUp size={16} />
			{:else}
				<ChevronDown size={16} />
			{/if}
		</button>
	</div>
	
	<!-- Quick Filters -->
	<div class="quick-filters">
		{#each quickFilters as filter}
			<button
				type="button"
				class="quick-filter {activeQuickFilter === filter.id ? 'active' : ''}"
				on:click={filter.action}
			>
				{filter.label}
			</button>
		{/each}
		
		{#if savedPresets.length > 0}
			<div class="preset-separator"></div>
			{#each savedPresets as preset, index}
				<div class="preset-filter">
					<button
						type="button"
						class="quick-filter"
						on:click={() => loadPreset(preset)}
					>
						{preset.name}
					</button>
					<button
						type="button"
						class="delete-preset"
						on:click={() => deletePreset(index)}
						title="Delete preset"
					>
						<X size={14} />
					</button>
				</div>
			{/each}
		{/if}
	</div>
	
	<!-- Advanced Filters -->
	{#if showAdvanced}
		<div class="advanced-filters card">
			<div class="filter-grid">
				<!-- Basic Filters -->
				<div class="filter-group">
					<label for="symbol">Symbol</label>
					<input
						id="symbol"
						type="text"
						bind:value={symbol}
						on:input={handleFilter}
						placeholder="AAPL"
						class="uppercase"
					/>
				</div>
				
				<div class="filter-group">
					<label for="side">Side</label>
					<select id="side" bind:value={side} on:change={handleFilter}>
						<option value="">All</option>
						<option value="long">Long</option>
						<option value="short">Short</option>
					</select>
				</div>
				
				<div class="filter-group">
					<label for="strategy">Strategy</label>
					<select id="strategy" bind:value={strategy} on:change={handleFilter}>
						<option value="">All Strategies</option>
						{#each strategies as strat}
							<option value={strat}>{strat}</option>
						{/each}
					</select>
				</div>
				
				<!-- Date Range -->
				<div class="filter-group">
					<label for="dateFrom">From Date</label>
					<input
						id="dateFrom"
						type="date"
						bind:value={dateFrom}
						on:change={handleFilter}
					/>
				</div>
				
				<div class="filter-group">
					<label for="dateTo">To Date</label>
					<input
						id="dateTo"
						type="date"
						bind:value={dateTo}
						on:change={handleFilter}
					/>
				</div>
				
				<!-- P&L Range -->
				<div class="filter-group">
					<label for="minPnl">Min P&L</label>
					<input
						id="minPnl"
						type="number"
						bind:value={minPnl}
						on:input={handleFilter}
						placeholder="-100"
						step="0.01"
					/>
				</div>
				
				<div class="filter-group">
					<label for="maxPnl">Max P&L</label>
					<input
						id="maxPnl"
						type="number"
						bind:value={maxPnl}
						on:input={handleFilter}
						placeholder="1000"
						step="0.01"
					/>
				</div>
				
				<!-- Quantity Range -->
				<div class="filter-group">
					<label for="minQuantity">Min Quantity</label>
					<input
						id="minQuantity"
						type="number"
						bind:value={minQuantity}
						on:input={handleFilter}
						placeholder="1"
						min="0"
					/>
				</div>
				
				<div class="filter-group">
					<label for="maxQuantity">Max Quantity</label>
					<input
						id="maxQuantity"
						type="number"
						bind:value={maxQuantity}
						on:input={handleFilter}
						placeholder="1000"
						min="0"
					/>
				</div>
			</div>
			
			<!-- Filter Actions -->
			<div class="filter-actions">
				<button type="button" class="reset-button" on:click={resetFilters}>
					<X size={16} />
					Reset All
				</button>
				
				{#if !showSavePreset}
					<button 
						type="button" 
						class="save-preset-button"
						on:click={() => showSavePreset = true}
						disabled={activeFilterCount === 0}
					>
						<Save size={16} />
						Save Preset
					</button>
				{:else}
					<div class="save-preset-form">
						<input
							type="text"
							bind:value={presetName}
							placeholder="Preset name..."
							on:keypress={(e) => e.key === 'Enter' && savePreset()}
						/>
						<button type="button" on:click={savePreset} disabled={!presetName.trim()}>
							Save
						</button>
						<button type="button" on:click={() => showSavePreset = false}>
							Cancel
						</button>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.filters-container {
		margin-bottom: 2rem;
	}
	
	.search-bar {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		margin-bottom: 1rem;
	}
	
	:global(.search-icon) {
		color: #999;
		flex-shrink: 0;
	}
	
	.search-input {
		flex: 1;
		border: none;
		outline: none;
		font-size: 1rem;
		background: none;
	}
	
	.filter-count {
		background: #10b981;
		color: white;
		padding: 0.25rem 0.5rem;
		border-radius: 12px;
		font-size: 0.75rem;
		font-weight: 600;
	}
	
	.toggle-filters {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: #f3f4f6;
		border: none;
		border-radius: 6px;
		font-size: 0.875rem;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.toggle-filters:hover {
		background: #e5e7eb;
		color: #333;
	}
	
	.quick-filters {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
		margin-bottom: 1rem;
		align-items: center;
	}
	
	.quick-filter {
		padding: 0.5rem 1rem;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 20px;
		font-size: 0.875rem;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
		white-space: nowrap;
	}
	
	.quick-filter:hover {
		border-color: #10b981;
		color: #10b981;
	}
	
	.quick-filter.active {
		background: #10b981;
		border-color: #10b981;
		color: white;
	}
	
	.preset-separator {
		width: 1px;
		height: 20px;
		background: #e0e0e0;
		margin: 0 0.5rem;
	}
	
	.preset-filter {
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}
	
	.delete-preset {
		padding: 0.25rem;
		background: none;
		border: none;
		color: #999;
		cursor: pointer;
		border-radius: 4px;
		display: flex;
		align-items: center;
		transition: all 0.2s;
	}
	
	.delete-preset:hover {
		background: #fee;
		color: #c00;
	}
	
	.advanced-filters {
		padding: 1.5rem;
		margin-top: 1rem;
		animation: slideDown 0.3s ease-out;
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
	
	.filter-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 1rem;
		margin-bottom: 1.5rem;
	}
	
	.filter-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.filter-group label {
		font-size: 0.875rem;
		font-weight: 500;
		color: #333;
	}
	
	.filter-group input,
	.filter-group select {
		padding: 0.625rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 0.875rem;
		background: white;
		transition: border-color 0.2s;
	}
	
	.filter-group input:focus,
	.filter-group select:focus {
		outline: none;
		border-color: #10b981;
	}
	
	.uppercase {
		text-transform: uppercase;
	}
	
	.filter-actions {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-top: 1rem;
		border-top: 1px solid #e0e0e0;
	}
	
	.reset-button {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: #f3f4f6;
		border: none;
		border-radius: 6px;
		font-size: 0.875rem;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.reset-button:hover {
		background: #e5e7eb;
		color: #333;
	}
	
	.save-preset-button {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: #10b981;
		border: none;
		border-radius: 6px;
		font-size: 0.875rem;
		color: white;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.save-preset-button:hover:not(:disabled) {
		background: #059669;
	}
	
	.save-preset-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	.save-preset-form {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}
	
	.save-preset-form input {
		padding: 0.5rem 1rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 0.875rem;
		min-width: 150px;
	}
	
	.save-preset-form button {
		padding: 0.5rem 1rem;
		border: none;
		border-radius: 6px;
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.save-preset-form button:first-of-type {
		background: #10b981;
		color: white;
	}
	
	.save-preset-form button:first-of-type:hover:not(:disabled) {
		background: #059669;
	}
	
	.save-preset-form button:first-of-type:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	.save-preset-form button:last-of-type {
		background: #f3f4f6;
		color: #666;
	}
	
	.save-preset-form button:last-of-type:hover {
		background: #e5e7eb;
	}
	
	@media (max-width: 768px) {
		.search-bar {
			flex-wrap: wrap;
		}
		
		.search-input {
			width: 100%;
			order: 2;
			margin-top: 0.5rem;
		}
		
		.filter-grid {
			grid-template-columns: 1fr;
		}
	}
</style>