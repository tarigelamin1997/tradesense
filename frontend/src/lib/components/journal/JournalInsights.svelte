<script lang="ts">
	import { Brain, TrendingUp, TrendingDown, Activity, Heart } from 'lucide-svelte';
	import { analyzeTradingMindset } from '$lib/utils/sentimentAnalyzer';
	import type { JournalEntry } from '$lib/api/journal';
	import FeatureGate from '../FeatureGate.svelte';
	
	export let entries: JournalEntry[] = [];
	export let userPlan: 'free' | 'pro' | 'enterprise' = 'free';
	
	// Prepare entries for analysis
	$: entriesForAnalysis = entries.map(entry => ({
		content: entry.content.replace(/<[^>]*>/g, ''), // Strip HTML
		date: entry.created_at
	}));
	
	$: analysis = analyzeTradingMindset(entriesForAnalysis);
	
	function getSentimentIcon(sentiment: string) {
		switch (sentiment) {
			case 'positive': return TrendingUp;
			case 'negative': return TrendingDown;
			default: return Activity;
		}
	}
	
	function getSentimentColor(sentiment: string) {
		switch (sentiment) {
			case 'positive': return '#10b981';
			case 'negative': return '#ef4444';
			default: return '#6b7280';
		}
	}
	
	function getTrendIcon(trend: string) {
		switch (trend) {
			case 'improving': return TrendingUp;
			case 'declining': return TrendingDown;
			default: return Activity;
		}
	}
	
	function getTrendColor(trend: string) {
		switch (trend) {
			case 'improving': return '#10b981';
			case 'declining': return '#ef4444';
			default: return '#6b7280';
		}
	}
	
	function formatEmotion(emotion: string): string {
		return emotion.charAt(0).toUpperCase() + emotion.slice(1);
	}
</script>

<div class="insights-container card">
	<div class="insights-header">
		<h2>
			<Brain size={24} />
			Mindset Analysis
		</h2>
		<p>AI-powered insights into your trading psychology</p>
	</div>
	
	<FeatureGate feature="ai-insights" {userPlan}>
		{#if entries.length === 0}
			<div class="empty-insights">
				<Heart size={48} />
				<p>Start journaling to unlock mindset insights</p>
			</div>
		{:else}
			<div class="insights-grid">
				<!-- Overall Sentiment -->
				<div class="insight-card">
					<div class="insight-header">
						<svelte:component 
							this={getSentimentIcon(analysis.overallSentiment)} 
							size={20} 
							color={getSentimentColor(analysis.overallSentiment)}
						/>
						<h3>Overall Sentiment</h3>
					</div>
					<p class="sentiment-value" style="color: {getSentimentColor(analysis.overallSentiment)}">
						{formatEmotion(analysis.overallSentiment)}
					</p>
				</div>
				
				<!-- Sentiment Trend -->
				<div class="insight-card">
					<div class="insight-header">
						<svelte:component 
							this={getTrendIcon(analysis.sentimentTrend)} 
							size={20} 
							color={getTrendColor(analysis.sentimentTrend)}
						/>
						<h3>Trend Direction</h3>
					</div>
					<p class="trend-value" style="color: {getTrendColor(analysis.sentimentTrend)}">
						{formatEmotion(analysis.sentimentTrend)}
					</p>
				</div>
				
				<!-- Dominant Emotions -->
				{#if analysis.dominantEmotions.length > 0}
					<div class="insight-card full-width">
						<h3>Dominant Emotions</h3>
						<div class="emotions-list">
							{#each analysis.dominantEmotions as emotion}
								<span class="emotion-tag">
									{formatEmotion(emotion)}
								</span>
							{/each}
						</div>
					</div>
				{/if}
				
				<!-- Suggestions -->
				{#if analysis.suggestions.length > 0}
					<div class="suggestions-card full-width">
						<h3>Recommendations</h3>
						<ul class="suggestions-list">
							{#each analysis.suggestions as suggestion}
								<li>{suggestion}</li>
							{/each}
						</ul>
					</div>
				{/if}
			</div>
		{/if}
	</FeatureGate>
</div>

<style>
	.insights-container {
		padding: 2rem;
		margin-bottom: 2rem;
	}
	
	.insights-header {
		margin-bottom: 2rem;
	}
	
	.insights-header h2 {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}
	
	.insights-header p {
		color: #666;
	}
	
	.empty-insights {
		text-align: center;
		padding: 3rem;
		color: #999;
	}
	
	.empty-insights :global(svg) {
		margin: 0 auto 1rem;
		opacity: 0.3;
	}
	
	.insights-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
	}
	
	.insight-card {
		background: #f9fafb;
		padding: 1.5rem;
		border-radius: 12px;
	}
	
	.insight-card.full-width {
		grid-column: 1 / -1;
	}
	
	.insight-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}
	
	.insight-header h3 {
		font-size: 0.875rem;
		color: #666;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin: 0;
	}
	
	.sentiment-value,
	.trend-value {
		font-size: 1.5rem;
		font-weight: 600;
	}
	
	.emotions-list {
		display: flex;
		gap: 0.75rem;
		flex-wrap: wrap;
	}
	
	.emotion-tag {
		background: #e0f2fe;
		color: #0369a1;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-size: 0.875rem;
		font-weight: 500;
	}
	
	.suggestions-card {
		background: #f0fdf4;
		padding: 1.5rem;
		border-radius: 12px;
		border: 1px solid #bbf7d0;
	}
	
	.suggestions-card h3 {
		font-size: 1.125rem;
		margin-bottom: 1rem;
		color: #047857;
	}
	
	.suggestions-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	
	.suggestions-list li {
		padding: 0.75rem 0;
		border-bottom: 1px solid #d1fae5;
		color: #065f46;
		line-height: 1.6;
		position: relative;
		padding-left: 1.5rem;
	}
	
	.suggestions-list li:last-child {
		border-bottom: none;
	}
	
	.suggestions-list li::before {
		content: '→';
		position: absolute;
		left: 0;
		color: #10b981;
		font-weight: bold;
	}
	
	@media (max-width: 768px) {
		.insights-grid {
			grid-template-columns: 1fr;
		}
	}
</style>