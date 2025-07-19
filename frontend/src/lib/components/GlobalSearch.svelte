<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { Search, X, TrendingUp, FileText, BarChart3, Calendar, Hash } from 'lucide-svelte';
	import { api } from '$lib/api/client';
	import { logger } from '$lib/utils/logger';
	
	let isOpen = false;
	let searchQuery = '';
	let searchResults: any = {
		trades: [],
		journal: [],
		analytics: []
	};
	let loading = false;
	let selectedIndex = -1;
	let searchTimeout: NodeJS.Timeout;
	let searchInput: HTMLInputElement;
	
	// Categories for filtering
	let activeCategory = 'all';
	const categories = [
		{ id: 'all', label: 'All', icon: Search },
		{ id: 'trades', label: 'Trades', icon: TrendingUp },
		{ id: 'journal', label: 'Journal', icon: FileText },
		{ id: 'analytics', label: 'Analytics', icon: BarChart3 }
	];
	
	// Keyboard shortcut to open search (Cmd/Ctrl + K)
	function handleKeydown(e: KeyboardEvent) {
		if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
			e.preventDefault();
			openSearch();
		}
		
		if (isOpen) {
			if (e.key === 'Escape') {
				closeSearch();
			} else if (e.key === 'ArrowDown') {
				e.preventDefault();
				navigateResults(1);
			} else if (e.key === 'ArrowUp') {
				e.preventDefault();
				navigateResults(-1);
			} else if (e.key === 'Enter' && selectedIndex >= 0) {
				e.preventDefault();
				selectResult(selectedIndex);
			}
		}
	}
	
	function openSearch() {
		isOpen = true;
		selectedIndex = -1;
		// Focus input after a brief delay to ensure it's rendered
		setTimeout(() => {
			searchInput?.focus();
		}, 50);
	}
	
	function closeSearch() {
		isOpen = false;
		searchQuery = '';
		searchResults = { trades: [], journal: [], analytics: [] };
		selectedIndex = -1;
	}
	
	function navigateResults(direction: number) {
		const allResults = getAllResults();
		if (allResults.length === 0) return;
		
		selectedIndex = selectedIndex + direction;
		if (selectedIndex < 0) selectedIndex = allResults.length - 1;
		if (selectedIndex >= allResults.length) selectedIndex = 0;
	}
	
	function getAllResults() {
		const results = [];
		
		if (activeCategory === 'all' || activeCategory === 'trades') {
			results.push(...searchResults.trades.map((t: any) => ({ ...t, type: 'trade' })));
		}
		if (activeCategory === 'all' || activeCategory === 'journal') {
			results.push(...searchResults.journal.map((j: any) => ({ ...j, type: 'journal' })));
		}
		if (activeCategory === 'all' || activeCategory === 'analytics') {
			results.push(...searchResults.analytics.map((a: any) => ({ ...a, type: 'analytics' })));
		}
		
		return results;
	}
	
	function selectResult(index: number) {
		const allResults = getAllResults();
		const result = allResults[index];
		
		if (!result) return;
		
		closeSearch();
		
		switch (result.type) {
			case 'trade':
				goto(`/trades/${result.id}`);
				break;
			case 'journal':
				goto(`/journal?entry=${result.id}`);
				break;
			case 'analytics':
				if (result.route) {
					goto(result.route);
				}
				break;
		}
	}
	
	async function performSearch() {
		if (!searchQuery.trim()) {
			searchResults = { trades: [], journal: [], analytics: [] };
			return;
		}
		
		loading = true;
		
		try {
			// Search trades
			if (activeCategory === 'all' || activeCategory === 'trades') {
				const trades = await api.get('/api/v1/trades', {
					params: { search: searchQuery, limit: 5 }
				});
				searchResults.trades = trades || [];
			}
			
			// Search journal entries
			if (activeCategory === 'all' || activeCategory === 'journal') {
				const journal = await api.get('/api/v1/journal/entries', {
					params: { search: searchQuery, limit: 5 }
				});
				searchResults.journal = journal || [];
			}
			
			// Search analytics pages (client-side)
			if (activeCategory === 'all' || activeCategory === 'analytics') {
				const analyticsPages = [
					{ id: 1, title: 'Performance Overview', route: '/analytics', keywords: ['performance', 'overview', 'pnl', 'profit', 'loss'] },
					{ id: 2, title: 'Risk Analysis', route: '/analytics/risk', keywords: ['risk', 'exposure', 'position', 'size'] },
					{ id: 3, title: 'Trade Statistics', route: '/analytics/statistics', keywords: ['statistics', 'stats', 'average', 'win', 'rate'] },
					{ id: 4, title: 'Market Correlations', route: '/analytics/correlations', keywords: ['correlation', 'market', 'relationship'] },
					{ id: 5, title: 'Execution Quality', route: '/analytics/execution', keywords: ['execution', 'slippage', 'quality'] },
					{ id: 6, title: 'Playbook Manager', route: '/playbook', keywords: ['playbook', 'strategy', 'setup'] }
				];
				
				const query = searchQuery.toLowerCase();
				searchResults.analytics = analyticsPages.filter(page => 
					page.title.toLowerCase().includes(query) ||
					page.keywords.some(keyword => keyword.includes(query))
				);
			}
			
			searchResults = { ...searchResults };
			selectedIndex = -1;
			
		} catch (error) {
			logger.error('Search failed:', error);
		} finally {
			loading = false;
		}
	}
	
	// Debounced search
	function handleSearchInput() {
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			performSearch();
		}, 300);
	}
	
	function formatDate(dateString: string) {
		return new Date(dateString).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}
	
	function formatPnL(amount: number) {
		const formatted = Math.abs(amount).toFixed(2);
		return amount >= 0 ? `+$${formatted}` : `-$${formatted}`;
	}
	
	onMount(() => {
		window.addEventListener('keydown', handleKeydown);
	});
	
	onDestroy(() => {
		window.removeEventListener('keydown', handleKeydown);
		clearTimeout(searchTimeout);
	});
