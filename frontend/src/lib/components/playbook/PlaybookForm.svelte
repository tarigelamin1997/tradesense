<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { X, Plus, Minus } from 'lucide-svelte';
	
	export let playbook: any = null;
	
	const dispatch = createEventDispatcher();
	
	// Form data
	let formData = {
		title: '',
		strategy_type: 'daytrading',
		timeframe: '',
		market_conditions: '',
		entry_rules: [''],
		exit_rules: [''],
		risk_management: '',
		position_sizing: '',
		indicators: [],
		notes: '',
		backtest_results: {
			win_rate: 0,
			profit_factor: 0,
			avg_win: 0,
			avg_loss: 0,
			max_drawdown: 0
		},
		tags: [],
		is_active: true
	};
	
	let tagInput = '';
	let indicatorInput = '';
	let showBacktest = false;
	
	// Initialize form with existing data if editing
	if (playbook) {
		formData = {
			...playbook,
			entry_rules: [...playbook.entry_rules],
			exit_rules: [...playbook.exit_rules],
			indicators: [...playbook.indicators],
			tags: [...playbook.tags],
			backtest_results: playbook.backtest_results || {
				win_rate: 0,
				profit_factor: 0,
				avg_win: 0,
				avg_loss: 0,
				max_drawdown: 0
			}
		};
		showBacktest = !!playbook.backtest_results;
	}
	
	function addEntryRule() {
		formData.entry_rules = [...formData.entry_rules, ''];
	}
	
	function removeEntryRule(index: number) {
		formData.entry_rules = formData.entry_rules.filter((_, i) => i !== index);
	}
	
	function addExitRule() {
		formData.exit_rules = [...formData.exit_rules, ''];
	}
	
	function removeExitRule(index: number) {
		formData.exit_rules = formData.exit_rules.filter((_, i) => i !== index);
	}
	
	function addIndicator() {
		if (indicatorInput.trim() && !formData.indicators.includes(indicatorInput.trim())) {
			formData.indicators = [...formData.indicators, indicatorInput.trim()];
			indicatorInput = '';
		}
	}
	
	function removeIndicator(indicator: string) {
		formData.indicators = formData.indicators.filter(i => i !== indicator);
	}
	
	function addTag() {
		if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
			formData.tags = [...formData.tags, tagInput.trim()];
			tagInput = '';
		}
	}
	
	function removeTag(tag: string) {
		formData.tags = formData.tags.filter(t => t !== tag);
	}
	
	function handleSubmit() {
		// Filter out empty rules
		const cleanedData = {
			...formData,
			entry_rules: formData.entry_rules.filter(rule => rule.trim()),
			exit_rules: formData.exit_rules.filter(rule => rule.trim()),
			backtest_results: showBacktest ? formData.backtest_results : undefined,
			updated_at: new Date().toISOString()
		};
		
		dispatch('save', { playbook: cleanedData });
	}
	
	function handleCancel() {
		dispatch('cancel');
	}
</script>

