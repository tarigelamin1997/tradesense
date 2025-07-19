<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { FileText, TrendingUp, Target, Brain, Calendar, AlertCircle } from 'lucide-svelte';
	
	const dispatch = createEventDispatcher();
	
	const templates = [
		{
			id: 'daily-review',
			name: 'Daily Review',
			icon: Calendar,
			description: 'Review your trading day',
			content: `<h2>Daily Trading Review</h2>
<h3>Market Overview</h3>
<p>What was the overall market condition today?</p>
<ul>
<li>Market trend:</li>
<li>Key news/events:</li>
<li>Volatility level:</li>
</ul>

<h3>Trades Executed</h3>
<p>List and analyze each trade:</p>
<ul>
<li>Trade 1: [Symbol] - [Result]</li>
<li>Trade 2: [Symbol] - [Result]</li>
</ul>

<h3>What Went Well?</h3>
<p></p>

<h3>What Could Be Improved?</h3>
<p></p>

<h3>Lessons Learned</h3>
<p></p>

<h3>Tomorrow's Plan</h3>
<p></p>`
		},
		{
			id: 'trade-plan',
			name: 'Trade Plan',
			icon: Target,
			description: 'Plan your next trade',
			content: `<h2>Trade Plan</h2>
<h3>Setup Details</h3>
<ul>
<li><strong>Symbol:</strong></li>
<li><strong>Strategy:</strong></li>
<li><strong>Timeframe:</strong></li>
<li><strong>Direction:</strong></li>
</ul>

<h3>Entry Criteria</h3>
<ul>
<li>Entry price:</li>
<li>Position size:</li>
<li>Confirmation signals:</li>
</ul>

<h3>Risk Management</h3>
<ul>
<li>Stop loss:</li>
<li>Risk amount:</li>
<li>Risk/Reward ratio:</li>
</ul>

<h3>Exit Strategy</h3>
<ul>
<li>Target 1:</li>
<li>Target 2:</li>
<li>Trailing stop:</li>
</ul>

<h3>Market Conditions</h3>
<p>Why this trade makes sense now:</p>`
		},
		{
			id: 'mistake-analysis',
			name: 'Mistake Analysis',
			icon: AlertCircle,
			description: 'Learn from trading mistakes',
			content: `<h2>Mistake Analysis</h2>
<h3>What Happened?</h3>
<p>Describe the mistake in detail:</p>

<h3>Why Did It Happen?</h3>
<ul>
<li>Emotional state:</li>
<li>Market conditions:</li>
<li>Rule violations:</li>
</ul>

<h3>Impact</h3>
<ul>
<li>Financial loss:</li>
<li>Psychological impact:</li>
<li>Confidence impact:</li>
</ul>

<h3>Root Cause Analysis</h3>
<p>What was the underlying cause?</p>

<h3>Prevention Strategy</h3>
<p>How will you prevent this in the future?</p>

<h3>Action Items</h3>
<ul>
<li>[ ] Action 1</li>
<li>[ ] Action 2</li>
<li>[ ] Action 3</li>
</ul>`
		},
		{
			id: 'strategy-notes',
			name: 'Strategy Notes',
			icon: Brain,
			description: 'Document strategy insights',
			content: `<h2>Strategy Notes</h2>
<h3>Strategy Name</h3>
<p></p>

<h3>Market Conditions</h3>
<p>When does this strategy work best?</p>

<h3>Entry Rules</h3>
<ol>
<li></li>
<li></li>
<li></li>
</ol>

<h3>Exit Rules</h3>
<ol>
<li></li>
<li></li>
<li></li>
</ol>

<h3>Risk Parameters</h3>
<ul>
<li>Max risk per trade:</li>
<li>Position sizing:</li>
<li>Stop loss placement:</li>
</ul>

<h3>Performance Metrics</h3>
<ul>
<li>Win rate:</li>
<li>Average win:</li>
<li>Average loss:</li>
<li>Profit factor:</li>
</ul>

<h3>Improvements & Observations</h3>
<p></p>`
		},
		{
			id: 'market-analysis',
			name: 'Market Analysis',
			icon: TrendingUp,
			description: 'Analyze market conditions',
			content: `<h2>Market Analysis</h2>
<h3>Overall Market Trend</h3>
<ul>
<li>Primary trend:</li>
<li>Secondary trend:</li>
<li>Key support/resistance:</li>
</ul>

<h3>Sector Analysis</h3>
<p>Which sectors are strong/weak?</p>

<h3>Economic Factors</h3>
<ul>
<li>Interest rates:</li>
<li>Economic data:</li>
<li>Geopolitical events:</li>
</ul>

<h3>Technical Analysis</h3>
<p>Key technical observations:</p>

<h3>Sentiment Analysis</h3>
<ul>
<li>VIX level:</li>
<li>Put/Call ratio:</li>
<li>Market breadth:</li>
</ul>

<h3>Trading Opportunities</h3>
<p>Based on this analysis:</p>`
		},
		{
			id: 'blank',
			name: 'Blank Entry',
			icon: FileText,
			description: 'Start with a blank journal',
			content: '<h2>Journal Entry</h2><p></p>'
		}
	];
	
	function selectTemplate(template: any) {
		dispatch('select', { template });
	}
</script>

<div class="templates">
	<h3>Quick Start Templates</h3>
	<div class="template-grid">
		{#each templates as template}
			<button
				type="button"
				class="template-card"
				on:click={() => selectTemplate(template)}
			>
				<svelte:component this={template.icon} size={24} class="template-icon" />
				<h4>{template.name}</h4>
				<p>{template.description}</p>
			</button>
		{/each}
	</div>
</div>

<style>
	.templates {
		margin-bottom: 2rem;
	}
	
	.templates h3 {
		font-size: 1.125rem;
		font-weight: 600;
		margin-bottom: 1rem;
		color: #333;
	}
	
	.template-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 1rem;
	}
	
	.template-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		padding: 1.5rem;
		background: white;
		border: 2px solid #e0e0e0;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.2s;
		text-align: center;
	}
	
	.template-card:hover {
		border-color: #10b981;
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}
	
	:global(.template-icon) {
		color: #10b981;
	}
	
	.template-card h4 {
		font-size: 1rem;
		font-weight: 600;
		color: #333;
		margin: 0;
	}
	
	.template-card p {
		font-size: 0.875rem;
		color: #666;
		margin: 0;
	}
	
	@media (max-width: 640px) {
		.template-grid {
			grid-template-columns: 1fr 1fr;
		}
		
		.template-card {
			padding: 1rem;
		}
	}
</style>