</script>

<!-- Search Trigger Button -->
<button class="search-trigger" on:click={openSearch}>
	<Search size={18} />
	<span>Search</span>
	<kbd>⌘K</kbd>
</button>

<!-- Search Modal -->
{#if isOpen}
	<div class="search-overlay" on:click={closeSearch}>
		<div class="search-modal" on:click|stopPropagation>
			<div class="search-header">
				<div class="search-input-wrapper">
					<Search size={20} />
					<input
						bind:this={searchInput}
						bind:value={searchQuery}
						on:input={handleSearchInput}
						type="text"
						placeholder="Search trades, journal entries, analytics..."
						class="search-input"
					/>
					{#if searchQuery}
						<button class="clear-button" on:click={() => { searchQuery = ''; searchInput.focus(); }}>
							<X size={18} />
						</button>
					{/if}
				</div>
				<button class="close-button" on:click={closeSearch}>
					<X size={20} />
				</button>
			</div>
			
			<!-- Category Filters -->
			<div class="category-filters">
				{#each categories as category}
					<button
						class="category-button"
						class:active={activeCategory === category.id}
						on:click={() => { activeCategory = category.id; performSearch(); }}
					>
						<svelte:component this={category.icon} size={16} />
						{category.label}
					</button>
				{/each}
			</div>
			
			<!-- Search Results -->
			<div class="search-results">
				{#if loading}
					<div class="loading">
						<div class="spinner"></div>
						<span>Searching...</span>
					</div>
				{:else if searchQuery && getAllResults().length === 0}
					<div class="no-results">
						<p>No results found for "{searchQuery}"</p>
						<p class="hint">Try different keywords or check the spelling</p>
					</div>
				{:else if getAllResults().length > 0}
					{#each getAllResults() as result, index}
						<button
							class="result-item"
							class:selected={index === selectedIndex}
							on:click={() => selectResult(index)}
							on:mouseenter={() => selectedIndex = index}
						>
							{#if result.type === 'trade'}
								<div class="result-icon">
									<TrendingUp size={20} />
								</div>
								<div class="result-content">
									<div class="result-title">
										{result.symbol}
										<span class="result-meta">{result.direction || result.side || 'LONG'}</span>
									</div>
									<div class="result-details">
										<span class="pnl" class:positive={result.pnl >= 0}>
											{formatPnL(result.pnl || 0)}
										</span>
										<span class="separator">•</span>
										<span>{formatDate(result.entry_time || result.entry_date)}</span>
									</div>
								</div>
							{:else if result.type === 'journal'}
								<div class="result-icon">
									<FileText size={20} />
								</div>
								<div class="result-content">
									<div class="result-title">{result.title || 'Untitled Entry'}</div>
									<div class="result-details">
										<span>{formatDate(result.created_at)}</span>
										{#if result.tags?.length > 0}
											<span class="separator">•</span>
											<span class="tags">
												{#each result.tags.slice(0, 2) as tag}
													<span class="tag">#{tag}</span>
												{/each}
											</span>
										{/if}
									</div>
								</div>
							{:else if result.type === 'analytics'}
								<div class="result-icon">
									<BarChart3 size={20} />
								</div>
								<div class="result-content">
									<div class="result-title">{result.title}</div>
									<div class="result-details">
										<span>Analytics</span>
									</div>
								</div>
							{/if}
						</button>
					{/each}
				{:else}
					<div class="search-help">
						<h3>Quick Actions</h3>
						<div class="quick-actions">
							<button class="quick-action" on:click={() => { closeSearch(); goto('/trades/new'); }}>
								<TrendingUp size={18} />
								<span>Add New Trade</span>
							</button>
							<button class="quick-action" on:click={() => { closeSearch(); goto('/journal'); }}>
								<FileText size={18} />
								<span>Create Journal Entry</span>
							</button>
							<button class="quick-action" on:click={() => { closeSearch(); goto('/upload'); }}>
								<Hash size={18} />
								<span>Import Trades</span>
							</button>
						</div>
						
						<h3>Recent Searches</h3>
						<p class="hint">Start typing to search...</p>
					</div>
				{/if}
			</div>
			
			<!-- Search Footer -->
			<div class="search-footer">
				<div class="shortcuts">
					<kbd>↑↓</kbd> Navigate
					<kbd>Enter</kbd> Select
					<kbd>Esc</kbd> Close
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	.search-trigger {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		cursor: pointer;
		transition: all 0.2s;
		font-size: 0.875rem;
	}
	
	.search-trigger:hover {
		background: rgba(255, 255, 255, 0.15);
		border-color: rgba(255, 255, 255, 0.3);
	}
	
	.search-trigger kbd {
		background: rgba(255, 255, 255, 0.2);
		padding: 0.125rem 0.375rem;
		border-radius: 4px;
		font-size: 0.75rem;
		font-family: monospace;
	}
	
	.search-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(4px);
		z-index: 1000;
		display: flex;
		align-items: flex-start;
		justify-content: center;
		padding: 10vh 1rem;
	}
	
	.search-modal {
		background: white;
		border-radius: 12px;
		box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
		width: 100%;
		max-width: 600px;
		max-height: 70vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	
	.search-header {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		border-bottom: 1px solid #e5e7eb;
	}
	
	.search-input-wrapper {
		flex: 1;
		display: flex;
		align-items: center;
		gap: 0.75rem;
		background: #f3f4f6;
		padding: 0.75rem 1rem;
		border-radius: 8px;
	}
	
	.search-input-wrapper :global(svg) {
		color: #6b7280;
		flex-shrink: 0;
	}
	
	.search-input {
		flex: 1;
		background: none;
		border: none;
		outline: none;
		font-size: 1rem;
		color: #1a1a1a;
	}
	
	.clear-button,
	.close-button {
		background: none;
		border: none;
		color: #6b7280;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 6px;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.clear-button:hover,
	.close-button:hover {
		background: #f3f4f6;
		color: #1a1a1a;
	}
	
	.category-filters {
		display: flex;
		gap: 0.5rem;
		padding: 1rem;
		border-bottom: 1px solid #e5e7eb;
	}
	
	.category-button {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.5rem 0.875rem;
		background: #f3f4f6;
		border: 1px solid transparent;
		border-radius: 6px;
		font-size: 0.875rem;
		color: #6b7280;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.category-button:hover {
		background: #e5e7eb;
		color: #1a1a1a;
	}
	
	.category-button.active {
		background: #10b981;
		color: white;
		border-color: #10b981;
	}
	
	.search-results {
		flex: 1;
		overflow-y: auto;
		padding: 0.5rem;
	}
	
	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 3rem;
		color: #6b7280;
		gap: 1rem;
	}
	
	.spinner {
		width: 24px;
		height: 24px;
		border: 2px solid #e5e7eb;
		border-top-color: #10b981;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}
	
	@keyframes spin {
		to { transform: rotate(360deg); }
	}
	
	.no-results {
		text-align: center;
		padding: 3rem;
		color: #6b7280;
	}
	
	.no-results p {
		margin: 0.5rem 0;
	}
	
	.hint {
		font-size: 0.875rem;
		color: #9ca3af;
	}
	
	.result-item {
		display: flex;
		align-items: center;
		gap: 1rem;
		width: 100%;
		padding: 0.875rem 1rem;
		background: white;
		border: 1px solid transparent;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.2s;
		text-align: left;
	}
	
	.result-item:hover,
	.result-item.selected {
		background: #f3f4f6;
		border-color: #e5e7eb;
	}
	
	.result-item.selected {
		border-color: #10b981;
	}
	
	.result-icon {
		width: 40px;
		height: 40px;
		background: #f3f4f6;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #6b7280;
		flex-shrink: 0;
	}
	
	.result-content {
		flex: 1;
		min-width: 0;
	}
	
	.result-title {
		font-weight: 500;
		color: #1a1a1a;
		margin-bottom: 0.25rem;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.result-meta {
		font-size: 0.75rem;
		color: #6b7280;
		font-weight: normal;
		text-transform: uppercase;
	}
	
	.result-details {
		font-size: 0.875rem;
		color: #6b7280;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.pnl {
		font-weight: 500;
	}
	
	.pnl.positive {
		color: #10b981;
	}
	
	.pnl:not(.positive) {
		color: #ef4444;
	}
	
	.separator {
		color: #d1d5db;
	}
	
	.tags {
		display: flex;
		gap: 0.375rem;
	}
	
	.tag {
		color: #6b7280;
		font-size: 0.75rem;
	}
	
	.search-help {
		padding: 1.5rem;
	}
	
	.search-help h3 {
		font-size: 0.875rem;
		font-weight: 600;
		color: #6b7280;
		margin-bottom: 1rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.quick-actions {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		margin-bottom: 2rem;
	}
	
	.quick-action {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.2s;
		text-align: left;
		width: 100%;
		color: #4b5563;
	}
	
	.quick-action:hover {
		background: #f3f4f6;
		border-color: #d1d5db;
		color: #1a1a1a;
	}
	
	.search-footer {
		padding: 1rem;
		border-top: 1px solid #e5e7eb;
		background: #f9fafb;
	}
	
	.shortcuts {
		display: flex;
		align-items: center;
		gap: 1rem;
		font-size: 0.75rem;
		color: #6b7280;
		justify-content: center;
	}
	
	.shortcuts kbd {
		background: white;
		border: 1px solid #e5e7eb;
		padding: 0.125rem 0.375rem;
		border-radius: 4px;
		font-family: monospace;
		color: #4b5563;
	}
	
	/* Mobile Styles */
	@media (max-width: 640px) {
		.search-trigger span {
			display: none;
		}
		
		.search-trigger kbd {
			display: none;
		}
		
		.search-overlay {
			padding: 0;
		}
		
		.search-modal {
			max-height: 100vh;
			height: 100vh;
			max-width: 100%;
			border-radius: 0;
		}
		
		.category-filters {
			overflow-x: auto;
			-webkit-overflow-scrolling: touch;
		}
		
		.shortcuts {
			font-size: 0.625rem;
			gap: 0.5rem;
		}
	}
	
	/* Hide on mobile - search will be in mobile nav */
	@media (max-width: 768px) {
		.search-trigger {
			display: none;
		}
	}
</style>