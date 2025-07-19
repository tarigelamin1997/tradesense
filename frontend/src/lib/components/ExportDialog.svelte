<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Download, FileText, FileSpreadsheet, FileJson, Calendar, Filter, X } from 'lucide-svelte';
	import type { Trade } from '$lib/stores/trades';
	import { TradeExporter } from '$lib/utils/exporters';
	
	export let show = false;
	export let trades: Trade[] = [];
	export let filteredTrades: Trade[] = [];
	
	const dispatch = createEventDispatcher();
	
	let exportFormat: 'csv' | 'excel' | 'json' = 'csv';
	let exportScope: 'all' | 'filtered' | 'selected' | 'dateRange' = 'all';
	let dateFrom = '';
	let dateTo = '';
	let selectedColumns = [
		'symbol', 'side', 'entryPrice', 'exitPrice', 'quantity',
		'pnl', 'entryDate', 'exitDate', 'strategy', 'notes'
	];
	
	const availableColumns = [
		{ value: 'symbol', label: 'Symbol', selected: true },
		{ value: 'side', label: 'Side', selected: true },
		{ value: 'entryPrice', label: 'Entry Price', selected: true },
		{ value: 'exitPrice', label: 'Exit Price', selected: true },
		{ value: 'quantity', label: 'Quantity', selected: true },
		{ value: 'pnl', label: 'P&L', selected: true },
		{ value: 'entryDate', label: 'Entry Date', selected: true },
		{ value: 'exitDate', label: 'Exit Date', selected: true },
		{ value: 'strategy', label: 'Strategy', selected: true },
		{ value: 'notes', label: 'Notes', selected: true }
	];
	
	// Initialize date range to last 30 days
	$: {
		const today = new Date();
		const thirtyDaysAgo = new Date(today);
		thirtyDaysAgo.setDate(today.getDate() - 30);
		
		dateTo = today.toISOString().split('T')[0];
		dateFrom = thirtyDaysAgo.toISOString().split('T')[0];
	}
	
	function handleColumnToggle(column: string) {
		if (selectedColumns.includes(column)) {
			selectedColumns = selectedColumns.filter(c => c !== column);
		} else {
			selectedColumns = [...selectedColumns, column];
		}
	}
	
	function selectAllColumns() {
		selectedColumns = availableColumns.map(c => c.value);
	}
	
	function deselectAllColumns() {
		selectedColumns = [];
	}
	
	function getTradesToExport(): Trade[] {
		switch (exportScope) {
			case 'filtered':
				return filteredTrades;
			case 'dateRange':
				return trades.filter(trade => {
					const tradeDate = new Date(trade.entryDate);
					const from = new Date(dateFrom);
					const to = new Date(dateTo);
					to.setHours(23, 59, 59, 999); // Include entire day
					return tradeDate >= from && tradeDate <= to;
				});
			case 'all':
			default:
				return trades;
		}
	}
	
	function handleExport() {
		const tradesToExport = getTradesToExport();
		
		if (tradesToExport.length === 0) {
			alert('No trades to export with the selected criteria.');
			return;
		}
		
		try {
			TradeExporter.export(tradesToExport, exportFormat, {
				columns: selectedColumns
			});
			
			dispatch('export', {
				format: exportFormat,
				count: tradesToExport.length
			});
			
			handleClose();
		} catch (error) {
			console.error('Export failed:', error);
			alert('Failed to export trades. Please try again.');
		}
	}
	
	function handleClose() {
		show = false;
		dispatch('close');
	}
	
	$: tradesToExportCount = getTradesToExport().length;
</script>

