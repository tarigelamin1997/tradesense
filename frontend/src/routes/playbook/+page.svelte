<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$lib/api/auth.js';
	import { get } from 'svelte/store';
	import { FileText, Plus, Edit, Trash2, Copy, Search, Filter, Tag } from 'lucide-svelte';
	import PlaybookForm from '$lib/components/playbook/PlaybookForm.svelte';
	import PlaybookDetail from '$lib/components/playbook/PlaybookDetail.svelte';
	import { logger } from '$lib/utils/logger';
	
	interface PlaybookEntry {
		id: number;
		title: string;
		strategy_type: 'scalping' | 'swing' | 'daytrading' | 'position' | 'other';
		timeframe: string;
		market_conditions: string;
		entry_rules: string[];
		exit_rules: string[];
		risk_management: string;
		position_sizing: string;
		indicators: string[];
		notes: string;
		backtest_results?: {
			win_rate: number;
			profit_factor: number;
			avg_win: number;
			avg_loss: number;
			max_drawdown: number;
		};
		tags: string[];
		created_at: string;
		updated_at: string;
		is_active: boolean;
	}
	
	let loading = true;
	let error = '';
	let playbooks: PlaybookEntry[] = [];
	let filteredPlaybooks: PlaybookEntry[] = [];
	let selectedPlaybook: PlaybookEntry | null = null;
	let showForm = false;
	let editingPlaybook: PlaybookEntry | null = null;
	
	// Filters
	let searchQuery = '';
	let selectedStrategy = '';
	let activeOnly = false;
	
	async function fetchPlaybooks() {
		try {
			loading = true;
			error = '';
			
			// Check if authenticated
			if (!get(isAuthenticated)) {
				goto('/login');
				return;
			}
			
			// For now, use sample data
			playbooks = generateSamplePlaybooks();
			applyFilters();
			
		} catch (err: any) {
			logger.error('Failed to fetch playbooks:', err);
			error = 'Failed to load playbooks.';
			playbooks = generateSamplePlaybooks();
			applyFilters();
		} finally {
			loading = false;
		}
	}
	
	function generateSamplePlaybooks(): PlaybookEntry[] {
		return [
			{
				id: 1,
				title: 'Morning Gap Strategy',
				strategy_type: 'daytrading',
				timeframe: '5min, 15min',
				market_conditions: 'High volatility, strong pre-market activity, gap > 2%',
				entry_rules: [
					'Wait for first 15 minutes to establish range',
					'Enter on break of opening range with volume',
					'Confirm with VWAP direction',
					'RSI should be > 60 for longs, < 40 for shorts'
				],
				exit_rules: [
					'Initial stop: Previous candle low/high',
					'Target 1: 1.5x risk at 50% position',
					'Target 2: 2.5x risk at 30% position',
					'Trail stop on remaining 20%'
				],
				risk_management: '1% account risk per trade, max 3 concurrent positions',
				position_sizing: 'Risk / (Entry - Stop Loss) = Share size',
				indicators: ['VWAP', 'RSI', 'Volume', 'ATR'],
				notes: 'Best performance on large-cap stocks with news catalysts. Avoid on Fed days.',
				backtest_results: {
					win_rate: 68.5,
					profit_factor: 2.3,
					avg_win: 285,
					avg_loss: 124,
					max_drawdown: 8.5
				},
				tags: ['gaps', 'momentum', 'morning'],
				created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
				updated_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
				is_active: true
			},
			{
				id: 2,
				title: 'Mean Reversion Swing Trade',
				strategy_type: 'swing',
				timeframe: 'Daily, 4H',
				market_conditions: 'Ranging market, low volatility, established support/resistance',
				entry_rules: [
					'Price at key support/resistance level',
					'RSI oversold (<30) or overbought (>70)',
					'Bullish/bearish divergence on indicators',
					'Volume spike on reversal candle'
				],
				exit_rules: [
					'Stop loss: Beyond support/resistance level',
					'Target: Previous swing high/low',
					'Time stop: Exit after 5 days if no movement',
					'Exit on momentum exhaustion'
				],
				risk_management: '2% account risk per trade, max 5 swing positions',
				position_sizing: 'Kelly Criterion with 25% reduction for safety',
				indicators: ['RSI', 'MACD', 'Bollinger Bands', 'Support/Resistance'],
				notes: 'Works best in established ranges. Avoid in trending markets.',
				backtest_results: {
					win_rate: 72.3,
					profit_factor: 1.8,
					avg_win: 425,
					avg_loss: 236,
					max_drawdown: 12.3
				},
				tags: ['mean-reversion', 'swing', 'range-bound'],
				created_at: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
				updated_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
				is_active: true
			},
			{
				id: 3,
				title: 'Scalping the Open',
				strategy_type: 'scalping',
				timeframe: '1min, 3min',
				market_conditions: 'First 30 minutes of market open, high liquidity stocks',
				entry_rules: [
					'Trade only liquid stocks (>5M volume)',
					'Enter on momentum with tape reading',
					'Use Level 2 for entry timing',
					'Quick in and out, no holding'
				],
				exit_rules: [
					'Fixed stop: $0.10 or 10 cents',
					'Target: $0.15-0.20 or 15-20 cents',
					'Time stop: Exit after 5 minutes',
					'Exit on momentum shift'
				],
				risk_management: '0.5% account risk per trade, max 2 positions at once',
				position_sizing: 'Fixed 1000 shares for consistency',
				indicators: ['Level 2', 'Time & Sales', 'VWAP'],
				notes: 'Requires fast execution and low commissions. Mental discipline crucial.',
				tags: ['scalping', 'open', 'high-frequency'],
				created_at: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
				updated_at: new Date(Date.now() - 45 * 24 * 60 * 60 * 1000).toISOString(),
				is_active: false
			}
		];
	}
	
	function applyFilters() {
		filteredPlaybooks = playbooks.filter(playbook => {
			// Search filter
			if (searchQuery) {
				const query = searchQuery.toLowerCase();
				const matchesSearch = 
					playbook.title.toLowerCase().includes(query) ||
					playbook.notes.toLowerCase().includes(query) ||
					playbook.tags.some(tag => tag.toLowerCase().includes(query)) ||
					playbook.indicators.some(ind => ind.toLowerCase().includes(query));
				if (!matchesSearch) return false;
			}
			
			// Strategy filter
			if (selectedStrategy && playbook.strategy_type !== selectedStrategy) {
				return false;
			}
			
			// Active filter
			if (activeOnly && !playbook.is_active) {
				return false;
			}
			
			return true;
		});
		
		// Sort by updated date (newest first)
		filteredPlaybooks.sort((a, b) => 
			new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
		);
	}
	
	function handleNewPlaybook() {
		showForm = true;
		editingPlaybook = null;
	}
	
	function handleEditPlaybook(playbook: PlaybookEntry) {
		editingPlaybook = playbook;
		showForm = true;
	}
	
	function handleClonePlaybook(playbook: PlaybookEntry) {
		const cloned = {
			...playbook,
			id: Date.now(),
			title: `${playbook.title} (Copy)`,
			created_at: new Date().toISOString(),
			updated_at: new Date().toISOString()
		};
		
		playbooks = [cloned, ...playbooks];
		applyFilters();
	}
	
	function handleDeletePlaybook(id: number) {
		if (!confirm('Are you sure you want to delete this playbook?')) return;
		
		playbooks = playbooks.filter(p => p.id !== id);
		applyFilters();
		
		if (selectedPlaybook?.id === id) {
			selectedPlaybook = null;
		}
	}
	
	function handleSavePlaybook(event: CustomEvent<{ playbook: PlaybookEntry }>) {
		const { playbook } = event.detail;
		
		if (editingPlaybook) {
			// Update existing
			playbooks = playbooks.map(p => 
				p.id === editingPlaybook.id ? { ...playbook, id: editingPlaybook.id } : p
			);
		} else {
			// Create new
			const newPlaybook = {
				...playbook,
				id: Date.now(),
				created_at: new Date().toISOString(),
				updated_at: new Date().toISOString()
			};
			playbooks = [newPlaybook, ...playbooks];
		}
		
		applyFilters();
		showForm = false;
		editingPlaybook = null;
	}
	
	function handleToggleActive(playbook: PlaybookEntry) {
		playbooks = playbooks.map(p => 
			p.id === playbook.id ? { ...p, is_active: !p.is_active } : p
		);
		applyFilters();
	}
	
	function formatDate(dateString: string) {
		const date = new Date(dateString);
		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}
	
	// Update filters when search or filter values change
	$: if (searchQuery !== undefined || selectedStrategy !== undefined || activeOnly !== undefined) {
		applyFilters();
	}
	
	onMount(() => {
		fetchPlaybooks();
	});
