<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Play, Pause, BarChart2, Users, Clock } from 'lucide-svelte';
	
	export let experiment: any;
	
	const dispatch = createEventDispatcher();
	
	function getStatusColor(status: string) {
		const colors = {
			draft: 'bg-gray-100 text-gray-700',
			running: 'bg-green-100 text-green-700',
			paused: 'bg-yellow-100 text-yellow-700',
			completed: 'bg-blue-100 text-blue-700',
			stopped: 'bg-red-100 text-red-700'
		};
		return colors[status] || 'bg-gray-100 text-gray-700';
	}
	
	function getConfidenceColor(confidence: number) {
		if (confidence >= 95) return 'text-green-600';
		if (confidence >= 90) return 'text-yellow-600';
		return 'text-gray-600';
	}
	
	function formatDate(date: string) {
		return new Date(date).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}
</script>

<div class="experiment-card">
	<div class="card-header">
		<div>
			<h3>{experiment.name}</h3>
			<p class="description">{experiment.description}</p>
		</div>
		<span class="status {getStatusColor(experiment.status)}">
			{experiment.status}
		</span>
	</div>
	
	<div class="card-body">
		<div class="metrics">
			<div class="metric">
				<Users size={16} />
				<span>{experiment.participants || 0} participants</span>
			</div>
			<div class="metric">
				<BarChart2 size={16} />
				<span class="{getConfidenceColor(experiment.confidence || 0)}">
					{experiment.confidence || 0}% confidence
				</span>
			</div>
			<div class="metric">
				<Clock size={16} />
				<span>{formatDate(experiment.created_at)}</span>
			</div>
		</div>
		
		{#if experiment.variants}
			<div class="variants">
				{#each experiment.variants as variant}
					<div class="variant">
						<div class="variant-header">
							<span class="variant-name">{variant.name}</span>
							<span class="variant-allocation">{variant.allocation}%</span>
						</div>
						<div class="variant-stats">
							<div class="stat">
								<span class="stat-label">Conversions</span>
								<span class="stat-value">{variant.conversions || 0}</span>
							</div>
							<div class="stat">
								<span class="stat-label">Rate</span>
								<span class="stat-value">
									{((variant.conversions / variant.participants) * 100 || 0).toFixed(2)}%
								</span>
							</div>
						</div>
						<div class="variant-bar">
							<div 
								class="variant-fill"
								style="width: {variant.allocation}%"
								class:winner={variant.is_winner}
							></div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
	
	<div class="card-actions">
		<button 
			class="action-button"
			on:click={() => dispatch('view', experiment)}
		>
			View Details
		</button>
		{#if experiment.status === 'running'}
			<button 
				class="action-button pause"
				on:click={() => dispatch('pause', experiment)}
			>
				<Pause size={16} />
				Pause
			</button>
		{:else if experiment.status === 'paused' || experiment.status === 'draft'}
			<button 
				class="action-button start"
				on:click={() => dispatch('start', experiment)}
			>
				<Play size={16} />
				Start
			</button>
		{/if}
	</div>
</div>

<style>
	.experiment-card {
		background: white;
		border-radius: 8px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		padding: 1.5rem;
		transition: box-shadow 0.2s;
	}
	
	.experiment-card:hover {
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
	}
	
	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1rem;
	}
	
	.card-header h3 {
		font-size: 1.125rem;
		font-weight: 600;
		margin-bottom: 0.25rem;
		color: #1f2937;
	}
	
	.description {
		font-size: 0.875rem;
		color: #6b7280;
	}
	
	.status {
		padding: 0.25rem 0.75rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 500;
		text-transform: capitalize;
	}
	
	.card-body {
		margin-bottom: 1rem;
	}
	
	.metrics {
		display: flex;
		gap: 1rem;
		margin-bottom: 1rem;
		flex-wrap: wrap;
	}
	
	.metric {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		font-size: 0.875rem;
		color: #6b7280;
	}
	
	.metric :global(svg) {
		color: #9ca3af;
	}
	
	.variants {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.variant {
		padding: 0.75rem;
		background: #f9fafb;
		border-radius: 6px;
	}
	
	.variant-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}
	
	.variant-name {
		font-weight: 500;
		color: #374151;
	}
	
	.variant-allocation {
		font-size: 0.875rem;
		color: #6b7280;
	}
	
	.variant-stats {
		display: flex;
		gap: 1.5rem;
		margin-bottom: 0.5rem;
	}
	
	.stat {
		display: flex;
		flex-direction: column;
		gap: 0.125rem;
	}
	
	.stat-label {
		font-size: 0.75rem;
		color: #9ca3af;
	}
	
	.stat-value {
		font-size: 0.875rem;
		font-weight: 500;
		color: #1f2937;
	}
	
	.variant-bar {
		height: 4px;
		background: #e5e7eb;
		border-radius: 2px;
		overflow: hidden;
	}
	
	.variant-fill {
		height: 100%;
		background: #3b82f6;
		transition: width 0.3s;
	}
	
	.variant-fill.winner {
		background: #10b981;
	}
	
	.card-actions {
		display: flex;
		gap: 0.75rem;
		border-top: 1px solid #e5e7eb;
		padding-top: 1rem;
	}
	
	.action-button {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.5rem 1rem;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		background: white;
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.action-button:hover {
		background: #f3f4f6;
		border-color: #d1d5db;
	}
	
	.action-button.start {
		color: #10b981;
		border-color: #10b981;
	}
	
	.action-button.start:hover {
		background: #f0fdf4;
	}
	
	.action-button.pause {
		color: #f59e0b;
		border-color: #f59e0b;
	}
	
	.action-button.pause:hover {
		background: #fffbeb;
	}
</style>