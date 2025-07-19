<script lang="ts">
	import { onMount } from 'svelte';
	import { analyticsAdvancedApi } from '$lib/api/analyticsAdvanced.js';
	import type { TradeIntelligence, PerformanceSummary, EmotionalAnalytics } from '$lib/api/analyticsAdvanced.js';
	
	let loading = true;
	let error = '';
	let performanceSummary: PerformanceSummary | null = null;
	let tradeIntelligence: TradeIntelligence | null = null;
	let emotionalAnalytics: EmotionalAnalytics | null = null;
	
	async function testAnalyticsEndpoints() {
		try {
			loading = true;
			error = '';
			
			console.log('Testing analytics endpoints...');
			
			// Test performance summary
			try {
				performanceSummary = await analyticsAdvancedApi.getPerformanceSummary();
				console.log('Performance Summary:', performanceSummary);
			} catch (e) {
				console.error('Performance Summary failed:', e);
			}
			
			// Test trade intelligence
			try {
				tradeIntelligence = await analyticsAdvancedApi.analyzePatterns();
				console.log('Trade Intelligence:', tradeIntelligence);
			} catch (e) {
				console.error('Trade Intelligence failed:', e);
			}
			
			// Test emotional analytics
			try {
				emotionalAnalytics = await analyticsAdvancedApi.getEmotionImpact();
				console.log('Emotional Analytics:', emotionalAnalytics);
			} catch (e) {
				console.error('Emotional Analytics failed:', e);
			}
			
		} catch (err: any) {
			error = err.message || 'Failed to test analytics endpoints';
			console.error('Error:', err);
		} finally {
			loading = false;
		}
	}
	
	onMount(() => {
		testAnalyticsEndpoints();
	});
</script>

<div class="test-page">
	<h1>Analytics Endpoints Test</h1>
	
	{#if loading}
		<p>Loading...</p>
	{:else if error}
		<div class="error">{error}</div>
	{:else}
		<div class="results">
			<section>
				<h2>Performance Summary</h2>
				{#if performanceSummary}
					<pre>{JSON.stringify(performanceSummary, null, 2)}</pre>
				{:else}
					<p>No data</p>
				{/if}
			</section>
			
			<section>
				<h2>Trade Intelligence</h2>
				{#if tradeIntelligence}
					<pre>{JSON.stringify(tradeIntelligence, null, 2)}</pre>
				{:else}
					<p>No data</p>
				{/if}
			</section>
			
			<section>
				<h2>Emotional Analytics</h2>
				{#if emotionalAnalytics}
					<pre>{JSON.stringify(emotionalAnalytics, null, 2)}</pre>
				{:else}
					<p>No data</p>
				{/if}
			</section>
		</div>
	{/if}
</div>

<style>
	.test-page {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}
	
	.error {
		background: #fee;
		color: #c00;
		padding: 1rem;
		border-radius: 4px;
		margin: 1rem 0;
	}
	
	.results {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}
	
	section {
		background: white;
		padding: 1.5rem;
		border-radius: 8px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
	
	pre {
		background: #f5f5f5;
		padding: 1rem;
		border-radius: 4px;
		overflow-x: auto;
		font-size: 0.875rem;
	}
</style>