<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { tradesApi, type Trade } from '$lib/api/trades';
	import { Save, Calculator, TrendingUp, TrendingDown, X } from 'lucide-svelte';
	
	export let trade: Partial<Trade> | null = null;
	export let show = false;
	
	const dispatch = createEventDispatcher();
	
	// Popular trading strategies
	const strategies = [
		'Momentum',
		'Mean Reversion',
		'Breakout',
		'Scalping',
		'Swing Trading',
		'Position Trading',
		'Day Trading',
		'News Trading',
		'Pairs Trading',
		'Other'
	];
	
	// Commission presets
	const commissionPresets = [
		{ label: 'None', value: 0 },
		{ label: 'Fixed $5', value: 5 },
		{ label: 'Fixed $10', value: 10 },
		{ label: 'IB ($1/trade)', value: 1 },
		{ label: 'Custom', value: -1 }
	];
	
	let formData = {
		symbol: '',
		side: 'long' as 'long' | 'short',
		entry_price: '',
		exit_price: '',
		quantity: '',
		entry_date: '',
		exit_date: '',
		strategy: '',
		notes: '',
		commission: '0',
		risk_amount: '',
		target_price: '',
		stop_loss: ''
	};
	
	let loading = false;
	let error = '';
	let successMessage = '';
	let showAdvanced = false;
	let customCommission = false;
	let selectedCommissionPreset = 0;
	
	// Initialize form when trade prop changes
	$: if (trade) {
		const entryDate = trade.entry_date ? new Date(trade.entry_date).toISOString().slice(0, 16) : '';
		const exitDate = trade.exit_date ? new Date(trade.exit_date).toISOString().slice(0, 16) : '';
		
		formData = {
			symbol: trade.symbol || '',
			side: trade.side || 'long',
			entry_price: trade.entry_price?.toString() || '',
			exit_price: trade.exit_price?.toString() || '',
			quantity: trade.quantity?.toString() || '',
			entry_date: entryDate,
			exit_date: exitDate,
			strategy: trade.strategy || '',
			notes: trade.notes || '',
			commission: '0',
			risk_amount: '',
			target_price: '',
			stop_loss: ''
		};
	} else {
		// Set default dates for new trades
		const now = new Date();
		formData.entry_date = now.toISOString().slice(0, 16);
		formData.exit_date = now.toISOString().slice(0, 16);
	}
	
	// Convert string inputs to numbers for calculations
	$: entryPrice = parseFloat(formData.entry_price) || 0;
	$: exitPrice = parseFloat(formData.exit_price) || 0;
	$: quantity = parseFloat(formData.quantity) || 0;
	$: commission = parseFloat(formData.commission) || 0;
	$: targetPrice = parseFloat(formData.target_price) || 0;
	$: stopLoss = parseFloat(formData.stop_loss) || 0;
	
	// Calculate P&L
	$: grossPnL = formData.side === 'long' 
		? (exitPrice - entryPrice) * quantity
		: (entryPrice - exitPrice) * quantity;
	
	$: netPnL = grossPnL - (commission * 2); // Commission on entry and exit
	
	$: pnlPercent = entryPrice > 0 && quantity > 0
		? (netPnL / (entryPrice * quantity)) * 100 
		: 0;
	
	// Calculate risk/reward ratio
	$: riskAmount = formData.side === 'long'
		? (entryPrice - stopLoss) * quantity
		: (stopLoss - entryPrice) * quantity;
	
	$: rewardAmount = formData.side === 'long'
		? (targetPrice - entryPrice) * quantity
		: (entryPrice - targetPrice) * quantity;
	
	$: riskRewardRatio = riskAmount > 0 ? rewardAmount / riskAmount : 0;
	
	// Calculate trade duration
	$: {
		if (formData.entry_date && formData.exit_date) {
			const entry = new Date(formData.entry_date);
			const exit = new Date(formData.exit_date);
			const durationMs = exit.getTime() - entry.getTime();
			const hours = Math.floor(durationMs / (1000 * 60 * 60));
			const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
			tradeDuration = `${hours}h ${minutes}m`;
		} else {
			tradeDuration = '-';
		}
	}
	let tradeDuration = '-';
	
	function handleCommissionPresetChange(event: Event) {
		const value = parseInt((event.target as HTMLSelectElement).value);
		selectedCommissionPreset = value;
		
		if (value === -1) {
			customCommission = true;
		} else {
			customCommission = false;
			formData.commission = value.toString();
		}
	}
	
	async function handleSubmit(event: Event, continueAdding = false) {
		event.preventDefault();
		loading = true;
		error = '';
		successMessage = '';
		
		try {
			const tradeData: any = {
				symbol: formData.symbol.toUpperCase(),
				side: formData.side,
				entry_price: parseFloat(formData.entry_price),
				exit_price: parseFloat(formData.exit_price),
				quantity: parseFloat(formData.quantity),
				entry_date: new Date(formData.entry_date).toISOString(),
				exit_date: new Date(formData.exit_date).toISOString(),
				strategy: formData.strategy,
				notes: formData.notes
			};
			
			if (trade?.id) {
				// Update existing trade
				await tradesApi.updateTrade(trade.id, tradeData);
				dispatch('save', { type: 'update', trade: { ...trade, ...tradeData } });
			} else {
				// Create new trade
				const newTrade = await tradesApi.createTrade(tradeData);
				dispatch('save', { type: 'create', trade: newTrade });
			}
			
			if (continueAdding) {
				successMessage = 'Trade saved! Add another...';
				resetForm();
			} else {
				handleClose();
			}
		} catch (err: any) {
			error = err.message || 'Failed to save trade';
		} finally {
			loading = false;
		}
	}
	
	function resetForm() {
		const now = new Date();
		formData = {
			symbol: '',
			side: formData.side, // Keep the side preference
			entry_price: '',
			exit_price: '',
			quantity: formData.quantity, // Keep quantity as it's often the same
			entry_date: now.toISOString().slice(0, 16),
			exit_date: now.toISOString().slice(0, 16),
			strategy: formData.strategy, // Keep strategy preference
			notes: '',
			commission: formData.commission, // Keep commission settings
			risk_amount: '',
			target_price: '',
			stop_loss: ''
		};
	}
	
	function handleClose() {
		dispatch('close');
		error = '';
		successMessage = '';
	}
	
	// Auto-capitalize symbol as user types
	function handleSymbolInput(event: Event) {
		const input = event.target as HTMLInputElement;
		formData.symbol = input.value.toUpperCase();
	}
	
	// Quick calculation helpers
	function calculateFromRiskReward() {
		if (riskRewardRatio > 0 && stopLoss > 0) {
			if (formData.side === 'long') {
				formData.target_price = (entryPrice + (entryPrice - stopLoss) * riskRewardRatio).toFixed(2);
			} else {
				formData.target_price = (entryPrice - (stopLoss - entryPrice) * riskRewardRatio).toFixed(2);
			}
		}
	}
