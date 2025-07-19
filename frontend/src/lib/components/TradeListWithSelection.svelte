<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { Edit2, Trash2, TrendingUp, TrendingDown } from 'lucide-svelte';
	import TradeMobileCard from './TradeMobileCard.svelte';
	
	export let trades: Array<{
		id: number;
		symbol: string;
		side: 'long' | 'short';
		entryPrice: number;
		exitPrice: number;
		quantity: number;
		pnl: number;
		entryDate: string;
		exitDate: string;
		strategy?: string;
		notes?: string;
	}> = [];
	
	export let selectedIds: Set<number> = new Set();
	export let enableSelection = true;
	
	const dispatch = createEventDispatcher();
	
	let isMobile = false;
	
	onMount(() => {
		// Check if mobile
		const checkMobile = () => {
			isMobile = window.innerWidth <= 768;
		};
		
		checkMobile();
		window.addEventListener('resize', checkMobile);
		
		return () => {
			window.removeEventListener('resize', checkMobile);
		};
	});
	
	function formatCurrency(value: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD'
		}).format(value);
	}
	
	function formatDate(dateString: string): string {
		const date = new Date(dateString);
		return date.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
	
	function calculateDuration(entryDate: string, exitDate: string): string {
		const entry = new Date(entryDate);
		const exit = new Date(exitDate);
		const durationMs = exit.getTime() - entry.getTime();
		const hours = Math.floor(durationMs / (1000 * 60 * 60));
		const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
		
		if (hours > 0) {
			return `${hours}h ${minutes}m`;
		} else {
			return `${minutes}m`;
		}
	}
	
	function handleSelectToggle(tradeId: number) {
		dispatch('toggleSelect', { id: tradeId });
	}
	
	function handleSelectAll() {
		if (selectedIds.size === trades.length) {
			dispatch('deselectAll');
		} else {
			dispatch('selectAll');
		}
	}
	
	$: isAllSelected = trades.length > 0 && selectedIds.size === trades.length;
	$: isPartiallySelected = selectedIds.size > 0 && selectedIds.size < trades.length;
</script>

<div class="trade-list">
	{#if isMobile}
		<!-- Mobile View -->
		<div class="mobile-trades">
			{#each trades as trade}
				<TradeMobileCard 
					{trade}
					isSelected={selectedIds.has(trade.id)}
					on:edit
					on:delete
					on:toggleSelect
				/>
			{/each}
		</div>
	{:else}
		<!-- Desktop View -->
		<table>
			<thead>
				<tr>
				{#if enableSelection}
					<th class="checkbox-column">
						<input
							type="checkbox"
							checked={isAllSelected}
							indeterminate={isPartiallySelected}
							on:change={handleSelectAll}
							title={isAllSelected ? 'Deselect all' : 'Select all'}
						/>
					</th>
				{/if}
				<th>Symbol</th>
				<th>Side</th>
				<th>Entry</th>
				<th>Exit</th>
				<th>Qty</th>
				<th>P&L</th>
				<th>Duration</th>
				<th>Strategy</th>
				<th>Actions</th>
			</tr>
		</thead>
		<tbody>
			{#each trades as trade}
				<tr class:selected={selectedIds.has(trade.id)}>
					{#if enableSelection}
						<td class="checkbox-column">
							<input
								type="checkbox"
								checked={selectedIds.has(trade.id)}
								on:change={() => handleSelectToggle(trade.id)}
							/>
						</td>
					{/if}
					<td class="symbol">{trade.symbol}</td>
					<td>
						<span class="side" class:long={trade.side === 'long'} class:short={trade.side === 'short'}>
							{#if trade.side === 'long'}
								<TrendingUp size={14} />
							{:else}
								<TrendingDown size={14} />
							{/if}
							{trade.side}
						</span>
					</td>
					<td class="price">${trade.entryPrice.toFixed(2)}</td>
					<td class="price">${trade.exitPrice.toFixed(2)}</td>
					<td class="quantity">{trade.quantity}</td>
					<td class="pnl" class:profit={trade.pnl > 0} class:loss={trade.pnl < 0}>
						{formatCurrency(trade.pnl)}
						<span class="pnl-percent">
							({((trade.pnl / (trade.entryPrice * trade.quantity)) * 100).toFixed(1)}%)
						</span>
					</td>
					<td class="duration">{calculateDuration(trade.entryDate, trade.exitDate)}</td>
					<td class="strategy">{trade.strategy || '-'}</td>
					<td class="actions">
						<button 
							class="action-button edit" 
							on:click={() => dispatch('edit', { trade })}
							title="Edit trade"
						>
							<Edit2 size={14} />
						</button>
						<button 
							class="action-button delete" 
							on:click={() => dispatch('delete', { id: trade.id })}
							title="Delete trade"
						>
							<Trash2 size={14} />
						</button>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
	{/if}
	
	{#if trades.length === 0}
		<div class="empty">
			<p>No trades to display</p>
			<p class="empty-hint">Add your first trade or adjust filters</p>
		</div>
	{/if}
</div>

<style>
	.trade-list {
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		overflow: hidden;
	}
	
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}
	
	thead {
		background: #f9fafb;
		border-bottom: 1px solid #e5e7eb;
	}
	
	th {
		padding: 0.75rem 1rem;
		text-align: left;
		font-weight: 600;
		color: #666;
		white-space: nowrap;
		position: sticky;
		top: 0;
		background: #f9fafb;
		z-index: 1;
	}
	
	.checkbox-column {
		width: 40px;
		text-align: center;
		padding: 0.75rem 0.5rem;
	}
	
	.checkbox-column input {
		cursor: pointer;
	}
	
	tbody tr {
		border-bottom: 1px solid #f0f0f0;
		transition: background-color 0.2s;
	}
	
	tbody tr:hover {
		background: #fafafa;
	}
	
	tbody tr.selected {
		background: #f0fdf4;
	}
	
	tbody tr.selected:hover {
		background: #dcfce7;
	}
	
	tbody tr:last-child {
		border-bottom: none;
	}
	
	td {
		padding: 0.75rem 1rem;
		color: #333;
	}
	
	.symbol {
		font-weight: 600;
		color: #111;
	}
	
	.side {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
		font-size: 0.75rem;
		font-weight: 500;
		text-transform: uppercase;
	}
	
	.side.long {
		background: #d1fae5;
		color: #065f46;
	}
	
	.side.short {
		background: #fee2e2;
		color: #991b1b;
	}
	
	.price, .quantity {
		font-family: 'Courier New', monospace;
		text-align: right;
	}
	
	.pnl {
		font-weight: 600;
		text-align: right;
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 0.125rem;
	}
	
	.pnl.profit {
		color: #059669;
	}
	
	.pnl.loss {
		color: #dc2626;
	}
	
	.pnl-percent {
		font-size: 0.75rem;
		font-weight: 400;
		opacity: 0.8;
	}
	
	.duration {
		color: #666;
		font-size: 0.875rem;
	}
	
	.strategy {
		color: #666;
		font-size: 0.875rem;
	}
	
	.actions {
		display: flex;
		gap: 0.5rem;
		justify-content: flex-end;
	}
	
	.action-button {
		padding: 0.375rem;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 4px;
		cursor: pointer;
		color: #666;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.action-button:hover {
		background: #f5f5f5;
		color: #333;
	}
	
	.action-button.edit:hover {
		border-color: #3b82f6;
		background: #eff6ff;
		color: #3b82f6;
	}
	
	.action-button.delete:hover {
		border-color: #ef4444;
		background: #fef2f2;
		color: #ef4444;
	}
	
	.empty {
		text-align: center;
		padding: 4rem 2rem;
		color: #666;
	}
	
	.empty p {
		margin: 0;
		font-size: 1rem;
	}
	
	.empty-hint {
		margin-top: 0.5rem !important;
		font-size: 0.875rem !important;
		color: #999 !important;
	}
	
	@media (max-width: 1024px) {
		.trade-list {
			overflow-x: auto;
		}
		
		table {
			min-width: 800px;
		}
	}
	
	@media (max-width: 640px) {
		th, td {
			padding: 0.5rem;
		}
		
		.side {
			font-size: 0.625rem;
		}
		
		.pnl-percent {
			display: none;
		}
	}
</style>