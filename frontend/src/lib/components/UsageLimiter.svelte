<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { TrendingUp, AlertTriangle } from 'lucide-svelte';
	
	export let current: number;
	export let limit: number;
	export let type: 'trades' | 'journal' | 'playbooks';
	export let showUpgradePrompt = true;
	
	const dispatch = createEventDispatcher();
	
	$: percentage = limit === -1 ? 0 : Math.min((current / limit) * 100, 100);
	$: isNearLimit = limit !== -1 && percentage >= 80;
	$: isAtLimit = limit !== -1 && current >= limit;
	
	const typeLabels = {
		trades: 'trades',
		journal: 'journal entries',
		playbooks: 'playbooks'
	};
	
	function handleUpgrade() {
		dispatch('upgrade');
	}
</script>

{#if limit !== -1 && (isNearLimit || isAtLimit)}
	<div class="usage-warning" class:limit-reached={isAtLimit}>
		<div class="warning-content">
			<div class="warning-icon">
				<AlertTriangle size={20} />
			</div>
			<div class="warning-text">
				{#if isAtLimit}
					<strong>Limit reached!</strong> You've used all {limit} {typeLabels[type]} for this month.
				{:else}
					<strong>Approaching limit!</strong> You've used {current} of {limit} {typeLabels[type]} ({Math.round(percentage)}%).
				{/if}
			</div>
			{#if showUpgradePrompt}
				<button class="upgrade-button" on:click={handleUpgrade}>
					<TrendingUp size={16} />
					Upgrade
				</button>
			{/if}
		</div>
		<div class="usage-bar">
			<div class="usage-bar-fill" style="width: {percentage}%" />
		</div>
	</div>
{/if}

<style>
	.usage-warning {
		background: #fffbeb;
		border: 1px solid #fbbf24;
		border-radius: 8px;
		padding: 1rem;
		margin-bottom: 1.5rem;
	}
	
	.usage-warning.limit-reached {
		background: #fef2f2;
		border-color: #f87171;
	}
	
	.warning-content {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 0.75rem;
	}
	
	.warning-icon {
		color: #f59e0b;
		flex-shrink: 0;
	}
	
	.limit-reached .warning-icon {
		color: #ef4444;
	}
	
	.warning-text {
		flex: 1;
		font-size: 0.875rem;
		color: #92400e;
	}
	
	.limit-reached .warning-text {
		color: #991b1b;
	}
	
	.upgrade-button {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.5rem 1rem;
		background: #10b981;
		color: white;
		border: none;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.2s;
	}
	
	.upgrade-button:hover {
		background: #059669;
	}
	
	.usage-bar {
		height: 6px;
		background: #fee0b2;
		border-radius: 3px;
		overflow: hidden;
	}
	
	.limit-reached .usage-bar {
		background: #fecaca;
	}
	
	.usage-bar-fill {
		height: 100%;
		background: #f59e0b;
		transition: width 0.3s;
	}
	
	.limit-reached .usage-bar-fill {
		background: #ef4444;
	}
	
	@media (max-width: 640px) {
		.warning-content {
			flex-wrap: wrap;
		}
		
		.upgrade-button {
			width: 100%;
			justify-content: center;
		}
	}
</style>