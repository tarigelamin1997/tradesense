<script lang="ts">
	import { Lock, Sparkles } from 'lucide-svelte';
	import { goto } from '$app/navigation';
	
	export let feature: 'advanced-analytics' | 'ai-insights' | 'real-time' | 'unlimited-trades' | 'api-access';
	export let userPlan: 'free' | 'pro' | 'enterprise' = 'free';
	export let showLock = true;
	export let message = '';
	
	const featureRequirements = {
		'advanced-analytics': ['pro', 'enterprise'],
		'ai-insights': ['enterprise'],
		'real-time': ['pro', 'enterprise'],
		'unlimited-trades': ['pro', 'enterprise'],
		'api-access': ['pro', 'enterprise']
	};
	
	const featureMessages = {
		'advanced-analytics': 'Unlock advanced analytics with Pro',
		'ai-insights': 'AI-powered insights available on Enterprise',
		'real-time': 'Real-time data sync with Pro',
		'unlimited-trades': 'Remove trade limits with Pro',
		'api-access': 'API access available on Pro'
	};
	
	$: hasAccess = featureRequirements[feature]?.includes(userPlan) || false;
	$: displayMessage = message || featureMessages[feature];
	
	function handleUpgrade() {
		goto('/pricing');
	}
</script>

{#if hasAccess}
	<slot />
{:else if showLock}
	<div class="feature-locked">
		<div class="lock-overlay">
			<div class="lock-content">
				<Lock size={32} />
				<p>{displayMessage}</p>
				<button on:click={handleUpgrade} class="unlock-button">
					<Sparkles size={16} />
					Upgrade Now
				</button>
			</div>
		</div>
		<div class="locked-content">
			<slot />
		</div>
	</div>
{:else}
	<slot name="fallback">
		<div class="feature-unavailable">
			<p>{displayMessage}</p>
			<button on:click={handleUpgrade} class="text-button">
				View Plans →
			</button>
		</div>
	</slot>
{/if}

<style>
	.feature-locked {
		position: relative;
	}
	
	.lock-overlay {
		position: absolute;
		inset: 0;
		background: rgba(255, 255, 255, 0.95);
		backdrop-filter: blur(2px);
		z-index: 10;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 8px;
	}
	
	.lock-content {
		text-align: center;
		padding: 2rem;
	}
	
	.lock-content :global(svg) {
		color: #9ca3af;
		margin: 0 auto 1rem;
	}
	
	.lock-content p {
		font-size: 1.125rem;
		color: #4b5563;
		margin-bottom: 1.5rem;
		font-weight: 500;
	}
	
	.unlock-button {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1.5rem;
		background: #10b981;
		color: white;
		border: none;
		border-radius: 8px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.unlock-button:hover {
		background: #059669;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
	}
	
	.locked-content {
		filter: blur(2px);
		opacity: 0.5;
		pointer-events: none;
		user-select: none;
	}
	
	.feature-unavailable {
		padding: 2rem;
		text-align: center;
		background: #f9fafb;
		border: 2px dashed #e5e7eb;
		border-radius: 8px;
	}
	
	.feature-unavailable p {
		color: #6b7280;
		margin-bottom: 1rem;
	}
	
	.text-button {
		color: #10b981;
		background: none;
		border: none;
		font-weight: 500;
		cursor: pointer;
		transition: color 0.2s;
	}
	
	.text-button:hover {
		color: #059669;
		text-decoration: underline;
	}
</style>