</script>

<svelte:head>
	<title>Playbook - TradeSense</title>
</svelte:head>

<div class="playbook-page">
	<header class="page-header">
		<div>
			<h1>Trading Playbook</h1>
			<p>Document and refine your trading strategies</p>
		</div>
		<button on:click={handleNewPlaybook} class="new-button">
			<Plus size={18} />
			New Strategy
		</button>
	</header>
	
	{#if loading}
		<div class="loading">Loading playbook...</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else if showForm}
		<PlaybookForm
			playbook={editingPlaybook}
			on:save={handleSavePlaybook}
			on:cancel={() => {
				showForm = false;
				editingPlaybook = null;
			}}
		/>
	{:else}
		<!-- Filters -->
		<div class="filters-section">
			<div class="search-container">
				<Search size={20} class="search-icon" />
				<input
					type="text"
					placeholder="Search strategies..."
					bind:value={searchQuery}
					class="search-input"
				/>
			</div>
			
			<div class="filter-buttons">
				<select bind:value={selectedStrategy} class="filter-select">
					<option value="">All Strategies</option>
					<option value="scalping">Scalping</option>
					<option value="daytrading">Day Trading</option>
					<option value="swing">Swing Trading</option>
					<option value="position">Position Trading</option>
					<option value="other">Other</option>
				</select>
				
				<label class="checkbox-label">
					<input
						type="checkbox"
						bind:checked={activeOnly}
					/>
					Active Only
				</label>
			</div>
		</div>
		
		{#if filteredPlaybooks.length === 0}
			<div class="empty-state">
				<FileText size={48} />
				<h2>No strategies found</h2>
				<p>
					{searchQuery || selectedStrategy || activeOnly 
						? 'Try adjusting your filters' 
						: 'Create your first trading strategy'}
				</p>
				{#if !searchQuery && !selectedStrategy && !activeOnly}
					<button on:click={handleNewPlaybook} class="primary-button">
						Create Strategy
					</button>
				{/if}
			</div>
		{:else}
			<div class="playbook-layout">
				<div class="playbook-list">
					{#each filteredPlaybooks as playbook}
						<button 
							class="playbook-card card"
							class:selected={selectedPlaybook?.id === playbook.id}
							class:inactive={!playbook.is_active}
							on:click={() => selectedPlaybook = playbook}
							type="button"
						>
							<div class="playbook-header">
								<div>
									<h3>{playbook.title}</h3>
									<div class="playbook-meta">
										<span class="strategy-type">{playbook.strategy_type}</span>
										<span class="timeframe">{playbook.timeframe}</span>
										{#if playbook.backtest_results}
											<span class="win-rate">WR: {playbook.backtest_results.win_rate}%</span>
										{/if}
									</div>
								</div>
								<div class="playbook-status">
									<button
										class="status-toggle"
										class:active={playbook.is_active}
										on:click|stopPropagation={() => handleToggleActive(playbook)}
										title={playbook.is_active ? 'Active' : 'Inactive'}
									>
										{playbook.is_active ? '✓' : '○'}
									</button>
								</div>
							</div>
							
							<p class="playbook-conditions">{playbook.market_conditions}</p>
							
							{#if playbook.tags.length > 0}
								<div class="tags">
									{#each playbook.tags as tag}
										<span class="tag">{tag}</span>
									{/each}
								</div>
							{/if}
							
							<div class="playbook-footer">
								<span class="date">Updated {formatDate(playbook.updated_at)}</span>
								<div class="playbook-actions">
									<button
										class="icon-button"
										on:click|stopPropagation={() => handleEditPlaybook(playbook)}
										title="Edit"
									>
										<Edit size={16} />
									</button>
									<button
										class="icon-button"
										on:click|stopPropagation={() => handleClonePlaybook(playbook)}
										title="Clone"
									>
										<Copy size={16} />
									</button>
									<button
										class="icon-button danger"
										on:click|stopPropagation={() => handleDeletePlaybook(playbook.id)}
										title="Delete"
									>
										<Trash2 size={16} />
									</button>
								</div>
							</div>
						</button>
					{/each}
				</div>
				
				{#if selectedPlaybook}
					<PlaybookDetail
						playbook={selectedPlaybook}
						on:edit={() => handleEditPlaybook(selectedPlaybook)}
						on:clone={() => handleClonePlaybook(selectedPlaybook)}
						on:delete={() => handleDeletePlaybook(selectedPlaybook.id)}
					/>
				{/if}
			</div>
		{/if}
	{/if}
</div>

<style>
	.playbook-page {
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
	
	.new-button {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: #10b981;
		color: white;
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 1rem;
		transition: background 0.2s;
	}
	
	.new-button:hover {
		background: #059669;
	}
	
	.loading {
		text-align: center;
		padding: 4rem;
		color: #666;
	}
	
	.error {
		background: #fee;
		color: #c00;
		padding: 1rem;
		border-radius: 6px;
		margin-bottom: 1rem;
	}
	
	/* Filters */
	.filters-section {
		display: flex;
		gap: 1rem;
		margin-bottom: 2rem;
		flex-wrap: wrap;
	}
	
	.search-container {
		flex: 1;
		position: relative;
		min-width: 300px;
	}
	
	:global(.search-icon) {
		position: absolute;
		left: 1rem;
		top: 50%;
		transform: translateY(-50%);
		color: #666;
		pointer-events: none;
	}
	
	.search-input {
		width: 100%;
		padding: 0.75rem 1rem 0.75rem 3rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 1rem;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #10b981;
	}
	
	.filter-buttons {
		display: flex;
		gap: 1rem;
		align-items: center;
	}
	
	.filter-select {
		padding: 0.75rem 1rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		background: white;
		font-size: 0.875rem;
		cursor: pointer;
	}
	
	.filter-select:focus {
		outline: none;
		border-color: #10b981;
	}
	
	.checkbox-label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		color: #666;
		cursor: pointer;
	}
	
	/* Layout */
	.playbook-layout {
		display: grid;
		grid-template-columns: 400px 1fr;
		gap: 2rem;
		align-items: start;
	}
	
	.playbook-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		max-height: calc(100vh - 300px);
		overflow-y: auto;
		padding-right: 0.5rem;
	}
	
	.playbook-card {
		padding: 1.5rem;
		cursor: pointer;
		transition: all 0.2s;
		border: 2px solid transparent;
		width: 100%;
		text-align: left;
		background: transparent;
		font-family: inherit;
	}
	
	.playbook-card:hover {
		transform: translateX(4px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}
	
	.playbook-card.selected {
		border-color: #10b981;
		background: #f0fdf4;
	}
	
	.playbook-card.inactive {
		opacity: 0.7;
	}
	
	.playbook-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 0.75rem;
	}
	
	.playbook-header h3 {
		font-size: 1.125rem;
		margin-bottom: 0.25rem;
		color: #333;
	}
	
	.playbook-meta {
		display: flex;
		gap: 0.75rem;
		font-size: 0.75rem;
		color: #666;
	}
	
	.strategy-type {
		background: #e0f2fe;
		color: #0369a1;
		padding: 0.125rem 0.5rem;
		border-radius: 12px;
		text-transform: capitalize;
	}
	
	.timeframe {
		color: #666;
	}
	
	.win-rate {
		color: #10b981;
		font-weight: 500;
	}
	
	.playbook-status {
		display: flex;
		align-items: center;
	}
	
	.status-toggle {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		border: 2px solid #e0e0e0;
		background: white;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.875rem;
	}
	
	.status-toggle.active {
		border-color: #10b981;
		background: #10b981;
		color: white;
	}
	
	.playbook-conditions {
		font-size: 0.875rem;
		color: #666;
		margin-bottom: 0.75rem;
		line-height: 1.5;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	
	.tags {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
		margin-bottom: 0.75rem;
	}
	
	.tag {
		background: #f3f4f6;
		color: #666;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.75rem;
	}
	
	.playbook-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 0.75rem;
		padding-top: 0.75rem;
		border-top: 1px solid #e0e0e0;
	}
	
	.date {
		font-size: 0.75rem;
		color: #999;
	}
	
	.playbook-actions {
		display: flex;
		gap: 0.25rem;
	}
	
	.icon-button {
		padding: 0.375rem;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 4px;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.icon-button:hover {
		background: #f3f4f6;
		border-color: #d1d5db;
		color: #333;
	}
	
	.icon-button.danger:hover {
		background: #fef2f2;
		border-color: #fecaca;
		color: #ef4444;
	}
	
	/* Empty State */
	.empty-state {
		text-align: center;
		padding: 4rem 2rem;
		color: #666;
	}
	
	.empty-state h2 {
		font-size: 1.5rem;
		margin: 1rem 0;
	}
	
	.empty-state p {
		margin-bottom: 2rem;
	}
	
	.primary-button {
		background: #10b981;
		color: white;
		padding: 1rem 2rem;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 1.125rem;
		transition: all 0.2s;
	}
	
	.primary-button:hover {
		background: #059669;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
	}
	
	@media (max-width: 1024px) {
		.playbook-layout {
			grid-template-columns: 1fr;
		}
		
		.playbook-list {
			max-height: none;
		}
	}
	
	@media (max-width: 640px) {
		.playbook-page {
			padding: 0 1rem 4rem;
		}
		
		.filters-section {
			flex-direction: column;
		}
		
		.search-container {
			min-width: auto;
		}
		
		.filter-buttons {
			flex-wrap: wrap;
		}
	}
</style>