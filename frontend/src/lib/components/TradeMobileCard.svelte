<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { TrendingUp, TrendingDown, Calendar, Hash, Edit, Trash2 } from 'lucide-svelte';
	import type { Trade } from '$lib/stores/trades';
	
	export let trade: Trade;
	export let isSelected = false;
	
	const dispatch = createEventDispatcher();
	
	function handleEdit() {
		dispatch('edit', { trade });
	}
	
	function handleDelete() {
		dispatch('delete', { id: trade.id });
	}
	
	function handleToggleSelect() {
		dispatch('toggleSelect', { id: trade.id });
	}
	
	function formatDate(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}
	
	function formatTime(dateStr: string): string {
		const date = new Date(dateStr);
		return date.toLocaleTimeString('en-US', {
			hour: '2-digit',
			minute: '2-digit'
		});
	}
	
	function formatCurrency(value: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD'
		}).format(value);
	}
</script>

<div class="trade-card" class:selected={isSelected}>
	<div class="trade-header">
		<div class="symbol-section">
			<h3>{trade.symbol}</h3>
			<span class="side" class:long={trade.side === 'long'} class:short={trade.side === 'short'}>
				{#if trade.side === 'long'}
					<TrendingUp size={14} />
				{:else}
					<TrendingDown size={14} />
				{/if}
				{trade.side.toUpperCase()}
			</span>
		</div>
		<div class="pnl" class:positive={trade.pnl > 0} class:negative={trade.pnl < 0}>
			{formatCurrency(trade.pnl)}
		</div>
	</div>
	
	<div class="trade-details">
		<div class="detail-row">
			<div class="detail">
				<span class="label">Entry</span>
				<span class="value">{formatCurrency(trade.entryPrice)}</span>
			</div>
			<div class="detail">
				<span class="label">Exit</span>
				<span class="value">{formatCurrency(trade.exitPrice || 0)}</span>
			</div>
			<div class="detail">
				<span class="label">Qty</span>
				<span class="value">{trade.quantity}</span>
			</div>
		</div>
		
		<div class="date-row">
			<Calendar size={14} />
			<span>{formatDate(trade.entryDate)}</span>
			<span class="time">{formatTime(trade.entryDate)}</span>
		</div>
		
		{#if trade.strategy}
			<div class="strategy-row">
				<Hash size={14} />
				<span>{trade.strategy}</span>
			</div>
		{/if}
	</div>
	
	<div class="trade-actions">
		<label class="checkbox-container">
			<input 
				type="checkbox" 
				checked={isSelected}
				on:change={handleToggleSelect}
			/>
			<span class="checkbox-label">Select</span>
		</label>
		<div class="action-buttons">
			<button on:click={handleEdit} class="action-button edit">
				<Edit size={16} />
			</button>
			<button on:click={handleDelete} class="action-button delete">
				<Trash2 size={16} />
			</button>
		</div>
	</div>
</div>

<style>
	.trade-card {
		background: white;
		border-radius: 12px;
		padding: 1rem;
		border: 2px solid #e0e0e0;
		transition: all 0.2s;
		margin-bottom: 0.75rem;
	}
	
	.trade-card.selected {
		border-color: #10b981;
		background: #f0fdf4;
	}
	
	.trade-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 0.75rem;
	}
	
	.symbol-section {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	
	.symbol-section h3 {
		font-size: 1.25rem;
		margin: 0;
		font-weight: 600;
	}
	
	.side {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.75rem;
		font-weight: 500;
	}
	
	.side.long {
		background: #d1fae5;
		color: #065f46;
	}
	
	.side.short {
		background: #fee2e2;
		color: #991b1b;
	}
	
	.pnl {
		font-size: 1.25rem;
		font-weight: 600;
	}
	
	.pnl.positive {
		color: #10b981;
	}
	
	.pnl.negative {
		color: #ef4444;
	}
	
	.trade-details {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		margin-bottom: 1rem;
	}
	
	.detail-row {
		display: flex;
		gap: 1.5rem;
	}
	
	.detail {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
	}
	
	.label {
		font-size: 0.75rem;
		color: #666;
	}
	
	.value {
		font-weight: 500;
		color: #333;
	}
	
	.date-row,
	.strategy-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		color: #666;
	}
	
	.time {
		color: #999;
	}
	
	.trade-actions {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-top: 0.75rem;
		border-top: 1px solid #e0e0e0;
	}
	
	.checkbox-container {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
	}
	
	.checkbox-label {
		font-size: 0.875rem;
		color: #666;
	}
	
	.action-buttons {
		display: flex;
		gap: 0.5rem;
	}
	
	.action-button {
		padding: 0.5rem;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.action-button:active {
		transform: scale(0.95);
	}
	
	.action-button.edit:hover {
		background: #e0f2fe;
		border-color: #7dd3fc;
		color: #0369a1;
	}
	
	.action-button.delete:hover {
		background: #fee2e2;
		border-color: #fca5a5;
		color: #dc2626;
	}
</style>