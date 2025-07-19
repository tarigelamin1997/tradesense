<script lang="ts">
	import { onMount } from 'svelte';
	import { Brain, TrendingUp, AlertTriangle, Target, Lightbulb, Activity, BarChart3, Zap } from 'lucide-svelte';
	import { analyticsAdvancedApi, type TradeIntelligence, type MarketRegime } from '$lib/api/analyticsAdvanced';
	import type { Trade } from '$lib/stores/trades';
	
	export let trades: Trade[] = [];
	export let userPlan: 'free' | 'pro' | 'enterprise' = 'free';
	
	let loading = true;
	let error = '';
	let activeSection = 'patterns';
	
	// AI Data
	let tradeIntelligence: TradeIntelligence | null = null;
	let marketRegime: MarketRegime | null = null;
	let marketAlerts: any[] = [];
	let performanceForecast: any = null;
	
	async function fetchAIInsights() {
		try {
			loading = true;
			error = '';
			
			// Fetch all AI insights in parallel
			const [patterns, regime, alerts, forecast] = await Promise.all([
				analyticsAdvancedApi.analyzePatterns().catch(() => null),
				analyticsAdvancedApi.getMarketRegime().catch(() => null),
				analyticsAdvancedApi.getMarketAlerts().catch(() => null),
				analyticsAdvancedApi.getPerformanceForecast().catch(() => null)
			]);
			
			tradeIntelligence = patterns;
			marketRegime = regime;
			marketAlerts = alerts || [];
			performanceForecast = forecast;
			
		} catch (err: any) {
			error = err.message || 'Failed to load AI insights';
			console.error('AI Insights error:', err);
		} finally {
			loading = false;
		}
	}
	
	function getRegimeIcon(regime: string) {
		switch (regime) {
			case 'trending': return TrendingUp;
			case 'volatile': return Activity;
			case 'ranging': return BarChart3;
			default: return Target;
		}
	}
	
	function getRegimeColor(regime: string) {
		switch (regime) {
			case 'trending': return 'green';
			case 'volatile': return 'red';
			case 'ranging': return 'blue';
			default: return 'gray';
		}
	}
	
	onMount(() => {
		if (userPlan !== 'free' && trades.length > 0) {
			fetchAIInsights();
		}
	});
</script>

