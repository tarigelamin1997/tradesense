<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	
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
	}> = [];
	
	const dispatch = createEventDispatcher();
	
	function formatCurrency(value: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD'
		}).format(value);
	}
</script>

<div class="trade-list">
	<table>
		<thead>
			<tr>
				<th>Symbol</th>
				<th>Side</th>
				<th>Entry</th>
				<th>Exit</th>
				<th>Quantity</th>
				<th>P&L</th>
				<th>Entry Time</th>
				<th>Exit Time</th>
				<th>Actions</th>
			</tr>
		</thead>
		<tbody>
			{#each trades as trade}
				<tr>
					<td class="symbol">{trade.symbol}</td>
					<td>
						<span class="side" class:long={trade.side === 'long'} class:short={trade.side === 'short'}>
							{trade.side}
						</span>
					</td>
					<td>${trade.entryPrice.toFixed(2)}</td>
					<td>${trade.exitPrice.toFixed(2)}</td>
					<td>{trade.quantity}</td>
					<td class:profit={trade.pnl > 0} class:loss={trade.pnl < 0}>
						{formatCurrency(trade.pnl)}
					</td>
					<td>{trade.entryDate}</td>
					<td>{trade.exitDate}</td>
					<td class="actions">
						<button 
							class="action-button edit" 
							on:click={() => dispatch('edit', { trade })}
							title="Edit trade"
						>
							✏️
						</button>
						<button 
							class="action-button delete" 
							on:click={() => dispatch('delete', { id: trade.id })}
							title="Delete trade"
						>
							🗑️
						</button>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
	
	{#if trades.length === 0}
		<div class="empty">No trades to display</div>
	{/if}
</div>

<style>
	.symbol {
		font-weight: 600;
	}
	
	.side {
		display: inline-block;
		padding: 0.25rem 0.75rem;
		border-radius: 4px;
		font-size: 0.875rem;
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
	
	.empty {
		text-align: center;
		padding: 2rem;
		color: #666;
	}
	
	.actions {
		display: flex;
		gap: 0.5rem;
	}
	
	.action-button {
		padding: 0.25rem 0.5rem;
		background: none;
		border: 1px solid #e0e0e0;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.875rem;
		transition: all 0.2s;
	}
	
	.action-button:hover {
		background: #f5f5f5;
	}
	
	.action-button.edit:hover {
		border-color: #3b82f6;
		background: #eff6ff;
	}
	
	.action-button.delete:hover {
		border-color: #ef4444;
		background: #fef2f2;
	}
</style>