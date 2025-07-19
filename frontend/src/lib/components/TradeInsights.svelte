<script lang="ts">
	import { Brain, TrendingUp, AlertTriangle, Lightbulb, Target } from 'lucide-svelte';
	import type { Trade } from '$lib/stores/trades';
	import FeatureGate from './FeatureGate.svelte';
	import { analyticsAdvancedApi, type TradeIntelligence, type EmotionalAnalytics } from '$lib/api/analyticsAdvanced';
	import { onMount } from 'svelte';
	
	export let trades: Trade[] = [];
	export let userPlan: 'free' | 'pro' | 'enterprise' = 'free';
	export let showAIInsights = true;
	
	interface Insight {
		id: string;
		type: 'strength' | 'weakness' | 'opportunity' | 'tip';
		title: string;
		message: string;
		priority: 'high' | 'medium' | 'low';
		actionable?: string;
		isAI?: boolean;
	}
	
	let aiInsights: TradeIntelligence | null = null;
	let emotionalInsights: EmotionalAnalytics | null = null;
	let loadingAI = false;
	
	// Generate AI insights based on trading patterns
	function generateInsights(trades: Trade[]): Insight[] {
		const insights: Insight[] = [];
		
		if (trades.length === 0) {
			return [{
				id: 'start',
				type: 'tip',
				title: 'Get Started',
				message: 'Start by adding your first trade to see personalized insights.',
				priority: 'high'
			}];
		}
		
		// Calculate basic metrics
		const wins = trades.filter(t => t.pnl > 0);
		const losses = trades.filter(t => t.pnl < 0);
		const winRate = (wins.length / trades.length) * 100;
		const avgWin = wins.length > 0 ? wins.reduce((sum, t) => sum + t.pnl, 0) / wins.length : 0;
		const avgLoss = losses.length > 0 ? Math.abs(losses.reduce((sum, t) => sum + t.pnl, 0) / losses.length) : 0;
		const riskRewardRatio = avgLoss > 0 ? avgWin / avgLoss : 0;
		
		// Strategy performance
		const strategyStats = new Map<string, { count: number; pnl: number; winRate: number }>();
		trades.forEach(trade => {
			if (trade.strategy) {
				const stats = strategyStats.get(trade.strategy) || { count: 0, pnl: 0, winRate: 0 };
				stats.count++;
				stats.pnl += trade.pnl;
				if (trade.pnl > 0) stats.winRate++;
				strategyStats.set(trade.strategy, stats);
			}
		});
		
		// Time analysis
		const hourlyPerformance = new Map<number, { count: number; pnl: number }>();
		trades.forEach(trade => {
			const hour = new Date(trade.entryDate).getHours();
			const stats = hourlyPerformance.get(hour) || { count: 0, pnl: 0 };
			stats.count++;
			stats.pnl += trade.pnl;
			hourlyPerformance.set(hour, stats);
		});
		
		// Generate insights based on patterns
		
		// Win rate insights
		if (winRate >= 70) {
			insights.push({
				id: 'high-win-rate',
				type: 'strength',
				title: 'Excellent Win Rate',
				message: `Your win rate of ${winRate.toFixed(1)}% is exceptional. Focus on increasing position sizes on high-confidence trades.`,
				priority: 'high',
				actionable: 'Consider scaling up positions gradually'
			});
		} else if (winRate < 40) {
			insights.push({
				id: 'low-win-rate',
				type: 'weakness',
				title: 'Win Rate Needs Improvement',
				message: `Your win rate of ${winRate.toFixed(1)}% is below optimal. Review your entry criteria and consider being more selective.`,
				priority: 'high',
				actionable: 'Focus on quality over quantity'
			});
		}
		
		// Risk-reward insights
		if (riskRewardRatio < 1.5 && winRate < 60) {
			insights.push({
				id: 'poor-risk-reward',
				type: 'weakness',
				title: 'Risk-Reward Ratio Too Low',
				message: `Your risk-reward ratio of ${riskRewardRatio.toFixed(2)} requires a high win rate. Consider targeting larger profits or tighter stops.`,
				priority: 'high',
				actionable: 'Aim for at least 2:1 reward-to-risk'
			});
		}
		
		// Strategy insights
		let bestStrategy: string | null = null;
		let bestStrategyWinRate = 0;
		let worstStrategy: string | null = null;
		let worstStrategyWinRate = 100;
		
		strategyStats.forEach((stats, strategy) => {
			const stratWinRate = (stats.winRate / stats.count) * 100;
			if (stratWinRate > bestStrategyWinRate) {
				bestStrategy = strategy;
				bestStrategyWinRate = stratWinRate;
			}
			if (stratWinRate < worstStrategyWinRate && stats.count >= 5) {
				worstStrategy = strategy;
				worstStrategyWinRate = stratWinRate;
			}
		});
		
		if (bestStrategy && bestStrategyWinRate >= 60) {
			insights.push({
				id: 'best-strategy',
				type: 'strength',
				title: 'Top Performing Strategy',
				message: `Your "${bestStrategy}" strategy has a ${bestStrategyWinRate.toFixed(1)}% win rate. Consider allocating more capital to this approach.`,
				priority: 'medium'
			});
		}
		
		if (worstStrategy && worstStrategyWinRate < 40) {
			insights.push({
				id: 'worst-strategy',
				type: 'weakness',
				title: 'Underperforming Strategy',
				message: `Your "${worstStrategy}" strategy has only a ${worstStrategyWinRate.toFixed(1)}% win rate. Consider refining or pausing this approach.`,
				priority: 'medium',
				actionable: 'Review and backtest this strategy'
			});
		}
		
		// Time-based insights
		let bestHour = -1;
		let bestHourPnL = 0;
		let worstHour = -1;
		let worstHourPnL = 0;
		
		hourlyPerformance.forEach((stats, hour) => {
			if (stats.pnl > bestHourPnL && stats.count >= 3) {
				bestHour = hour;
				bestHourPnL = stats.pnl;
			}
			if (stats.pnl < worstHourPnL && stats.count >= 3) {
				worstHour = hour;
				worstHourPnL = stats.pnl;
			}
		});
		
		if (bestHour >= 0) {
			const timeStr = `${bestHour}:00-${bestHour + 1}:00`;
			insights.push({
				id: 'best-time',
				type: 'opportunity',
				title: 'Optimal Trading Time',
				message: `You perform best during ${timeStr}. Your total P&L during this hour is $${bestHourPnL.toFixed(2)}.`,
				priority: 'low'
			});
		}
		
		// Consecutive losses warning
		let maxConsecutiveLosses = 0;
		let currentLossStreak = 0;
		const sortedTrades = [...trades].sort((a, b) => 
			new Date(a.exitDate).getTime() - new Date(b.exitDate).getTime()
		);
		
		sortedTrades.forEach(trade => {
			if (trade.pnl < 0) {
				currentLossStreak++;
				maxConsecutiveLosses = Math.max(maxConsecutiveLosses, currentLossStreak);
			} else {
				currentLossStreak = 0;
			}
		});
		
		if (currentLossStreak >= 3) {
			insights.push({
				id: 'loss-streak',
				type: 'weakness',
				title: 'Active Loss Streak',
				message: `You've had ${currentLossStreak} consecutive losses. Consider taking a break to reset mentally and review your approach.`,
				priority: 'high',
				actionable: 'Take a break and review your recent trades'
			});
		}
		
		// Overtrading check
		const daysTraded = new Set(trades.map(t => 
			new Date(t.entryDate).toDateString()
		)).size;
		const avgTradesPerDay = trades.length / daysTraded;
		
		if (avgTradesPerDay > 10) {
			insights.push({
				id: 'overtrading',
				type: 'weakness',
				title: 'Possible Overtrading',
				message: `You average ${avgTradesPerDay.toFixed(1)} trades per day. High frequency can lead to poor decision making and increased costs.`,
				priority: 'medium',
				actionable: 'Focus on quality setups only'
			});
		}
		
		// General tips
		if (trades.length < 20) {
			insights.push({
				id: 'more-data',
				type: 'tip',
				title: 'Build More Data',
				message: 'Continue logging trades to get more accurate insights and identify patterns in your trading.',
				priority: 'low'
			});
		}
		
		return insights.sort((a, b) => {
			const priorityOrder = { high: 0, medium: 1, low: 2 };
			return priorityOrder[a.priority] - priorityOrder[b.priority];
		});
	}
	
	async function fetchAIInsights() {
		if (!showAIInsights || userPlan === 'free') return;
		
		try {
			loadingAI = true;
			const [patterns, emotions] = await Promise.all([
				analyticsAdvancedApi.analyzePatterns().catch(() => null),
				analyticsAdvancedApi.getEmotionImpact().catch(() => null)
			]);
			
			aiInsights = patterns;
			emotionalInsights = emotions;
		} catch (error) {
			console.error('Failed to fetch AI insights:', error);
		} finally {
			loadingAI = false;
		}
	}
	
	function combineInsights(): Insight[] {
		const localInsights = generateInsights(trades);
		const combinedInsights: Insight[] = [...localInsights];
		
		// Add AI-powered insights if available
		if (aiInsights && userPlan !== 'free') {
			// Add pattern insights
			aiInsights.patterns.slice(0, 3).forEach((pattern, idx) => {
				combinedInsights.push({
					id: `ai-pattern-${idx}`,
					type: pattern.win_rate > 60 ? 'strength' : 'weakness',
					title: pattern.pattern_name,
					message: `${pattern.description} (${pattern.frequency} occurrences, ${pattern.win_rate.toFixed(1)}% win rate)`,
					priority: pattern.frequency > 10 ? 'high' : 'medium',
					actionable: pattern.win_rate > 60 ? 'Focus on this pattern' : 'Review and improve this pattern',
					isAI: true
				});
			});
			
			// Add optimal conditions insight
			if (aiInsights.optimal_conditions) {
				combinedInsights.push({
					id: 'ai-optimal',
					type: 'opportunity',
					title: 'AI-Detected Optimal Trading Conditions',
					message: `Best performance during ${aiInsights.optimal_conditions.best_time} on ${aiInsights.optimal_conditions.best_day}. Top strategy: ${aiInsights.optimal_conditions.best_strategy}`,
					priority: 'high',
					actionable: 'Schedule your trading during these optimal times',
					isAI: true
				});
			}
		}
		
		// Add emotional insights if available
		if (emotionalInsights && userPlan === 'enterprise') {
			const topEmotion = Object.entries(emotionalInsights.emotion_performance)
				.sort(([,a], [,b]) => b.win_rate - a.win_rate)[0];
			
			if (topEmotion) {
				combinedInsights.push({
					id: 'ai-emotion',
					type: 'tip',
					title: 'Emotional State Impact',
					message: `You perform best when feeling "${topEmotion[0]}" (${topEmotion[1].win_rate.toFixed(1)}% win rate)`,
					priority: 'medium',
					actionable: 'Track your emotional state before trades',
					isAI: true
				});
			}
		}
		
		// Sort by priority and limit to top insights
		return combinedInsights
			.sort((a, b) => {
				const priorityOrder = { high: 0, medium: 1, low: 2 };
				return priorityOrder[a.priority] - priorityOrder[b.priority];
			})
			.slice(0, 8);
	}
	
	$: insights = combineInsights();
	
	onMount(() => {
		if (trades.length > 0) {
			fetchAIInsights();
		}
	});
	
	function getInsightIcon(type: Insight['type']) {
		switch (type) {
			case 'strength': return TrendingUp;
			case 'weakness': return AlertTriangle;
			case 'opportunity': return Target;
			case 'tip': return Lightbulb;
		}
	}
	
	function getInsightColor(type: Insight['type']) {
		switch (type) {
			case 'strength': return 'green';
			case 'weakness': return 'red';
			case 'opportunity': return 'blue';
			case 'tip': return 'yellow';
		}
	}
