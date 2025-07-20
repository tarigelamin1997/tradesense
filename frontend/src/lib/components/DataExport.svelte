<script lang="ts">
	import { Download, FileText, Table, FileSpreadsheet, Check } from 'lucide-svelte';
	import { api } from '$lib/api/ssr-safe';
	import { logger } from '$lib/utils/logger';
	
	export let endpoint: string;
	export let filename: string;
	export let buttonText: string = 'Export';
	export let buttonClass: string = '';
	export let data: any[] = []; // For client-side export
	
	let showMenu = false;
	let exporting = false;
	let exportSuccess = false;
	
	const exportFormats = [
		{ id: 'csv', label: 'CSV', icon: FileText, description: 'Comma-separated values' },
		{ id: 'excel', label: 'Excel', icon: Table, description: 'Microsoft Excel format' },
		{ id: 'json', label: 'JSON', icon: FileSpreadsheet, description: 'JavaScript Object Notation' }
	];
	
	async function handleExport(format: string) {
		exporting = true;
		exportSuccess = false;
		
		try {
			if (endpoint) {
				// Server-side export
				const response = await api.get(endpoint, {
					params: { format },
					responseType: 'blob'
				});
				
				const url = window.URL.createObjectURL(new Blob([response]));
				const link = document.createElement('a');
				link.href = url;
				link.setAttribute('download', `${filename}_${new Date().toISOString().split('T')[0]}.${format}`);
				document.body.appendChild(link);
				link.click();
				link.remove();
				window.URL.revokeObjectURL(url);
			} else if (data.length > 0) {
				// Client-side export
				let content: string;
				let mimeType: string;
				
				switch (format) {
					case 'csv':
						content = convertToCSV(data);
						mimeType = 'text/csv';
						break;
					case 'json':
						content = JSON.stringify(data, null, 2);
						mimeType = 'application/json';
						break;
					case 'excel':
						// For Excel, we'd need a library like xlsx
						// For now, fallback to CSV
						content = convertToCSV(data);
						mimeType = 'text/csv';
						format = 'csv';
						break;
					default:
						throw new Error('Unsupported format');
				}
				
				const blob = new Blob([content], { type: mimeType });
				const url = window.URL.createObjectURL(blob);
				const link = document.createElement('a');
				link.href = url;
				link.setAttribute('download', `${filename}_${new Date().toISOString().split('T')[0]}.${format}`);
				document.body.appendChild(link);
				link.click();
				link.remove();
				window.URL.revokeObjectURL(url);
			}
			
			exportSuccess = true;
			setTimeout(() => {
				exportSuccess = false;
				showMenu = false;
			}, 2000);
			
		} catch (error) {
			logger.error('Export failed:', error);
			alert('Export failed. Please try again.');
		} finally {
			exporting = false;
		}
	}
	
	function convertToCSV(data: any[]): string {
		if (data.length === 0) return '';
		
		// Get headers from first object
		const headers = Object.keys(data[0]);
		const csvHeaders = headers.join(',');
		
		// Convert each object to CSV row
		const csvRows = data.map(row => {
			return headers.map(header => {
				const value = row[header];
				// Escape values containing commas or quotes
				if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
					return `"${value.replace(/"/g, '""')}"`;
				}
				return value ?? '';
			}).join(',');
		});
		
		return [csvHeaders, ...csvRows].join('\n');
	}
	
	function handleClickOutside(event: MouseEvent) {
		if (showMenu && !(event.target as HTMLElement).closest('.export-dropdown')) {
			showMenu = false;
		}
	}
</script>

<svelte:window on:click={handleClickOutside} />

<div class="export-dropdown">
	<button
		class="export-button {buttonClass}"
		class:success={exportSuccess}
		on:click={() => showMenu = !showMenu}
		disabled={exporting}
	>
		{#if exportSuccess}
			<Check size={18} />
			Exported!
		{:else if exporting}
			<div class="spinner"></div>
			Exporting...
		{:else}
			<Download size={18} />
			{buttonText}
		{/if}
	</button>
	
	{#if showMenu && !exporting}
		<div class="export-menu">
			<div class="menu-header">Export Format</div>
			{#each exportFormats as format}
				<button
					class="format-option"
					on:click={() => handleExport(format.id)}
				>
					<svelte:component this={format.icon} size={20} />
					<div class="format-info">
						<div class="format-label">{format.label}</div>
						<div class="format-description">{format.description}</div>
					</div>
				</button>
			{/each}
		</div>
	{/if}
</div>

<style>
	.export-dropdown {
		position: relative;
		display: inline-block;
	}
	
	.export-button {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1.5rem;
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.export-button:hover:not(:disabled) {
		background: #f9fafb;
		border-color: #d1d5db;
	}
	
	.export-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	.export-button.success {
		background: #d1fae5;
		border-color: #6ee7b7;
		color: #065f46;
	}
	
	.spinner {
		width: 18px;
		height: 18px;
		border: 2px solid #e5e7eb;
		border-top-color: #10b981;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}
	
	@keyframes spin {
		to { transform: rotate(360deg); }
	}
	
	.export-menu {
		position: absolute;
		top: calc(100% + 0.5rem);
		right: 0;
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
		min-width: 250px;
		z-index: 100;
		overflow: hidden;
		animation: slideDown 0.2s ease-out;
	}
	
	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	
	.menu-header {
		padding: 0.75rem 1rem;
		background: #f9fafb;
		border-bottom: 1px solid #e5e7eb;
		font-size: 0.75rem;
		font-weight: 600;
		color: #6b7280;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.format-option {
		display: flex;
		align-items: center;
		gap: 1rem;
		width: 100%;
		padding: 0.875rem 1rem;
		background: none;
		border: none;
		cursor: pointer;
		transition: background 0.2s;
		text-align: left;
	}
	
	.format-option:hover {
		background: #f9fafb;
	}
	
	.format-option :global(svg) {
		color: #6b7280;
		flex-shrink: 0;
	}
	
	.format-info {
		flex: 1;
	}
	
	.format-label {
		font-weight: 500;
		color: #1a1a1a;
		margin-bottom: 0.125rem;
	}
	
	.format-description {
		font-size: 0.75rem;
		color: #6b7280;
	}
	
	/* Custom button styles can be passed via buttonClass */
	.export-button.primary {
		background: #10b981;
		color: white;
		border-color: #10b981;
	}
	
	.export-button.primary:hover:not(:disabled) {
		background: #059669;
		border-color: #059669;
	}
	
	/* Mobile Styles */
	@media (max-width: 640px) {
		.export-menu {
			right: auto;
			left: 0;
		}
		
		.export-button {
			padding: 0.625rem 1rem;
		}
	}
</style>