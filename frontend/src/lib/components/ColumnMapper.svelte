<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Info, AlertCircle, CheckCircle } from 'lucide-svelte';
	import type { ColumnMapping } from '$lib/api/uploads';
	
	const dispatch = createEventDispatcher();
	
	export let fileColumns: string[] = [];
	export let dataPreview: any[] = [];
	export let suggestedMapping: ColumnMapping = {};
	export let currentMapping: ColumnMapping = {};
	
	// System fields with descriptions
	const systemFields = [
		{ value: 'symbol', label: 'Symbol', required: true, description: 'Trading symbol (e.g., AAPL, TSLA)' },
		{ value: 'side', label: 'Side', required: true, description: 'Trade direction (long/short)' },
		{ value: 'entry_price', label: 'Entry Price', required: true, description: 'Price at entry' },
		{ value: 'exit_price', label: 'Exit Price', required: true, description: 'Price at exit' },
		{ value: 'quantity', label: 'Quantity', required: true, description: 'Number of shares/contracts' },
		{ value: 'entry_date', label: 'Entry Date', required: true, description: 'Date/time of entry' },
		{ value: 'exit_date', label: 'Exit Date', required: true, description: 'Date/time of exit' },
		{ value: 'pnl', label: 'P&L', required: false, description: 'Profit/Loss (will be calculated if not provided)' },
		{ value: 'strategy', label: 'Strategy', required: false, description: 'Trading strategy used' },
		{ value: 'notes', label: 'Notes', required: false, description: 'Additional notes or comments' },
		{ value: '', label: 'Skip this column', required: false, description: 'Do not import this column' }
	];
	
	// Initialize mapping with suggestions
	let mapping: ColumnMapping = { ...suggestedMapping, ...currentMapping };
	
	// Track which required fields are mapped
	$: requiredFields = systemFields.filter(f => f.required);
	$: mappedRequiredFields = requiredFields.filter(f => 
		Object.values(mapping).includes(f.value)
	);
	$: allRequiredMapped = mappedRequiredFields.length === requiredFields.length;
	
	// Get sample values for a column
	function getSampleValues(column: string): string[] {
		const values = dataPreview
			.map(row => row[column])
			.filter(v => v !== null && v !== undefined && v !== '')
			.slice(0, 3);
		return [...new Set(values)]; // Unique values only
	}
	
	// Handle mapping change
	function handleMappingChange(fileColumn: string, systemField: string) {
		if (systemField === '') {
			// Remove mapping
			const newMapping = { ...mapping };
			delete newMapping[fileColumn];
			mapping = newMapping;
		} else {
			// Check if this system field is already mapped to another column
			const existingColumn = Object.entries(mapping).find(
				([col, field]) => field === systemField && col !== fileColumn
			);
			
			if (existingColumn) {
				// Remove the existing mapping
				const newMapping = { ...mapping };
				delete newMapping[existingColumn[0]];
				newMapping[fileColumn] = systemField;
				mapping = newMapping;
			} else {
				mapping = { ...mapping, [fileColumn]: systemField };
			}
		}
		
		dispatch('change', { mapping });
	}
	
	// Apply suggested mappings
	function applySuggestions() {
		mapping = { ...suggestedMapping };
		dispatch('change', { mapping });
	}
	
	// Clear all mappings
	function clearMappings() {
		mapping = {};
		dispatch('change', { mapping });
	}
</script>