</script>

<div class="insights-container">
	<div class="insights-header">
		<h2>
			<Brain size={24} />
			AI Trading Insights
		</h2>
		<p>Personalized recommendations based on your trading patterns</p>
	</div>
	
	<FeatureGate feature="ai-insights" {userPlan}>
		<div class="insights-grid">
			{#each insights as insight (insight.id)}
				<div class="insight-card {getInsightColor(insight.type)}" class:ai-powered={insight.isAI}>
					<div class="insight-header">
						<div class="insight-icon">
							<svelte:component this={getInsightIcon(insight.type)} size={20} />
						</div>
						<h3>{insight.title}</h3>
						{#if insight.isAI}
							<span class="ai-badge">AI</span>
						{/if}
						{#if insight.priority === 'high'}
							<span class="priority-badge">High Priority</span>
						{/if}
					</div>
					<p>{insight.message}</p>
					{#if insight.actionable}
						<div class="actionable">
							<strong>Action:</strong> {insight.actionable}
						</div>
					{/if}
				</div>
			{/each}
			
			{#if loadingAI}
				<div class="loading-ai">
					<Brain size={24} class="spinning" />
					<p>Analyzing patterns with AI...</p>
				</div>
			{/if}
		</div>
	</FeatureGate>
</div>

<style>
	.insights-container {
		margin-bottom: 2rem;
	}
	
	.insights-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 1.5rem;
	}
	
	.insights-header h2 {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-size: 1.5rem;
		margin: 0;
	}
	
	.insights-header p {
		color: #666;
		margin-left: auto;
	}
	
	.insights-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
		gap: 1rem;
	}
	
	.insight-card {
		background: white;
		border-radius: 12px;
		padding: 1.5rem;
		border: 2px solid transparent;
		transition: all 0.2s;
		position: relative;
		overflow: hidden;
	}
	
	.insight-card::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		width: 4px;
		height: 100%;
		background: currentColor;
	}
	
	.insight-card.green {
		border-color: #d1fae5;
		color: #059669;
	}
	
	.insight-card.green::before {
		background: #10b981;
	}
	
	.insight-card.red {
		border-color: #fee2e2;
		color: #dc2626;
	}
	
	.insight-card.red::before {
		background: #ef4444;
	}
	
	.insight-card.blue {
		border-color: #dbeafe;
		color: #2563eb;
	}
	
	.insight-card.blue::before {
		background: #3b82f6;
	}
	
	.insight-card.yellow {
		border-color: #fef3c7;
		color: #d97706;
	}
	
	.insight-card.yellow::before {
		background: #f59e0b;
	}
	
	.insight-header {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 1rem;
	}
	
	.insight-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 36px;
		height: 36px;
		border-radius: 8px;
		background: currentColor;
		opacity: 0.1;
	}
	
	.insight-icon :global(svg) {
		opacity: 1;
	}
	
	.insight-header h3 {
		font-size: 1.125rem;
		margin: 0;
		flex: 1;
		color: #1a1a1a;
	}
	
	.priority-badge {
		background: #ef4444;
		color: white;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.75rem;
		font-weight: 600;
	}
	
	.insight-card p {
		color: #4b5563;
		line-height: 1.6;
		margin-bottom: 1rem;
	}
	
	.actionable {
		background: #f9fafb;
		padding: 0.75rem;
		border-radius: 6px;
		font-size: 0.875rem;
		color: #374151;
	}
	
	.actionable strong {
		color: #1f2937;
	}
	
	.insight-card.ai-powered {
		background: linear-gradient(135deg, white 0%, #f0fdf4 100%);
		border-color: #86efac;
	}
	
	.ai-badge {
		background: linear-gradient(135deg, #3b82f6, #8b5cf6);
		color: white;
		padding: 0.2rem 0.5rem;
		border-radius: 12px;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.5px;
	}
	
	.loading-ai {
		grid-column: 1 / -1;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		padding: 2rem;
		color: #666;
	}
	
	.loading-ai :global(.spinning) {
		animation: spin 2s linear infinite;
	}
	
	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	@media (max-width: 768px) {
		.insights-grid {
			grid-template-columns: 1fr;
		}
		
		.insights-header {
			flex-direction: column;
			align-items: flex-start;
			gap: 0.5rem;
		}
		
		.insights-header p {
			margin-left: 0;
		}
	}
</style>