<div class="form-container">
	<div class="form-card card">
		<div class="form-header">
			<h2>{playbook ? 'Edit' : 'New'} Strategy</h2>
			<button type="button" class="close-button" on:click={handleCancel}>
				<X size={20} />
			</button>
		</div>
		
		<form on:submit|preventDefault={handleSubmit}>
			<!-- Basic Information -->
			<div class="form-section">
				<h3>Basic Information</h3>
				
				<div class="form-group">
					<label for="title">Strategy Name</label>
					<input
						id="title"
						type="text"
						bind:value={formData.title}
						placeholder="e.g., Morning Gap Strategy"
						required
					/>
				</div>
				
				<div class="form-row">
					<div class="form-group">
						<label for="strategy_type">Strategy Type</label>
						<select id="strategy_type" bind:value={formData.strategy_type}>
							<option value="scalping">Scalping</option>
							<option value="daytrading">Day Trading</option>
							<option value="swing">Swing Trading</option>
							<option value="position">Position Trading</option>
							<option value="other">Other</option>
						</select>
					</div>
					
					<div class="form-group">
						<label for="timeframe">Timeframe</label>
						<input
							id="timeframe"
							type="text"
							bind:value={formData.timeframe}
							placeholder="e.g., 5min, 15min"
							required
						/>
					</div>
				</div>
				
				<div class="form-group">
					<label for="market_conditions">Market Conditions</label>
					<textarea
						id="market_conditions"
						bind:value={formData.market_conditions}
						placeholder="Describe when this strategy works best..."
						rows="3"
						required
					/>
				</div>
			</div>
			
			<!-- Entry Rules -->
			<div class="form-section">
				<h3>Entry Rules</h3>
				
				{#each formData.entry_rules as rule, index}
					<div class="rule-input">
						<span class="rule-number">{index + 1}.</span>
						<input
							type="text"
							bind:value={formData.entry_rules[index]}
							placeholder="Enter entry rule..."
						/>
						<button
							type="button"
							class="remove-button"
							on:click={() => removeEntryRule(index)}
							disabled={formData.entry_rules.length === 1}
						>
							<Minus size={16} />
						</button>
					</div>
				{/each}
				
				<button type="button" class="add-button" on:click={addEntryRule}>
					<Plus size={16} />
					Add Entry Rule
				</button>
			</div>
			
			<!-- Exit Rules -->
			<div class="form-section">
				<h3>Exit Rules</h3>
				
				{#each formData.exit_rules as rule, index}
					<div class="rule-input">
						<span class="rule-number">{index + 1}.</span>
						<input
							type="text"
							bind:value={formData.exit_rules[index]}
							placeholder="Enter exit rule..."
						/>
						<button
							type="button"
							class="remove-button"
							on:click={() => removeExitRule(index)}
							disabled={formData.exit_rules.length === 1}
						>
							<Minus size={16} />
						</button>
					</div>
				{/each}
				
				<button type="button" class="add-button" on:click={addExitRule}>
					<Plus size={16} />
					Add Exit Rule
				</button>
			</div>
			
			<!-- Risk Management -->
			<div class="form-section">
				<h3>Risk Management</h3>
				
				<div class="form-group">
					<label for="risk_management">Risk Management Rules</label>
					<textarea
						id="risk_management"
						bind:value={formData.risk_management}
						placeholder="e.g., 1% account risk per trade, max 3 concurrent positions"
						rows="2"
						required
					/>
				</div>
				
				<div class="form-group">
					<label for="position_sizing">Position Sizing</label>
					<input
						id="position_sizing"
						type="text"
						bind:value={formData.position_sizing}
						placeholder="e.g., Risk / (Entry - Stop Loss) = Share size"
						required
					/>
				</div>
			</div>
			
			<!-- Indicators -->
			<div class="form-section">
				<h3>Indicators</h3>
				
				<div class="indicator-input">
					<input
						type="text"
						bind:value={indicatorInput}
						on:keypress={(e) => e.key === 'Enter' && (e.preventDefault(), addIndicator())}
						placeholder="Add indicator (e.g., RSI, MACD, VWAP)"
					/>
					<button type="button" on:click={addIndicator} class="add-tag-button">
						Add
					</button>
				</div>
				
				{#if formData.indicators.length > 0}
					<div class="tags">
						{#each formData.indicators as indicator}
							<span class="tag removable">
								{indicator}
								<button type="button" on:click={() => removeIndicator(indicator)}>×</button>
							</span>
						{/each}
					</div>
				{/if}
			</div>
			
			<!-- Backtest Results -->
			<div class="form-section">
				<label class="checkbox-label">
					<input
						type="checkbox"
						bind:checked={showBacktest}
					/>
					Include Backtest Results
				</label>
				
				{#if showBacktest}
					<div class="backtest-grid">
						<div class="form-group">
							<label for="win_rate">Win Rate (%)</label>
							<input
								id="win_rate"
								type="number"
								step="0.1"
								min="0"
								max="100"
								bind:value={formData.backtest_results.win_rate}
							/>
						</div>
						
						<div class="form-group">
							<label for="profit_factor">Profit Factor</label>
							<input
								id="profit_factor"
								type="number"
								step="0.1"
								min="0"
								bind:value={formData.backtest_results.profit_factor}
							/>
						</div>
						
						<div class="form-group">
							<label for="avg_win">Avg Win ($)</label>
							<input
								id="avg_win"
								type="number"
								step="1"
								min="0"
								bind:value={formData.backtest_results.avg_win}
							/>
						</div>
						
						<div class="form-group">
							<label for="avg_loss">Avg Loss ($)</label>
							<input
								id="avg_loss"
								type="number"
								step="1"
								min="0"
								bind:value={formData.backtest_results.avg_loss}
							/>
						</div>
						
						<div class="form-group">
							<label for="max_drawdown">Max Drawdown (%)</label>
							<input
								id="max_drawdown"
								type="number"
								step="0.1"
								min="0"
								max="100"
								bind:value={formData.backtest_results.max_drawdown}
							/>
						</div>
					</div>
				{/if}
			</div>
			
			<!-- Additional Notes -->
			<div class="form-section">
				<h3>Additional Notes</h3>
				
				<div class="form-group">
					<textarea
						bind:value={formData.notes}
						placeholder="Any additional notes, observations, or reminders..."
						rows="4"
					/>
				</div>
			</div>
			
			<!-- Tags -->
			<div class="form-section">
				<h3>Tags</h3>
				
				<div class="tag-input-container">
					<input
						type="text"
						bind:value={tagInput}
						on:keypress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
						placeholder="Add tags..."
					/>
					<button type="button" on:click={addTag} class="add-tag-button">
						Add
					</button>
				</div>
				
				{#if formData.tags.length > 0}
					<div class="tags">
						{#each formData.tags as tag}
							<span class="tag removable">
								{tag}
								<button type="button" on:click={() => removeTag(tag)}>×</button>
							</span>
						{/each}
					</div>
				{/if}
			</div>
			
			<!-- Status -->
			<div class="form-section">
				<label class="checkbox-label">
					<input
						type="checkbox"
						bind:checked={formData.is_active}
					/>
					Active Strategy
				</label>
			</div>
			
			<!-- Form Actions -->
			<div class="form-actions">
				<button type="button" on:click={handleCancel} class="cancel-button">
					Cancel
				</button>
				<button type="submit" class="save-button">
					{playbook ? 'Update' : 'Create'} Strategy
				</button>
			</div>
		</form>
	</div>
</div>

<style>
	.form-container {
		max-width: 900px;
		margin: 0 auto;
	}
	
	.form-card {
		padding: 2rem;
	}
	
	.form-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid #e0e0e0;
	}
	
	.form-header h2 {
		font-size: 1.5rem;
		margin: 0;
	}
	
	.close-button {
		background: none;
		border: none;
		color: #666;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 4px;
		transition: all 0.2s;
	}
	
	.close-button:hover {
		background: #f3f4f6;
		color: #333;
	}
	
	.form-section {
		margin-bottom: 2rem;
	}
	
	.form-section h3 {
		font-size: 1.125rem;
		margin-bottom: 1rem;
		color: #333;
	}
	
	.form-group {
		margin-bottom: 1.5rem;
	}
	
	.form-group label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
		color: #333;
	}
	
	.form-group input,
	.form-group select,
	.form-group textarea {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 1rem;
		font-family: inherit;
	}
	
	.form-group input:focus,
	.form-group select:focus,
	.form-group textarea:focus {
		outline: none;
		border-color: #10b981;
	}
	
	.form-row {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
	}
	
	.rule-input {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.75rem;
	}
	
	.rule-number {
		font-weight: 600;
		color: #666;
		min-width: 20px;
	}
	
	.rule-input input {
		flex: 1;
		padding: 0.75rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 1rem;
	}
	
	.rule-input input:focus {
		outline: none;
		border-color: #10b981;
	}
	
	.remove-button {
		padding: 0.5rem;
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
	
	.remove-button:hover:not(:disabled) {
		background: #fef2f2;
		border-color: #fecaca;
		color: #ef4444;
	}
	
	.remove-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.add-button {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: #f3f4f6;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		color: #333;
		cursor: pointer;
		font-size: 0.875rem;
		transition: all 0.2s;
	}
	
	.add-button:hover {
		background: #e5e7eb;
		border-color: #d1d5db;
	}
	
	.indicator-input,
	.tag-input-container {
		display: flex;
		gap: 0.5rem;
	}
	
	.add-tag-button {
		padding: 0.75rem 1rem;
		background: #f3f4f6;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.add-tag-button:hover {
		background: #e5e7eb;
		border-color: #d1d5db;
	}
	
	.tags {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
		margin-top: 0.75rem;
	}
	
	.tag {
		background: #e0f2fe;
		color: #0369a1;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.875rem;
	}
	
	.tag.removable {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding-right: 0.5rem;
	}
	
	.tag.removable button {
		background: none;
		border: none;
		color: #0369a1;
		cursor: pointer;
		font-size: 1.25rem;
		line-height: 1;
		padding: 0;
		opacity: 0.7;
	}
	
	.tag.removable button:hover {
		opacity: 1;
	}
	
	.checkbox-label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 500;
		color: #333;
		cursor: pointer;
		margin-bottom: 1rem;
	}
	
	.backtest-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
		margin-top: 1rem;
	}
	
	.form-actions {
		display: flex;
		gap: 1rem;
		justify-content: flex-end;
		margin-top: 2rem;
		padding-top: 2rem;
		border-top: 1px solid #e0e0e0;
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
	
	.cancel-button:hover {
		background: #e5e7eb;
	}
	
	.save-button {
		padding: 0.75rem 1.5rem;
		background: #10b981;
		color: white;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 1rem;
		transition: background 0.2s;
	}
	
	.save-button:hover {
		background: #059669;
	}
	
	@media (max-width: 640px) {
		.form-container {
			padding: 0 1rem;
		}
		
		.form-card {
			padding: 1.5rem;
		}
		
		.form-row {
			grid-template-columns: 1fr;
		}
		
		.backtest-grid {
			grid-template-columns: 1fr 1fr;
		}
	}
</style>