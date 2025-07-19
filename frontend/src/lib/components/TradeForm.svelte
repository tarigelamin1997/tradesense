<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { tradesApi, type Trade } from '$lib/api/trades';
	
	export let trade: Partial<Trade> | null = null;
	export let show = false;
	
	const dispatch = createEventDispatcher();
	
	let formData = {
		symbol: '',
		side: 'long' as 'long' | 'short',
		entry_price: 0,
		exit_price: 0,
		quantity: 0,
		entry_date: '',
		exit_date: '',
		strategy: '',
		notes: ''
	};
	
	let loading = false;
	let error = '';
	
	// Initialize form when trade prop changes
	$: if (trade) {
		formData = {
			symbol: trade.symbol || '',
			side: trade.side || 'long',
			entry_price: trade.entry_price || 0,
			exit_price: trade.exit_price || 0,
			quantity: trade.quantity || 0,
			entry_date: trade.entry_date || '',
			exit_date: trade.exit_date || '',
			strategy: trade.strategy || '',
			notes: trade.notes || ''
		};
	}
	
	async function handleSubmit(event: Event) {
		event.preventDefault();
		loading = true;
		error = '';
		
		try {
			if (trade?.id) {
				// Update existing trade
				await tradesApi.updateTrade(trade.id, formData);
				dispatch('save', { type: 'update', trade: { ...trade, ...formData } });
			} else {
				// Create new trade
				const newTrade = await tradesApi.createTrade(formData);
				dispatch('save', { type: 'create', trade: newTrade });
			}
			
			handleClose();
		} catch (err: any) {
			error = err.message || 'Failed to save trade';
		} finally {
			loading = false;
		}
	}
	
	function handleClose() {
		dispatch('close');
		// Reset form
		formData = {
			symbol: '',
			side: 'long',
			entry_price: 0,
			exit_price: 0,
			quantity: 0,
			entry_date: '',
			exit_date: '',
			strategy: '',
			notes: ''
		};
		error = '';
	}
	
	// Calculate P&L
	$: pnl = formData.side === 'long' 
		? (formData.exit_price - formData.entry_price) * formData.quantity
		: (formData.entry_price - formData.exit_price) * formData.quantity;
	
	$: pnlPercent = formData.entry_price > 0 
		? (pnl / (formData.entry_price * formData.quantity)) * 100 
		: 0;
</script>