<div class="ai-insights-panel">
	<div class="panel-header">
		<h2>
			<Brain size={24} />
			AI-Powered Insights
		</h2>
		<p>Advanced pattern recognition and market analysis</p>
	</div>
	
	{#if userPlan === 'free'}
		<div class="upgrade-prompt">
			<Zap size={32} />
			<h3>Unlock AI-Powered Trading Intelligence</h3>
			<p>Upgrade to Pro or Enterprise to access:</p>
			<ul>
				<li>Pattern recognition and analysis</li>
				<li>Market regime detection</li>
				<li>Performance forecasting</li>
				<li>Real-time trading alerts</li>
			</ul>
			<button class="upgrade-button">Upgrade Now</button>
		</div>
	{:else if loading}
		<div class="loading">
			<Brain size={32} class="spinning" />
			<p>Analyzing patterns with AI...</p>
		</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else}
		<div class="insights-tabs">
			<button 
				class="tab" 
				class:active={activeSection === 'patterns'}
				on:click={() => activeSection = 'patterns'}
			>
				<Target size={16} />
				Patterns
			</button>
			<button 
				class="tab" 
				class:active={activeSection === 'regime'}
				on:click={() => activeSection = 'regime'}
			>
				<Activity size={16} />
				Market Regime
			</button>
			<button 
				class="tab" 
				class:active={activeSection === 'alerts'}
				on:click={() => activeSection = 'alerts'}
			>
				<AlertTriangle size={16} />
				Alerts
			</button>
			{#if userPlan === 'enterprise'}
				<button 
					class="tab" 
					class:active={activeSection === 'forecast'}
					on:click={() => activeSection = 'forecast'}
				>
					<TrendingUp size={16} />
					Forecast
				</button>
			{/if}
		</div>
		
		<div class="insights-content">
			{#if activeSection === 'patterns' && tradeIntelligence}
				<div class="patterns-section">
					<h3>Detected Trading Patterns</h3>
					<div class="patterns-grid">
						{#each tradeIntelligence.patterns as pattern}
							<div class="pattern-card">
								<div class="pattern-header">
									<h4>{pattern.pattern_name}</h4>
									<span class="frequency">{pattern.frequency}x</span>
								</div>
								<p class="description">{pattern.description}</p>
								<div class="pattern-stats">
									<div class="stat">
										<span class="label">Win Rate</span>
										<span class="value" class:positive={pattern.win_rate > 50}>
											{pattern.win_rate.toFixed(1)}%
										</span>
									</div>
									<div class="stat">
										<span class="label">Avg P&L</span>
										<span class="value" class:positive={pattern.avg_pnl > 0}>
											${pattern.avg_pnl.toFixed(2)}
										</span>
									</div>
								</div>
							</div>
						{/each}
					</div>
					
					{#if tradeIntelligence.optimal_conditions}
						<div class="optimal-conditions">
							<h3>Optimal Trading Conditions</h3>
							<div class="conditions-grid">
								<div class="condition">
									<Lightbulb size={20} />
									<span class="label">Best Time</span>
									<span class="value">{tradeIntelligence.optimal_conditions.best_time}</span>
								</div>
								<div class="condition">
									<Lightbulb size={20} />
									<span class="label">Best Day</span>
									<span class="value">{tradeIntelligence.optimal_conditions.best_day}</span>
								</div>
								<div class="condition">
									<Lightbulb size={20} />
									<span class="label">Best Strategy</span>
									<span class="value">{tradeIntelligence.optimal_conditions.best_strategy}</span>
								</div>
							</div>
						</div>
					{/if}
				</div>
			{/if}
			
			{#if activeSection === 'regime' && marketRegime}
				<div class="regime-section">
					<div class="regime-card {getRegimeColor(marketRegime.current_regime)}">
						<div class="regime-icon">
							<svelte:component this={getRegimeIcon(marketRegime.current_regime)} size={48} />
						</div>
						<div class="regime-info">
							<h3>Current Market Regime</h3>
							<p class="regime-type">{marketRegime.current_regime.toUpperCase()}</p>
						</div>
					</div>
					
					<div class="recommendations">
						<h4>AI Recommendations</h4>
						<ul>
							{#each marketRegime.recommendations as recommendation}
								<li>{recommendation}</li>
							{/each}
						</ul>
					</div>
					
					<div class="regime-performance">
						<h4>Performance by Regime</h4>
						<div class="regime-stats">
							{#each Object.entries(marketRegime.regime_performance) as [regime, stats]}
								<div class="regime-stat">
									<span class="regime-name">{regime}</span>
									<div class="stats">
										<span>Win Rate: {stats.win_rate.toFixed(1)}%</span>
										<span>Avg P&L: ${stats.avg_pnl.toFixed(2)}</span>
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>
			{/if}
			
			{#if activeSection === 'alerts' && marketAlerts.length > 0}
				<div class="alerts-section">
					<h3>Market Alerts</h3>
					{#each marketAlerts as alert}
						<div class="alert-card {alert.severity}">
							<AlertTriangle size={20} />
							<div class="alert-content">
								<h4>{alert.title}</h4>
								<p>{alert.message}</p>
								<span class="timestamp">{new Date(alert.timestamp).toLocaleString()}</span>
							</div>
						</div>
					{/each}
				</div>
			{/if}
			
			{#if activeSection === 'forecast' && performanceForecast}
				<div class="forecast-section">
					<h3>Performance Forecast</h3>
					<div class="forecast-card">
						<div class="forecast-metric">
							<span class="label">Next 30 Days P&L</span>
							<span class="value">${performanceForecast.expected_pnl?.toFixed(2) || 'N/A'}</span>
						</div>
						<div class="forecast-metric">
							<span class="label">Confidence</span>
							<span class="value">{performanceForecast.confidence?.toFixed(1) || 'N/A'}%</span>
						</div>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.ai-insights-panel {
		background: white;
		border-radius: 12px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		padding: 1.5rem;
	}
	
	.panel-header {
		margin-bottom: 1.5rem;
	}
	
	.panel-header h2 {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}
	
	.panel-header p {
		color: #666;
	}
	
	.upgrade-prompt {
		text-align: center;
		padding: 3rem 2rem;
		background: #f9f9f9;
		border-radius: 8px;
	}
	
	.upgrade-prompt h3 {
		margin: 1rem 0;
		font-size: 1.25rem;
	}
	
	.upgrade-prompt ul {
		list-style: none;
		padding: 0;
		margin: 1.5rem 0;
	}
	
	.upgrade-prompt li {
		padding: 0.5rem 0;
		color: #555;
	}
	
	.upgrade-prompt li::before {
		content: '✓';
		color: #10b981;
		font-weight: bold;
		margin-right: 0.5rem;
	}
	
	.upgrade-button {
		background: linear-gradient(135deg, #3b82f6, #8b5cf6);
		color: white;
		border: none;
		padding: 0.75rem 2rem;
		border-radius: 6px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.upgrade-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
	}
	
	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 3rem;
		color: #666;
		gap: 1rem;
	}
	
	.loading :global(.spinning) {
		animation: spin 2s linear infinite;
	}
	
	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	.error {
		background: #fee;
		color: #c00;
		padding: 1rem;
		border-radius: 6px;
		text-align: center;
	}
	
	.insights-tabs {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1.5rem;
		border-bottom: 1px solid #e0e0e0;
		padding-bottom: 0.5rem;
	}
	
	.tab {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: none;
		border: none;
		color: #666;
		cursor: pointer;
		border-radius: 6px;
		transition: all 0.2s;
		font-weight: 500;
	}
	
	.tab:hover {
		background: #f3f4f6;
		color: #333;
	}
	
	.tab.active {
		background: #e0f2fe;
		color: #0369a1;
	}
	
	.patterns-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}
	
	.pattern-card {
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		padding: 1rem;
	}
	
	.pattern-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.75rem;
	}
	
	.pattern-header h4 {
		margin: 0;
		font-size: 1rem;
	}
	
	.frequency {
		background: #e0e7ff;
		color: #3730a3;
		padding: 0.25rem 0.5rem;
		border-radius: 12px;
		font-size: 0.75rem;
		font-weight: 600;
	}
	
	.description {
		color: #666;
		font-size: 0.875rem;
		margin-bottom: 1rem;
		line-height: 1.5;
	}
	
	.pattern-stats {
		display: flex;
		gap: 1.5rem;
	}
	
	.stat {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	
	.stat .label {
		font-size: 0.75rem;
		color: #666;
	}
	
	.stat .value {
		font-size: 1rem;
		font-weight: 600;
		color: #333;
	}
	
	.stat .value.positive {
		color: #10b981;
	}
	
	.optimal-conditions {
		background: #f0fdf4;
		border: 1px solid #86efac;
		border-radius: 8px;
		padding: 1.5rem;
		margin-top: 2rem;
	}
	
	.optimal-conditions h3 {
		margin-bottom: 1rem;
		color: #166534;
	}
	
	.conditions-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
	}
	
	.condition {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		background: white;
		padding: 1rem;
		border-radius: 6px;
	}
	
	.condition .label {
		font-size: 0.875rem;
		color: #666;
	}
	
	.condition .value {
		font-weight: 600;
		color: #166534;
		margin-left: auto;
	}
	
	.regime-card {
		display: flex;
		align-items: center;
		gap: 2rem;
		padding: 2rem;
		border-radius: 12px;
		margin-bottom: 2rem;
	}
	
	.regime-card.green {
		background: linear-gradient(135deg, #d1fae5, #a7f3d0);
		color: #065f46;
	}
	
	.regime-card.red {
		background: linear-gradient(135deg, #fee2e2, #fecaca);
		color: #991b1b;
	}
	
	.regime-card.blue {
		background: linear-gradient(135deg, #dbeafe, #bfdbfe);
		color: #1e40af;
	}
	
	.regime-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 80px;
		height: 80px;
		background: white;
		border-radius: 50%;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}
	
	.regime-type {
		font-size: 1.5rem;
		font-weight: 700;
		letter-spacing: 0.05em;
		margin-top: 0.5rem;
	}
	
	.recommendations {
		background: #f9fafb;
		border-radius: 8px;
		padding: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.recommendations h4 {
		margin-bottom: 1rem;
		color: #333;
	}
	
	.recommendations ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	
	.recommendations li {
		padding: 0.5rem 0;
		padding-left: 1.5rem;
		position: relative;
		color: #555;
	}
	
	.recommendations li::before {
		content: '→';
		position: absolute;
		left: 0;
		color: #3b82f6;
		font-weight: bold;
	}
	
	.regime-stats {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		gap: 1rem;
	}
	
	.regime-stat {
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		padding: 1rem;
	}
	
	.regime-name {
		font-weight: 600;
		color: #333;
		text-transform: capitalize;
		display: block;
		margin-bottom: 0.5rem;
	}
	
	.regime-stat .stats {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		font-size: 0.875rem;
		color: #666;
	}
	
	.alert-card {
		display: flex;
		gap: 1rem;
		padding: 1rem;
		border-radius: 8px;
		margin-bottom: 1rem;
		border: 1px solid;
	}
	
	.alert-card.high {
		background: #fee2e2;
		border-color: #fecaca;
		color: #991b1b;
	}
	
	.alert-card.medium {
		background: #fef3c7;
		border-color: #fde68a;
		color: #92400e;
	}
	
	.alert-card.low {
		background: #dbeafe;
		border-color: #bfdbfe;
		color: #1e40af;
	}
	
	.alert-content h4 {
		margin: 0 0 0.5rem 0;
		font-size: 1rem;
	}
	
	.alert-content p {
		margin: 0 0 0.5rem 0;
		font-size: 0.875rem;
	}
	
	.timestamp {
		font-size: 0.75rem;
		opacity: 0.7;
	}
	
	.forecast-card {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		padding: 2rem;
		background: linear-gradient(135deg, #ede9fe, #ddd6fe);
		border-radius: 12px;
	}
	
	.forecast-metric {
		text-align: center;
	}
	
	.forecast-metric .label {
		display: block;
		font-size: 0.875rem;
		color: #6b21a8;
		margin-bottom: 0.5rem;
	}
	
	.forecast-metric .value {
		font-size: 2rem;
		font-weight: 700;
		color: #581c87;
	}
	
	@media (max-width: 768px) {
		.patterns-grid {
			grid-template-columns: 1fr;
		}
		
		.conditions-grid {
			grid-template-columns: 1fr;
		}
		
		.regime-card {
			flex-direction: column;
			text-align: center;
			gap: 1rem;
		}
		
		.insights-tabs {
			overflow-x: auto;
			-webkit-overflow-scrolling: touch;
		}
		
		.tab {
			white-space: nowrap;
			font-size: 0.875rem;
			padding: 0.5rem 0.75rem;
		}
	}
</style>