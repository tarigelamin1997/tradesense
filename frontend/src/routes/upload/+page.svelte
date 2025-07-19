<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { get } from 'svelte/store';
	import { isAuthenticated } from '$lib/api/auth.js';
	import { uploadsApi, type ColumnMapping } from '$lib/api/uploads.js';
	import { uploadStore } from '$lib/stores/upload';
	import FileUpload from '$lib/components/FileUpload.svelte';
	import UploadProgress from '$lib/components/UploadProgress.svelte';
	import ColumnMapper from '$lib/components/ColumnMapper.svelte';
	import DataPreview from '$lib/components/DataPreview.svelte';
	import ImportResults from '$lib/components/ImportResults.svelte';
	import { logger } from '$lib/utils/logger';
	
	let currentFile: File | null = null;
	let uploadId: string | null = null;
	let suggestedMapping: ColumnMapping = {};
	let columnMapping: ColumnMapping = {};
	
	// Subscribe to upload store
	const {
		stage,
		progress,
		message,
		uploadResponse,
		validationResult,
		importResult,
		error
	} = uploadStore;
	
	async function handleFileUpload(event: CustomEvent<{ files: File[] }>) {
		const file = event.detail.files[0];
		if (!file) return;
		
		currentFile = file;
		uploadStore.setFile(file);
		uploadStore.setStage('uploading');
		uploadStore.setProgress(0);
		uploadStore.setMessage('Uploading file...');
		
		try {
			// Simulate upload progress
			const progressInterval = setInterval(() => {
				uploadStore.setProgress(prev => Math.min(prev + 10, 90));
			}, 200);
			
			// Upload file
			const response = await uploadsApi.uploadFile(file);
			clearInterval(progressInterval);
			
			uploadStore.setProgress(100);
			uploadStore.setUploadResponse(response);
			uploadId = response.upload_id;
			
			// Get suggested mappings
			suggestedMapping = await uploadsApi.getSuggestedMappings(response.columns);
			columnMapping = suggestedMapping;
			
			// Move to mapping stage
			uploadStore.setStage('mapping');
			uploadStore.setMessage('Configure column mappings...');
			
		} catch (err: any) {
			logger.error('Upload failed:', err);
			uploadStore.setError(err.message || 'Failed to upload file');
		}
	}
	
	async function handleMappingChange(event: CustomEvent<{ mapping: ColumnMapping }>) {
		columnMapping = event.detail.mapping;
	}
	
	async function proceedToValidation() {
		if (!uploadId) return;
		
		uploadStore.setStage('validating');
		uploadStore.setProgress(0);
		uploadStore.setMessage('Validating data...');
		
		try {
			const result = await uploadsApi.validateData(uploadId, columnMapping);
			uploadStore.setValidationResult(result);
			uploadStore.setProgress(100);
			
			if (result.valid) {
				// Auto-proceed to import if validation passes
				await proceedToImport();
			} else {
				uploadStore.setStage('mapping');
				uploadStore.setMessage(`Validation failed: ${result.errors.length} errors found`);
			}
			
		} catch (err: any) {
			logger.error('Validation failed:', err);
			uploadStore.setError(err.message || 'Failed to validate data');
		}
	}
	
	async function proceedToImport() {
		if (!uploadId) return;
		
		uploadStore.setStage('importing');
		uploadStore.setProgress(0);
		uploadStore.setMessage('Importing trades...');
		
		try {
			// Simulate import progress
			const progressInterval = setInterval(() => {
				uploadStore.setProgress(prev => Math.min(prev + 5, 95));
			}, 500);
			
			const result = await uploadsApi.importTrades(uploadId, columnMapping);
			clearInterval(progressInterval);
			
			uploadStore.setProgress(100);
			uploadStore.setImportResult(result);
			uploadStore.setStage('complete');
			uploadStore.setMessage(result.message);
			
		} catch (err: any) {
			logger.error('Import failed:', err);
			uploadStore.setError(err.message || 'Failed to import trades');
		}
	}
	
	function handleNewImport() {
		uploadStore.reset();
		currentFile = null;
		uploadId = null;
		suggestedMapping = {};
		columnMapping = {};
	}
	
	function handleRetryImport() {
		// In a real app, this would retry only failed rows
		proceedToImport();
	}
	
	onMount(() => {
		// Check authentication
		if (!get(isAuthenticated)) {
			goto('/login');
		}
		
		// Reset store on mount
		uploadStore.reset();
	});
</script>

<svelte:head>
	<title>Import Trades - TradeSense</title>
</svelte:head>