</script>

{#if show}
	<div class="modal-backdrop" on:click={handleClose}>
		<div class="modal" on:click|stopPropagation>
			<div class="modal-header">
				<h2>{trade?.id ? 'Edit Trade' : 'New Trade'}</h2>
				<button type="button" class="close-button" on:click={handleClose}>
					<X size={24} />
				</button>
			</div>
			
			{#if error}
				<div class="error-message">{error}</div>
			{/if}
			
			{#if successMessage}
				<div class="success-message">{successMessage}</div>
			{/if}
			
			<form on:submit={(e) => handleSubmit(e, false)}>
				<!-- Basic Fields -->
				<div class="form-section">
					<h3>Trade Details</h3>
					<div class="form-grid">
						<div class="form-group">
							<label for="symbol">
								Symbol <span class="required">*</span>
							</label>
							<input
								id="symbol"
								type="text"
								bind:value={formData.symbol}
								on:input={handleSymbolInput}
								required
								placeholder="AAPL"
								disabled={loading}
								class="uppercase"
							/>
						</div>
						
						<div class="form-group">
							<label for="side">
								Side <span class="required">*</span>
							</label>
							<div class="side-selector">
								<button
									type="button"
									class="side-button {formData.side === 'long' ? 'active long' : ''}"
									on:click={() => formData.side = 'long'}
									disabled={loading}
								>
									<TrendingUp size={16} />
									Long
								</button>
								<button
									type="button"
									class="side-button {formData.side === 'short' ? 'active short' : ''}"
									on:click={() => formData.side = 'short'}
									disabled={loading}
								>
									<TrendingDown size={16} />
									Short
								</button>
							</div>
						</div>
						
						<div class="form-group">
							<label for="quantity">
								Quantity <span class="required">*</span>
							</label>
							<input
								id="quantity"
								type="number"
								bind:value={formData.quantity}
								required
								placeholder="100"
								min="0"
								step="1"
								disabled={loading}
							/>
						</div>
						
						<div class="form-group">
							<label for="strategy">Strategy</label>
							<select id="strategy" bind:value={formData.strategy} disabled={loading}>
								<option value="">Select strategy...</option>
								{#each strategies as strategy}
									<option value={strategy}>{strategy}</option>
								{/each}
							</select>
						</div>
					</div>
				</div>
				
				<!-- Price Fields -->
				<div class="form-section">
					<h3>Prices & Timing</h3>
					<div class="form-grid">
						<div class="form-group">
							<label for="entry_price">
								Entry Price <span class="required">*</span>
							</label>
							<input
								id="entry_price"
								type="number"
								bind:value={formData.entry_price}
								required
								placeholder="0.00"
								min="0"
								step="0.01"
								disabled={loading}
							/>
						</div>
						
						<div class="form-group">
							<label for="exit_price">
								Exit Price <span class="required">*</span>
							</label>
							<input
								id="exit_price"
								type="number"
								bind:value={formData.exit_price}
								required
								placeholder="0.00"
								min="0"
								step="0.01"
								disabled={loading}
							/>
						</div>
						
						<div class="form-group">
							<label for="entry_date">
								Entry Date <span class="required">*</span>
							</label>
							<input
								id="entry_date"
								type="datetime-local"
								bind:value={formData.entry_date}
								required
								disabled={loading}
							/>
						</div>
						
						<div class="form-group">
							<label for="exit_date">
								Exit Date <span class="required">*</span>
							</label>
							<input
								id="exit_date"
								type="datetime-local"
								bind:value={formData.exit_date}
								required
								disabled={loading}
							/>
						</div>
					</div>
				</div>
				
				<!-- Advanced Fields -->
				<div class="form-section">
					<button
						type="button"
						class="toggle-advanced"
						on:click={() => showAdvanced = !showAdvanced}
					>
						{showAdvanced ? 'Hide' : 'Show'} Advanced Options
					</button>
					
					{#if showAdvanced}
						<div class="form-grid">
							<div class="form-group">
								<label for="commission">Commission</label>
								<div class="commission-input">
									<select
										bind:value={selectedCommissionPreset}
										on:change={handleCommissionPresetChange}
										disabled={loading}
									>
										{#each commissionPresets as preset}
											<option value={preset.value}>{preset.label}</option>
										{/each}
									</select>
									{#if customCommission}
										<input
											type="number"
											bind:value={formData.commission}
											placeholder="0.00"
											min="0"
											step="0.01"
											disabled={loading}
										/>
									{/if}
								</div>
							</div>
							
							<div class="form-group">
								<label for="stop_loss">Stop Loss</label>
								<input
									id="stop_loss"
									type="number"
									bind:value={formData.stop_loss}
									placeholder="0.00"
									min="0"
									step="0.01"
									disabled={loading}
								/>
							</div>
							
							<div class="form-group">
								<label for="target_price">Target Price</label>
								<div class="input-with-button">
									<input
										id="target_price"
										type="number"
										bind:value={formData.target_price}
										placeholder="0.00"
										min="0"
										step="0.01"
										disabled={loading}
									/>
									<button
										type="button"
										class="calc-button"
										on:click={calculateFromRiskReward}
										disabled={loading || !stopLoss || !entryPrice}
										title="Calculate from R:R ratio"
									>
										<Calculator size={16} />
									</button>
								</div>
							</div>
						</div>
					{/if}
				</div>
				
				<!-- Notes -->
				<div class="form-section">
					<div class="form-group full-width">
						<label for="notes">Notes</label>
						<textarea
							id="notes"
							bind:value={formData.notes}
							rows="3"
							placeholder="Trade setup, market conditions, lessons learned..."
							disabled={loading}
						></textarea>
					</div>
				</div>
				
				<!-- P&L Summary -->
				<div class="pnl-summary">
					<h3>Trade Summary</h3>
					<div class="summary-grid">
						<div class="summary-item">
							<span class="label">Gross P&L:</span>
							<span class="value" class:profit={grossPnL > 0} class:loss={grossPnL < 0}>
								${grossPnL.toFixed(2)}
							</span>
						</div>
						<div class="summary-item">
							<span class="label">Commission:</span>
							<span class="value">-${(commission * 2).toFixed(2)}</span>
						</div>
						<div class="summary-item">
							<span class="label">Net P&L:</span>
							<span class="value" class:profit={netPnL > 0} class:loss={netPnL < 0}>
								${netPnL.toFixed(2)} ({pnlPercent.toFixed(2)}%)
							</span>
						</div>
						<div class="summary-item">
							<span class="label">Duration:</span>
							<span class="value">{tradeDuration}</span>
						</div>
						{#if showAdvanced && riskRewardRatio > 0}
							<div class="summary-item">
								<span class="label">Risk/Reward:</span>
								<span class="value">1:{riskRewardRatio.toFixed(1)}</span>
							</div>
						{/if}
					</div>
				</div>
				
				<!-- Form Actions -->
				<div class="form-actions">
					<button type="button" class="cancel-button" on:click={handleClose} disabled={loading}>
						Cancel
					</button>
					{#if !trade?.id}
						<button 
							type="button" 
							class="save-continue-button" 
							on:click={(e) => handleSubmit(e, true)}
							disabled={loading}
						>
							<Save size={16} />
							Save & Add Another
						</button>
					{/if}
					<button type="submit" class="submit-button" disabled={loading}>
						{loading ? 'Saving...' : (trade?.id ? 'Update Trade' : 'Save Trade')}
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
		padding: 1rem;
		overflow-y: auto;
	}
	
	.modal {
		background: white;
		border-radius: 12px;
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
		max-width: 700px;
		width: 100%;
		max-height: 90vh;
		overflow-y: auto;
		margin: auto;
	}
	
	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem 2rem;
		border-bottom: 1px solid #e0e0e0;
		position: sticky;
		top: 0;
		background: white;
		z-index: 10;
	}
	
	.modal-header h2 {
		font-size: 1.5rem;
		margin: 0;
	}
	
	.close-button {
		background: none;
		border: none;
		color: #666;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 6px;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.close-button:hover {
		background: #f3f4f6;
		color: #333;
	}
	
	form {
		padding: 2rem;
	}
	
	.error-message, .success-message {
		margin: 0 2rem;
		padding: 0.75rem 1rem;
		border-radius: 6px;
		font-size: 0.875rem;
	}
	
	.error-message {
		background: #fee;
		color: #c00;
		border: 1px solid #fcc;
	}
	
	.success-message {
		background: #f0fdf4;
		color: #166534;
		border: 1px solid #86efac;
	}
	
	.form-section {
		margin-bottom: 2rem;
	}
	
	.form-section h3 {
		font-size: 1rem;
		font-weight: 600;
		color: #666;
		margin-bottom: 1rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.form-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
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
	
	.required {
		color: #ef4444;
	}
	
	input, select, textarea {
		padding: 0.625rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 0.875rem;
		font-family: inherit;
		transition: border-color 0.2s;
	}
	
	input:focus, select:focus, textarea:focus {
		outline: none;
		border-color: #10b981;
	}
	
	input:disabled, select:disabled, textarea:disabled {
		background: #f5f5f5;
		cursor: not-allowed;
	}
	
	input.uppercase {
		text-transform: uppercase;
	}
	
	textarea {
		resize: vertical;
		min-height: 80px;
	}
	
	.side-selector {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.5rem;
	}
	
	.side-button {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 0.625rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		background: white;
		color: #666;
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.side-button:hover {
		border-color: #d0d0d0;
	}
	
	.side-button.active.long {
		background: #f0fdf4;
		border-color: #10b981;
		color: #10b981;
	}
	
	.side-button.active.short {
		background: #fef2f2;
		border-color: #ef4444;
		color: #ef4444;
	}
	
	.toggle-advanced {
		background: none;
		border: none;
		color: #10b981;
		font-size: 0.875rem;
		cursor: pointer;
		padding: 0;
		margin-bottom: 1rem;
		text-decoration: underline;
	}
	
	.toggle-advanced:hover {
		color: #059669;
	}
	
	.commission-input {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.5rem;
	}
	
	.input-with-button {
		display: flex;
		gap: 0.5rem;
	}
	
	.input-with-button input {
		flex: 1;
	}
	
	.calc-button {
		padding: 0.625rem;
		background: #f3f4f6;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		cursor: pointer;
		color: #666;
		transition: all 0.2s;
		display: flex;
		align-items: center;
	}
	
	.calc-button:hover:not(:disabled) {
		background: #e5e7eb;
		color: #333;
	}
	
	.calc-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.pnl-summary {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		padding: 1.5rem;
		border-radius: 8px;
		margin-bottom: 2rem;
	}
	
	.pnl-summary h3 {
		font-size: 1rem;
		font-weight: 600;
		color: #666;
		margin: 0 0 1rem 0;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.summary-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
	}
	
	.summary-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.5rem 0;
		border-bottom: 1px solid #e0e0e0;
	}
	
	.summary-item:last-child {
		border-bottom: none;
	}
	
	.summary-item .label {
		font-size: 0.875rem;
		color: #666;
	}
	
	.summary-item .value {
		font-weight: 600;
		font-size: 1rem;
		color: #333;
	}
	
	.profit {
		color: #10b981;
	}
	
	.loss {
		color: #ef4444;
	}
	
	.form-actions {
		display: flex;
		gap: 1rem;
		justify-content: flex-end;
		padding-top: 1rem;
		border-top: 1px solid #e0e0e0;
	}
	
	.cancel-button, .save-continue-button, .submit-button {
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.cancel-button {
		background: #f3f4f6;
		color: #333;
	}
	
	.cancel-button:hover:not(:disabled) {
		background: #e5e7eb;
	}
	
	.save-continue-button {
		background: white;
		color: #10b981;
		border: 1px solid #10b981;
	}
	
	.save-continue-button:hover:not(:disabled) {
		background: #f0fdf4;
	}
	
	.submit-button {
		background: #10b981;
		color: white;
	}
	
	.submit-button:hover:not(:disabled) {
		background: #059669;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
	}
	
	.submit-button:disabled, .cancel-button:disabled, .save-continue-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
		transform: none;
		box-shadow: none;
	}
	
	@media (max-width: 640px) {
		.form-grid {
			grid-template-columns: 1fr;
		}
		
		.modal {
			margin: 1rem;
			max-height: calc(100vh - 2rem);
		}
		
		form {
			padding: 1.5rem;
		}
		
		.summary-grid {
			grid-template-columns: 1fr;
		}
		
		.form-actions {
			flex-direction: column;
		}
		
		.cancel-button, .save-continue-button, .submit-button {
			width: 100%;
			justify-content: center;
		}
	}
</style>