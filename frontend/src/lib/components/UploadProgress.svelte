<script lang="ts">
	import { CheckCircle, XCircle, Loader, AlertCircle } from 'lucide-svelte';
	
	export let stage: 'idle' | 'uploading' | 'validating' | 'mapping' | 'importing' | 'complete' | 'error' = 'idle';
	export let progress = 0;
	export let message = '';
	export let fileName = '';
	export let rowsProcessed = 0;
	export let totalRows = 0;
	export let errors: string[] = [];
	export let warnings: string[] = [];
	
	const stages = {
		idle: { label: 'Ready', icon: null, color: 'text-gray-500' },
		uploading: { label: 'Uploading', icon: Loader, color: 'text-blue-600' },
		validating: { label: 'Validating', icon: Loader, color: 'text-orange-600' },
		mapping: { label: 'Mapping Columns', icon: Loader, color: 'text-purple-600' },
		importing: { label: 'Importing', icon: Loader, color: 'text-green-600' },
		complete: { label: 'Complete', icon: CheckCircle, color: 'text-green-600' },
		error: { label: 'Error', icon: XCircle, color: 'text-red-600' }
	};
	
	$: currentStage = stages[stage];
	$: progressPercentage = Math.min(100, Math.max(0, progress));
</script>

{#if stage !== 'idle'}
	<div class="upload-progress">
		<div class="progress-header">
			<div class="stage-info">
				{#if currentStage.icon}
					<svelte:component 
						this={currentStage.icon} 
						size={20} 
						class="{currentStage.color} {stage === 'uploading' || stage === 'validating' || stage === 'mapping' || stage === 'importing' ? 'animate-spin' : ''}"
					/>
				{/if}
				<span class="stage-label {currentStage.color}">{currentStage.label}</span>
			</div>
			{#if fileName}
				<span class="file-name">{fileName}</span>
			{/if}
		</div>
		
		<div class="progress-bar-container">
			<div class="progress-bar" style="width: {progressPercentage}%"></div>
		</div>
		
		<div class="progress-details">
			{#if message}
				<p class="message">{message}</p>
			{/if}
			
			{#if totalRows > 0 && (stage === 'validating' || stage === 'importing')}
				<p class="row-count">
					Processing: {rowsProcessed} / {totalRows} rows
				</p>
			{/if}
		</div>
		
		{#if errors.length > 0}
			<div class="error-list">
				<h4><XCircle size={16} /> Errors ({errors.length})</h4>
				<ul>
					{#each errors.slice(0, 5) as error}
						<li>{error}</li>
					{/each}
					{#if errors.length > 5}
						<li class="more">... and {errors.length - 5} more errors</li>
					{/if}
				</ul>
			</div>
		{/if}
		
		{#if warnings.length > 0}
			<div class="warning-list">
				<h4><AlertCircle size={16} /> Warnings ({warnings.length})</h4>
				<ul>
					{#each warnings.slice(0, 3) as warning}
						<li>{warning}</li>
					{/each}
					{#if warnings.length > 3}
						<li class="more">... and {warnings.length - 3} more warnings</li>
					{/if}
				</ul>
			</div>
		{/if}
	</div>
{/if}

<style>
	.upload-progress {
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		padding: 1.5rem;
		margin-top: 1rem;
	}
	
	.progress-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}
	
	.stage-info {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.stage-label {
		font-weight: 600;
		font-size: 0.875rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.file-name {
		font-size: 0.875rem;
		color: #666;
		max-width: 200px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.progress-bar-container {
		width: 100%;
		height: 8px;
		background: #f0f0f0;
		border-radius: 4px;
		overflow: hidden;
		margin-bottom: 1rem;
	}
	
	.progress-bar {
		height: 100%;
		background: #10b981;
		border-radius: 4px;
		transition: width 0.3s ease;
	}
	
	.progress-details {
		margin-bottom: 1rem;
	}
	
	.message {
		font-size: 0.875rem;
		color: #666;
		margin: 0 0 0.5rem 0;
	}
	
	.row-count {
		font-size: 0.875rem;
		color: #999;
		margin: 0;
	}
	
	.error-list, .warning-list {
		margin-top: 1rem;
		padding: 1rem;
		border-radius: 6px;
		font-size: 0.875rem;
	}
	
	.error-list {
		background: #fee;
		border: 1px solid #fcc;
		color: #c00;
	}
	
	.warning-list {
		background: #fffbeb;
		border: 1px solid #fde68a;
		color: #92400e;
	}
	
	.error-list h4, .warning-list h4 {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin: 0 0 0.5rem 0;
		font-size: 0.875rem;
		font-weight: 600;
	}
	
	.error-list ul, .warning-list ul {
		margin: 0;
		padding-left: 1.5rem;
		list-style: disc;
	}
	
	.error-list li, .warning-list li {
		margin-bottom: 0.25rem;
	}
	
	.more {
		font-style: italic;
		opacity: 0.8;
	}
	
	:global(.animate-spin) {
		animation: spin 1s linear infinite;
	}
	
	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}
	
	@media (max-width: 640px) {
		.upload-progress {
			padding: 1rem;
		}
		
		.file-name {
			max-width: 150px;
		}
	}
</style>