<div class="upload-page">
	<header class="page-header">
		<div>
			<h1>Import Trades</h1>
			<p>Upload your trade history from CSV, Excel, or JSON files</p>
		</div>
	</header>
	
	{#if $stage === 'idle'}
		<FileUpload
			on:upload={handleFileUpload}
			accept=".csv,.xlsx,.xls,.json"
			maxSize={10485760}
		/>
		
		<div class="instructions">
			<h3>File Requirements</h3>
			<ul>
				<li>Supported formats: CSV (.csv), Excel (.xlsx, .xls), JSON (.json)</li>
				<li>Maximum file size: 10MB</li>
				<li>Required columns: Symbol, Side, Entry Price, Exit Price, Quantity, Entry Date, Exit Date</li>
				<li>Optional columns: P&L, Strategy, Notes</li>
			</ul>
			
			<h3>Sample File Format</h3>
			<div class="sample-format">
				<code>
					Symbol,Side,Entry Price,Exit Price,Quantity,Entry Date,Exit Date<br>
					AAPL,long,150.00,155.00,100,2024-01-01 09:30,2024-01-01 15:30<br>
					TSLA,short,240.50,238.00,50,2024-01-02 10:00,2024-01-02 14:00
				</code>
			</div>
		</div>
	{/if}
	
	{#if $stage !== 'idle' && $stage !== 'complete'}
		<UploadProgress
			stage={$stage}
			progress={$progress}
			message={$message}
			fileName={currentFile?.name || ''}
			totalRows={$uploadResponse?.rows || 0}
			errors={$validationResult?.errors.map(e => `Row ${e.row}: ${e.message}`) || []}
			warnings={$validationResult?.warnings.map(w => `Row ${w.row}: ${w.message}`) || []}
		/>
	{/if}
	
	{#if $stage === 'mapping' && $uploadResponse}
		<ColumnMapper
			fileColumns={$uploadResponse.columns}
			dataPreview={$uploadResponse.data_preview}
			{suggestedMapping}
			currentMapping={columnMapping}
			on:change={handleMappingChange}
		/>
		
		<DataPreview
			data={$uploadResponse.data_preview}
			columns={$uploadResponse.columns}
			title="File Preview"
			maxRows={5}
		/>
		
		<div class="actions">
			<button type="button" class="btn-secondary" on:click={handleNewImport}>
				Cancel
			</button>
			<button type="button" class="btn-primary" on:click={proceedToValidation}>
				Validate & Import
			</button>
		</div>
	{/if}
	
	{#if $stage === 'complete' && $importResult}
		<ImportResults
			result={$importResult}
			onRetry={handleRetryImport}
			onNewImport={handleNewImport}
		/>
	{/if}
	
	{#if $error}
		<div class="error-message">
			<h3>Error</h3>
			<p>{$error}</p>
			<button type="button" class="btn-primary" on:click={handleNewImport}>
				Try Again
			</button>
		</div>
	{/if}
</div>

<style>
	.upload-page {
		max-width: 1000px;
		margin: 0 auto;
		padding-bottom: 4rem;
	}
	
	.page-header {
		margin-bottom: 2rem;
	}
	
	.page-header h1 {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}
	
	.page-header p {
		color: #666;
		font-size: 1.125rem;
	}
	
	.instructions {
		margin-top: 3rem;
		display: grid;
		gap: 2rem;
	}
	
	.instructions h3 {
		font-size: 1.125rem;
		font-weight: 600;
		margin-bottom: 0.75rem;
		color: #333;
	}
	
	.instructions ul {
		margin: 0;
		padding-left: 1.5rem;
		color: #666;
		line-height: 1.8;
	}
	
	.sample-format {
		background: #f9f9f9;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		padding: 1rem;
		overflow-x: auto;
	}
	
	.sample-format code {
		font-family: 'Courier New', monospace;
		font-size: 0.875rem;
		color: #333;
		white-space: pre;
	}
	
	.actions {
		display: flex;
		justify-content: flex-end;
		gap: 1rem;
		margin-top: 2rem;
	}
	
	.btn-primary, .btn-secondary {
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
	}
	
	.error-message {
		background: #fee;
		border: 1px solid #fcc;
		border-radius: 8px;
		padding: 2rem;
		text-align: center;
		margin-top: 2rem;
	}
	
	.error-message h3 {
		font-size: 1.25rem;
		color: #c00;
		margin: 0 0 0.5rem 0;
	}
	
	.error-message p {
		color: #666;
		margin: 0 0 1.5rem 0;
	}
	
	@media (max-width: 768px) {
		.upload-page {
			padding: 1rem;
		}
		
		.actions {
			flex-direction: column;
		}
		
		.btn-primary, .btn-secondary {
			width: 100%;
		}
	}
</style>