<div class="column-mapper">
	<div class="mapper-header">
		<h3>Map Your Columns</h3>
		<p>Match your file columns to the system fields</p>
		
		<div class="actions">
			{#if Object.keys(suggestedMapping).length > 0}
				<button type="button" class="btn-secondary" on:click={applySuggestions}>
					Apply Suggestions
				</button>
			{/if}
			<button type="button" class="btn-ghost" on:click={clearMappings}>
				Clear All
			</button>
		</div>
	</div>
	
	{#if !allRequiredMapped}
		<div class="warning-banner">
			<AlertCircle size={20} />
			<span>
				Please map all required fields: 
				{requiredFields
					.filter(f => !Object.values(mapping).includes(f.value))
					.map(f => f.label)
					.join(', ')}
			</span>
		</div>
	{:else}
		<div class="success-banner">
			<CheckCircle size={20} />
			<span>All required fields are mapped!</span>
		</div>
	{/if}
	
	<div class="mapping-grid">
		<div class="grid-header">
			<div>Your Column</div>
			<div>Maps To</div>
			<div>Sample Values</div>
		</div>
		
		{#each fileColumns as column}
			<div class="mapping-row">
				<div class="column-name">
					<span class="name">{column}</span>
					{#if suggestedMapping[column] && !mapping[column]}
						<span class="suggestion">
							<Info size={14} />
							Suggested: {suggestedMapping[column]}
						</span>
					{/if}
				</div>
				
				<div class="mapping-select">
					<select
						value={mapping[column] || ''}
						on:change={(e) => handleMappingChange(column, e.currentTarget.value)}
					>
						<option value="">Select field...</option>
						{#each systemFields as field}
							<option 
								value={field.value}
								disabled={field.value !== '' && field.value !== mapping[column] && Object.values(mapping).includes(field.value)}
							>
								{field.label}
								{#if field.required}*{/if}
								{#if field.value !== '' && field.value !== mapping[column] && Object.values(mapping).includes(field.value)}
									(already mapped)
								{/if}
							</option>
						{/each}
					</select>
					
					{#if mapping[column]}
						{@const field = systemFields.find(f => f.value === mapping[column])}
						{#if field?.description}
							<p class="field-description">{field.description}</p>
						{/if}
					{/if}
				</div>
				
				<div class="sample-values">
					{#each getSampleValues(column) as value}
						<span class="sample">{value}</span>
					{/each}
				</div>
			</div>
		{/each}
	</div>
	
	<div class="legend">
		<p><span class="required">*</span> Required fields</p>
		<p><Info size={14} /> Suggested mappings are based on column names</p>
	</div>
</div>

<style>
	.column-mapper {
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		padding: 1.5rem;
	}
	
	.mapper-header {
		margin-bottom: 1.5rem;
	}
	
	.mapper-header h3 {
		font-size: 1.25rem;
		font-weight: 600;
		margin: 0 0 0.5rem 0;
	}
	
	.mapper-header p {
		color: #666;
		margin: 0 0 1rem 0;
	}
	
	.actions {
		display: flex;
		gap: 0.5rem;
	}
	
	.btn-secondary, .btn-ghost {
		padding: 0.5rem 1rem;
		border-radius: 6px;
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.2s;
		border: none;
	}
	
	.btn-secondary {
		background: #10b981;
		color: white;
	}
	
	.btn-secondary:hover {
		background: #059669;
	}
	
	.btn-ghost {
		background: #f3f4f6;
		color: #666;
	}
	
	.btn-ghost:hover {
		background: #e5e7eb;
	}
	
	.warning-banner, .success-banner {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 1rem;
		border-radius: 6px;
		margin-bottom: 1.5rem;
		font-size: 0.875rem;
	}
	
	.warning-banner {
		background: #fffbeb;
		border: 1px solid #fde68a;
		color: #92400e;
	}
	
	.success-banner {
		background: #f0fdf4;
		border: 1px solid #86efac;
		color: #166534;
	}
	
	.mapping-grid {
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		overflow: hidden;
	}
	
	.grid-header {
		display: grid;
		grid-template-columns: 1fr 1.5fr 1fr;
		gap: 1rem;
		padding: 1rem;
		background: #f9f9f9;
		font-weight: 600;
		font-size: 0.875rem;
		color: #666;
		border-bottom: 1px solid #e0e0e0;
	}
	
	.mapping-row {
		display: grid;
		grid-template-columns: 1fr 1.5fr 1fr;
		gap: 1rem;
		padding: 1rem;
		border-bottom: 1px solid #f0f0f0;
		align-items: start;
	}
	
	.mapping-row:last-child {
		border-bottom: none;
	}
	
	.column-name {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	
	.column-name .name {
		font-weight: 500;
		color: #333;
	}
	
	.suggestion {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.75rem;
		color: #10b981;
	}
	
	.mapping-select {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.mapping-select select {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 0.875rem;
		background: white;
		cursor: pointer;
	}
	
	.mapping-select select:focus {
		outline: none;
		border-color: #10b981;
	}
	
	.field-description {
		font-size: 0.75rem;
		color: #666;
		margin: 0;
		font-style: italic;
	}
	
	.sample-values {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
	}
	
	.sample {
		padding: 0.25rem 0.5rem;
		background: #f3f4f6;
		border-radius: 4px;
		font-size: 0.75rem;
		color: #666;
		max-width: 150px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.legend {
		display: flex;
		gap: 2rem;
		margin-top: 1rem;
		padding-top: 1rem;
		border-top: 1px solid #f0f0f0;
		font-size: 0.875rem;
		color: #666;
	}
	
	.legend p {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin: 0;
	}
	
	.required {
		color: #ef4444;
		font-weight: 600;
	}
	
	@media (max-width: 768px) {
		.grid-header, .mapping-row {
			grid-template-columns: 1fr;
			gap: 0.5rem;
		}
		
		.grid-header > div:not(:first-child),
		.mapping-row > div:not(:first-child) {
			padding-left: 1rem;
		}
		
		.grid-header {
			display: none;
		}
		
		.mapping-row {
			padding: 1rem 0.75rem;
		}
		
		.sample-values {
			margin-top: 0.5rem;
		}
	}
</style>