{#if show}
	<div class="modal-backdrop" on:click={handleClose}>
		<div class="modal" on:click|stopPropagation>
			<div class="modal-header">
				<h2>Export Trades</h2>
				<button type="button" class="close-button" on:click={handleClose}>
					<X size={24} />
				</button>
			</div>
			
			<div class="modal-body">
				<!-- Export Format -->
				<div class="section">
					<h3>Format</h3>
					<div class="format-options">
						<label class="format-option">
							<input
								type="radio"
								name="format"
								value="csv"
								bind:group={exportFormat}
							/>
							<div class="format-card">
								<FileText size={24} class="format-icon csv" />
								<span class="format-name">CSV</span>
								<span class="format-desc">Excel, Google Sheets</span>
							</div>
						</label>
						
						<label class="format-option">
							<input
								type="radio"
								name="format"
								value="excel"
								bind:group={exportFormat}
							/>
							<div class="format-card">
								<FileSpreadsheet size={24} class="format-icon excel" />
								<span class="format-name">Excel</span>
								<span class="format-desc">Microsoft Excel</span>
							</div>
						</label>
						
						<label class="format-option">
							<input
								type="radio"
								name="format"
								value="json"
								bind:group={exportFormat}
							/>
							<div class="format-card">
								<FileJson size={24} class="format-icon json" />
								<span class="format-name">JSON</span>
								<span class="format-desc">API, Backup</span>
							</div>
						</label>
					</div>
				</div>
				
				<!-- Export Scope -->
				<div class="section">
					<h3>Data Range</h3>
					<div class="scope-options">
						<label class="scope-option">
							<input
								type="radio"
								name="scope"
								value="all"
								bind:group={exportScope}
							/>
							<span>All Trades ({trades.length})</span>
						</label>
						
						{#if filteredTrades.length !== trades.length}
							<label class="scope-option">
								<input
									type="radio"
									name="scope"
									value="filtered"
									bind:group={exportScope}
								/>
								<span>Filtered Trades ({filteredTrades.length})</span>
							</label>
						{/if}
						
						<label class="scope-option">
							<input
								type="radio"
								name="scope"
								value="dateRange"
								bind:group={exportScope}
							/>
							<span>Date Range</span>
						</label>
					</div>
					
					{#if exportScope === 'dateRange'}
						<div class="date-range">
							<div class="date-input">
								<label for="dateFrom">From</label>
								<input
									id="dateFrom"
									type="date"
									bind:value={dateFrom}
								/>
							</div>
							<div class="date-input">
								<label for="dateTo">To</label>
								<input
									id="dateTo"
									type="date"
									bind:value={dateTo}
								/>
							</div>
						</div>
					{/if}
				</div>
				
				<!-- Column Selection -->
				<div class="section">
					<div class="section-header">
						<h3>Columns</h3>
						<div class="column-actions">
							<button type="button" class="text-button" on:click={selectAllColumns}>
								Select All
							</button>
							<button type="button" class="text-button" on:click={deselectAllColumns}>
								Deselect All
							</button>
						</div>
					</div>
					
					<div class="columns-grid">
						{#each availableColumns as column}
							<label class="column-option">
								<input
									type="checkbox"
									checked={selectedColumns.includes(column.value)}
									on:change={() => handleColumnToggle(column.value)}
								/>
								<span>{column.label}</span>
							</label>
						{/each}
					</div>
				</div>
				
				<!-- Export Summary -->
				<div class="export-summary">
					<div class="summary-icon">
						<Download size={20} />
					</div>
					<div class="summary-text">
						Export <strong>{tradesToExportCount}</strong> trades 
						as <strong>{exportFormat.toUpperCase()}</strong> 
						with <strong>{selectedColumns.length}</strong> columns
					</div>
				</div>
			</div>
			
			<div class="modal-footer">
				<button type="button" class="cancel-button" on:click={handleClose}>
					Cancel
				</button>
				<button 
					type="button" 
					class="export-button" 
					on:click={handleExport}
					disabled={selectedColumns.length === 0 || tradesToExportCount === 0}
				>
					<Download size={16} />
					Export
				</button>
			</div>
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
	}
	
	.modal {
		background: white;
		border-radius: 12px;
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
		max-width: 600px;
		width: 100%;
		max-height: 90vh;
		display: flex;
		flex-direction: column;
	}
	
	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		border-bottom: 1px solid #e0e0e0;
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
	
	.modal-body {
		flex: 1;
		overflow-y: auto;
		padding: 1.5rem;
	}
	
	.section {
		margin-bottom: 2rem;
	}
	
	.section:last-child {
		margin-bottom: 0;
	}
	
	.section h3 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 1rem;
		color: #333;
	}
	
	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}
	
	.section-header h3 {
		margin: 0;
	}
	
	.format-options {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1rem;
	}
	
	.format-option {
		position: relative;
	}
	
	.format-option input {
		position: absolute;
		opacity: 0;
	}
	
	.format-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		padding: 1.5rem 1rem;
		border: 2px solid #e0e0e0;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.2s;
		text-align: center;
	}
	
	.format-option input:checked + .format-card {
		border-color: #10b981;
		background: #f0fdf4;
	}
	
	.format-card:hover {
		border-color: #d0d0d0;
	}
	
	:global(.format-icon) {
		stroke-width: 1.5;
	}
	
	:global(.format-icon.csv) {
		color: #10b981;
	}
	
	:global(.format-icon.excel) {
		color: #16a34a;
	}
	
	:global(.format-icon.json) {
		color: #f59e0b;
	}
	
	.format-name {
		font-weight: 600;
		color: #333;
	}
	
	.format-desc {
		font-size: 0.75rem;
		color: #666;
	}
	
	.scope-options {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.scope-option {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
	}
	
	.scope-option input {
		cursor: pointer;
	}
	
	.scope-option span {
		color: #333;
	}
	
	.date-range {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-top: 1rem;
		padding: 1rem;
		background: #f9f9f9;
		border-radius: 6px;
	}
	
	.date-input {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.date-input label {
		font-size: 0.875rem;
		color: #666;
	}
	
	.date-input input {
		padding: 0.5rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 0.875rem;
	}
	
	.column-actions {
		display: flex;
		gap: 1rem;
	}
	
	.text-button {
		background: none;
		border: none;
		color: #10b981;
		font-size: 0.875rem;
		cursor: pointer;
		padding: 0;
		text-decoration: underline;
	}
	
	.text-button:hover {
		color: #059669;
	}
	
	.columns-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 0.75rem;
	}
	
	.column-option {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
	}
	
	.column-option input {
		cursor: pointer;
	}
	
	.export-summary {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		background: #f0fdf4;
		border: 1px solid #86efac;
		border-radius: 8px;
		color: #166534;
	}
	
	.summary-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		background: white;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	.summary-text {
		font-size: 0.875rem;
		line-height: 1.5;
	}
	
	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: 1rem;
		padding: 1.5rem;
		border-top: 1px solid #e0e0e0;
	}
	
	.cancel-button, .export-button {
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
	
	.cancel-button:hover {
		background: #e5e7eb;
	}
	
	.export-button {
		background: #10b981;
		color: white;
	}
	
	.export-button:hover:not(:disabled) {
		background: #059669;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
	}
	
	.export-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
		transform: none;
		box-shadow: none;
	}
	
	@media (max-width: 640px) {
		.format-options {
			grid-template-columns: 1fr;
		}
		
		.columns-grid {
			grid-template-columns: 1fr;
		}
		
		.date-range {
			grid-template-columns: 1fr;
		}
	}
</style>