{#if show}
	<div class="modal-backdrop" on:click={handleClose}>
		<div class="modal" on:click|stopPropagation>
			<div class="modal-header">
				<h2>{trade?.id ? 'Edit Trade' : 'New Trade'}</h2>
				<button type="button" class="close-button" on:click={handleClose}>×</button>
			</div>
			
			{#if error}
				<div class="error-message">{error}</div>
			{/if}
			
			<form on:submit={handleSubmit}>
				<div class="form-grid">
					<div class="form-group">
						<label for="symbol">Symbol</label>
						<input
							id="symbol"
							type="text"
							bind:value={formData.symbol}
							required
							placeholder="e.g., AAPL"
							disabled={loading}
						/>
					</div>
					
					<div class="form-group">
						<label for="side">Side</label>
						<select id="side" bind:value={formData.side} disabled={loading}>
							<option value="long">Long</option>
							<option value="short">Short</option>
						</select>
					</div>
					
					<div class="form-group">
						<label for="entry_price">Entry Price</label>
						<input
							id="entry_price"
							type="number"
							step="0.01"
							bind:value={formData.entry_price}
							required
							placeholder="0.00"
							disabled={loading}
						/>
					</div>
					
					<div class="form-group">
						<label for="exit_price">Exit Price</label>
						<input
							id="exit_price"
							type="number"
							step="0.01"
							bind:value={formData.exit_price}
							required
							placeholder="0.00"
							disabled={loading}
						/>
					</div>
					
					<div class="form-group">
						<label for="quantity">Quantity</label>
						<input
							id="quantity"
							type="number"
							bind:value={formData.quantity}
							required
							placeholder="0"
							disabled={loading}
						/>
					</div>
					
					<div class="form-group">
						<label for="strategy">Strategy</label>
						<input
							id="strategy"
							type="text"
							bind:value={formData.strategy}
							placeholder="e.g., Momentum"
							disabled={loading}
						/>
					</div>
					
					<div class="form-group">
						<label for="entry_date">Entry Date</label>
						<input
							id="entry_date"
							type="datetime-local"
							bind:value={formData.entry_date}
							required
							disabled={loading}
						/>
					</div>
					
					<div class="form-group">
						<label for="exit_date">Exit Date</label>
						<input
							id="exit_date"
							type="datetime-local"
							bind:value={formData.exit_date}
							required
							disabled={loading}
						/>
					</div>
				</div>
				
				<div class="form-group full-width">
					<label for="notes">Notes</label>
					<textarea
						id="notes"
						bind:value={formData.notes}
						rows="3"
						placeholder="Trade notes..."
						disabled={loading}
					></textarea>
				</div>
				
				<!-- P&L Preview -->
				<div class="pnl-preview">
					<h3>P&L Preview</h3>
					<div class="pnl-values">
						<div class="pnl-item">
							<span>Amount:</span>
							<span class:profit={pnl > 0} class:loss={pnl < 0}>
								${pnl.toFixed(2)}
							</span>
						</div>
						<div class="pnl-item">
							<span>Percentage:</span>
							<span class:profit={pnl > 0} class:loss={pnl < 0}>
								{pnlPercent.toFixed(2)}%
							</span>
						</div>
					</div>
				</div>
				
				<div class="form-actions">
					<button type="button" class="cancel-button" on:click={handleClose} disabled={loading}>
						Cancel
					</button>
					<button type="submit" class="submit-button" disabled={loading}>
						{loading ? 'Saving...' : (trade?.id ? 'Update Trade' : 'Create Trade')}
					</button>
				</div>
			</form>
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 2rem;
	}
	
	.modal {
		background: white;
		border-radius: 12px;
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
		max-width: 600px;
		width: 100%;
		max-height: 90vh;
		overflow-y: auto;
		padding: 2rem;
	}
	
	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}
	
	.modal-header h2 {
		font-size: 1.5rem;
		margin: 0;
	}
	
	.close-button {
		background: none;
		border: none;
		font-size: 2rem;
		line-height: 1;
		color: #666;
		cursor: pointer;
		padding: 0;
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.close-button:hover {
		color: #333;
	}
	
	.error-message {
		background: #fee;
		color: #c00;
		padding: 0.75rem;
		border-radius: 6px;
		margin-bottom: 1rem;
		font-size: 0.875rem;
	}
	
	.form-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
		margin-bottom: 1rem;
	}
	
	.form-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.form-group.full-width {
		grid-column: 1 / -1;
	}
	
	label {
		font-size: 0.875rem;
		font-weight: 500;
		color: #333;
	}
	
	input, select, textarea {
		padding: 0.5rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 1rem;
		font-family: inherit;
	}
	
	input:focus, select:focus, textarea:focus {
		outline: none;
		border-color: #10b981;
	}
	
	input:disabled, select:disabled, textarea:disabled {
		background: #f5f5f5;
		cursor: not-allowed;
	}
	
	textarea {
		resize: vertical;
		min-height: 80px;
	}
	
	.pnl-preview {
		background: #f9fafb;
		padding: 1rem;
		border-radius: 8px;
		margin-bottom: 1.5rem;
	}
	
	.pnl-preview h3 {
		font-size: 0.875rem;
		margin-bottom: 0.5rem;
		color: #666;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.pnl-values {
		display: flex;
		gap: 2rem;
	}
	
	.pnl-item {
		display: flex;
		gap: 0.5rem;
		align-items: center;
	}
	
	.pnl-item span:first-child {
		color: #666;
		font-size: 0.875rem;
	}
	
	.pnl-item span:last-child {
		font-weight: 600;
		font-size: 1.125rem;
	}
	
	.form-actions {
		display: flex;
		gap: 1rem;
		justify-content: flex-end;
	}
	
	.cancel-button {
		padding: 0.75rem 1.5rem;
		background: #f3f4f6;
		color: #333;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 1rem;
		transition: background 0.2s;
	}
	
	.cancel-button:hover:not(:disabled) {
		background: #e5e7eb;
	}
	
	.submit-button {
		padding: 0.75rem 1.5rem;
		background: #10b981;
		color: white;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 1rem;
		transition: background 0.2s;
	}
	
	.submit-button:hover:not(:disabled) {
		background: #059669;
	}
	
	.submit-button:disabled, .cancel-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	.profit {
		color: #10b981;
	}
	
	.loss {
		color: #ef4444;
	}
	
	@media (max-width: 640px) {
		.form-grid {
			grid-template-columns: 1fr;
		}
		
		.modal {
			padding: 1.5rem;
		}
	}
</style>