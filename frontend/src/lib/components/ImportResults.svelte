<script lang="ts">
	import { CheckCircle, XCircle, AlertCircle, Download, RefreshCw } from 'lucide-svelte';
	import type { ImportResult, ImportError } from '$lib/api/uploads';
	
	export let result: ImportResult;
	export let onRetry: () => void = () => {};
	export let onNewImport: () => void = () => {};
	
	$: successRate = result.imported > 0 
		? Math.round((result.imported / (result.imported + result.failed)) * 100)
		: 0;
	
	function downloadErrorReport() {
		const errors = result.errors.map(e => ({
			row: e.row,
			message: e.message,
			data: JSON.stringify(e.data || {})
		}));
		
		const csv = [
			['Row', 'Error Message', 'Data'],
			...errors.map(e => [e.row, e.message, e.data])
		].map(row => row.join(',')).join('\n');
		
		const blob = new Blob([csv], { type: 'text/csv' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = 'import-errors.csv';
		a.click();
		URL.revokeObjectURL(url);
	}
</script>

<div class="import-results">
	<div class="results-header">
		{#if result.success}
			<CheckCircle size={48} class="icon-success" />
			<h2>Import Complete!</h2>
		{:else if result.imported > 0}
			<AlertCircle size={48} class="icon-warning" />
			<h2>Partial Import Complete</h2>
		{:else}
			<XCircle size={48} class="icon-error" />
			<h2>Import Failed</h2>
		{/if}
		
		<p class="message">{result.message}</p>
	</div>
	
	<div class="stats-grid">
		<div class="stat-card success">
			<CheckCircle size={24} />
			<div class="stat-content">
				<span class="stat-value">{result.imported}</span>
				<span class="stat-label">Trades Imported</span>
			</div>
		</div>
		
		<div class="stat-card error">
			<XCircle size={24} />
			<div class="stat-content">
				<span class="stat-value">{result.failed}</span>
				<span class="stat-label">Failed Imports</span>
			</div>
		</div>
		
		<div class="stat-card neutral">
			<div class="progress-ring">
				<svg width="60" height="60">
					<circle
						cx="30"
						cy="30"
						r="25"
						stroke="#e0e0e0"
						stroke-width="5"
						fill="none"
					/>
					<circle
						cx="30"
						cy="30"
						r="25"
						stroke="#10b981"
						stroke-width="5"
						fill="none"
						stroke-dasharray={`${successRate * 1.57} 157`}
						stroke-dashoffset="0"
						transform="rotate(-90 30 30)"
						class="progress-circle"
					/>
				</svg>
				<span class="progress-text">{successRate}%</span>
			</div>
			<span class="stat-label">Success Rate</span>
		</div>
	</div>
	
	{#if result.errors.length > 0}
		<div class="errors-section">
			<div class="errors-header">
				<h3>Import Errors ({result.errors.length})</h3>
				<button type="button" class="btn-ghost" on:click={downloadErrorReport}>
					<Download size={16} />
					Download Error Report
				</button>
			</div>
			
			<div class="error-list">
				{#each result.errors.slice(0, 10) as error}
					<div class="error-item">
						<div class="error-row">Row {error.row}</div>
						<div class="error-message">{error.message}</div>
						{#if error.data}
							<details class="error-data">
								<summary>View data</summary>
								<pre>{JSON.stringify(error.data, null, 2)}</pre>
							</details>
						{/if}
					</div>
				{/each}
				
				{#if result.errors.length > 10}
					<div class="more-errors">
						... and {result.errors.length - 10} more errors
					</div>
				{/if}
			</div>
		</div>
	{/if}
	
	<div class="actions">
		{#if result.failed > 0}
			<button type="button" class="btn-secondary" on:click={onRetry}>
				<RefreshCw size={16} />
				Retry Failed Imports
			</button>
		{/if}
		<button type="button" class="btn-primary" on:click={onNewImport}>
			New Import
		</button>
	</div>
</div>

<style>
	.import-results {
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		padding: 2rem;
		max-width: 800px;
		margin: 0 auto;
	}
	
	.results-header {
		text-align: center;
		margin-bottom: 2rem;
	}
	
	.results-header h2 {
		font-size: 1.5rem;
		font-weight: 600;
		margin: 1rem 0 0.5rem 0;
	}
	
	.message {
		color: #666;
		margin: 0;
	}
	
	:global(.icon-success) {
		color: #10b981;
	}
	
	:global(.icon-warning) {
		color: #f59e0b;
	}
	
	:global(.icon-error) {
		color: #ef4444;
	}
	
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.stat-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
		padding: 1.5rem;
		border-radius: 8px;
		background: #f9f9f9;
	}
	
	.stat-card.success {
		background: #f0fdf4;
		color: #166534;
	}
	
	.stat-card.error {
		background: #fef2f2;
		color: #991b1b;
	}
	
	.stat-card.neutral {
		background: #f9f9f9;
		color: #333;
	}
	
	.stat-content {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.25rem;
	}
	
	.stat-value {
		font-size: 2rem;
		font-weight: 700;
		line-height: 1;
	}
	
	.stat-label {
		font-size: 0.875rem;
		opacity: 0.8;
	}
	
	.progress-ring {
		position: relative;
		width: 60px;
		height: 60px;
	}
	
	.progress-circle {
		transition: stroke-dasharray 0.5s ease;
	}
	
	.progress-text {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		font-size: 1rem;
		font-weight: 600;
	}
	
	.errors-section {
		background: #fef2f2;
		border: 1px solid #fecaca;
		border-radius: 8px;
		padding: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.errors-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
		flex-wrap: wrap;
		gap: 1rem;
	}
	
	.errors-header h3 {
		font-size: 1.125rem;
		font-weight: 600;
		margin: 0;
		color: #991b1b;
	}
	
	.btn-ghost {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: white;
		border: 1px solid #fecaca;
		border-radius: 6px;
		font-size: 0.875rem;
		color: #991b1b;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.btn-ghost:hover {
		background: #fee;
		border-color: #f87171;
	}
	
	.error-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.error-item {
		background: white;
		border: 1px solid #fecaca;
		border-radius: 6px;
		padding: 1rem;
	}
	
	.error-row {
		font-weight: 600;
		color: #991b1b;
		font-size: 0.875rem;
		margin-bottom: 0.25rem;
	}
	
	.error-message {
		color: #666;
		font-size: 0.875rem;
		margin-bottom: 0.5rem;
	}
	
	.error-data {
		margin-top: 0.5rem;
		font-size: 0.75rem;
	}
	
	.error-data summary {
		cursor: pointer;
		color: #991b1b;
		font-weight: 500;
	}
	
	.error-data pre {
		margin-top: 0.5rem;
		padding: 0.5rem;
		background: #fafafa;
		border-radius: 4px;
		overflow-x: auto;
		font-size: 0.75rem;
		line-height: 1.4;
	}
	
	.more-errors {
		text-align: center;
		padding: 1rem;
		color: #991b1b;
		font-size: 0.875rem;
		font-style: italic;
	}
	
	.actions {
		display: flex;
		justify-content: center;
		gap: 1rem;
		margin-top: 2rem;
	}
	
	.btn-primary, .btn-secondary {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 6px;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.btn-primary {
		background: #10b981;
		color: white;
	}
	
	.btn-primary:hover {
		background: #059669;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
	}
	
	.btn-secondary {
		background: #f3f4f6;
		color: #333;
		border: 1px solid #e5e7eb;
	}
	
	.btn-secondary:hover {
		background: #e5e7eb;
		transform: translateY(-1px);
	}
	
	@media (max-width: 768px) {
		.import-results {
			padding: 1.5rem;
		}
		
		.stats-grid {
			grid-template-columns: 1fr;
			gap: 1rem;
		}
		
		.actions {
			flex-direction: column;
		}
		
		.btn-primary, .btn-secondary {
			width: 100%;
			justify-content: center;
		}
	}
</style>