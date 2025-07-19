<script lang="ts">
  import { onMount } from 'svelte';
  import { 
    Brain, TrendingUp, AlertTriangle, Target, 
    Zap, Activity, BarChart3, Shield, 
    Lightbulb, ChevronRight, RefreshCw
  } from 'lucide-svelte';
  import { aiApi, type AIInsightsSummary, type PatternDetection, type EdgeStrength } from '$lib/api/ai.js';
  import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
  import ScoreGauge from '$lib/components/ScoreGauge.svelte';
  import { formatCurrency, formatPercent } from '$lib/utils/format';

  let loading = true;
  let error = '';
  let insights: AIInsightsSummary | null = null;
  let patterns: PatternDetection[] = [];
  let edgeStrength: EdgeStrength[] = [];
  let activeTab: 'overview' | 'patterns' | 'behavioral' | 'market' = 'overview';
  let refreshing = false;

  async function loadAIInsights() {
    try {
      loading = true;
      error = '';

      const [insightsSummary, patternsData, edgeData] = await Promise.all([
        aiApi.getAIInsightsSummary(),
        aiApi.detectPatterns('month'),
        aiApi.getEdgeStrength()
      ]);

      insights = insightsSummary;
      patterns = patternsData;
      edgeStrength = edgeData;
    } catch (err: any) {
      error = err.message || 'Failed to load AI insights';
      console.error('Error loading AI insights:', err);
    } finally {
      loading = false;
    }
  }

  async function refreshInsights() {
    refreshing = true;
    await loadAIInsights();
    refreshing = false;
  }

  function getScoreColor(score: number): string {
    if (score >= 80) return '#10b981';
    if (score >= 60) return '#f59e0b';
    if (score >= 40) return '#3b82f6';
    return '#ef4444';
  }

  function getConfidenceText(confidence: number): string {
    if (confidence >= 8) return 'Very High';
    if (confidence >= 6) return 'High';
    if (confidence >= 4) return 'Medium';
    return 'Low';
  }

  onMount(() => {
    loadAIInsights();
  });
</script>

<svelte:head>
  <title>AI Insights - TradeSense</title>
</svelte:head>

<div class="ai-insights-page">
  <!-- Header -->
  <div class="page-header">
    <div class="header-content">
      <div class="header-title">
        <Brain size={32} class="header-icon" />
        <div>
          <h1>AI Trading Intelligence</h1>
          <p>Powered by advanced pattern recognition and behavioral analytics</p>
        </div>
      </div>
      <button 
        class="refresh-button" 
        on:click={refreshInsights}
        disabled={refreshing}
        class:spinning={refreshing}
      >
        <RefreshCw size={20} />
        <span>Refresh</span>
      </button>
    </div>
  </div>

  {#if loading}
    <div class="loading-container">
      <LoadingSkeleton type="card" count={4} />
    </div>
  {:else if error}
    <div class="error-container">
      <AlertTriangle size={48} />
      <h3>Unable to Load AI Insights</h3>
      <p>{error}</p>
      <button on:click={loadAIInsights}>Try Again</button>
    </div>
  {:else if insights}
    <!-- AI Score Overview -->
    <div class="ai-score-section">
      <div class="score-cards">
        <div class="main-score-card">
          <h3>Overall Trading Score</h3>
          <div class="score-display">
            <ScoreGauge score={insights.trade_score.overall_score} size={200} />
            <div class="score-breakdown">
              <div class="score-item">
                <span>Execution</span>
                <span style="color: {getScoreColor(insights.trade_score.execution_score)}">
                  {insights.trade_score.execution_score}/100
                </span>
              </div>
              <div class="score-item">
                <span>Timing</span>
                <span style="color: {getScoreColor(insights.trade_score.timing_score)}">
                  {insights.trade_score.timing_score}/100
                </span>
              </div>
              <div class="score-item">
                <span>Strategy</span>
                <span style="color: {getScoreColor(insights.trade_score.strategy_score)}">
                  {insights.trade_score.strategy_score}/100
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="insight-cards">
          <div class="insight-card behavioral">
            <div class="card-header">
              <Activity size={24} />
              <h4>Behavioral Score</h4>
            </div>
            <div class="score-value">
              {insights.behavioral_insights.discipline_score}/10
            </div>
            <p class="score-label">Discipline Rating</p>
            <div class="mini-stats">
              <span>Consistency: {insights.behavioral_insights.consistency_rating}%</span>
              <span>Profile: {insights.behavioral_insights.risk_profile}</span>
            </div>
          </div>

          <div class="insight-card market">
            <div class="card-header">
              <TrendingUp size={24} />
              <h4>Market Alignment</h4>
            </div>
            <div class="regime-indicator {insights.market_context.regime}">
              {insights.market_context.regime.toUpperCase()} Market
            </div>
            <p class="score-label">Current Regime</p>
            <div class="mini-stats">
              <span>Volatility: {insights.market_context.volatility}</span>
              <span>Trend: {insights.market_context.trend_strength}/10</span>
            </div>
          </div>

          <div class="insight-card emotional">
            <div class="card-header">
              <Zap size={24} />
              <h4>Emotional State</h4>
            </div>
            <div class="emotion-display">
              {insights.behavioral_insights.emotional_state}
            </div>
            <p class="score-label">Current State</p>
            <div class="mini-stats">
              <span>Consistency: {insights.emotional_analytics.emotional_consistency}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs-container">
      <div class="tabs">
        <button 
          class="tab" 
          class:active={activeTab === 'overview'}
          on:click={() => activeTab = 'overview'}
        >
          <Lightbulb size={18} />
          <span>Key Insights</span>
        </button>
        <button 
          class="tab" 
          class:active={activeTab === 'patterns'}
          on:click={() => activeTab = 'patterns'}
        >
          <Target size={18} />
          <span>Pattern Detection</span>
        </button>
        <button 
          class="tab" 
          class:active={activeTab === 'behavioral'}
          on:click={() => activeTab = 'behavioral'}
        >
          <Brain size={18} />
          <span>Behavioral Analysis</span>
        </button>
        <button 
          class="tab" 
          class:active={activeTab === 'market'}
          on:click={() => activeTab = 'market'}
        >
          <BarChart3 size={18} />
          <span>Market Context</span>
        </button>
      </div>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      {#if activeTab === 'overview'}
        <div class="overview-content">
          <!-- AI Critique -->
          <div class="section critique-section">
            <h3>AI Trading Coach Analysis</h3>
            <div class="critique-card">
              <div class="critique-header">
                <span class="confidence-badge">
                  Confidence: {getConfidenceText(insights.critique.confidence)}
                </span>
                <div class="critique-tags">
                  {#each insights.critique.tags.slice(0, 3) as tag}
                    <span class="tag">{tag}</span>
                  {/each}
                </div>
              </div>
              <div class="critique-content">
                <h4>Summary</h4>
                <p>{insights.critique.summary}</p>
                
                <h4>Recommendation</h4>
                <p class="recommendation">{insights.critique.suggestion}</p>
              </div>
            </div>
          </div>

          <!-- Key Insights -->
          <div class="section insights-grid">
            <div class="insight-panel">
              <h4><Shield size={20} /> Risk Assessment</h4>
              <p>{insights.critique.risk_assessment}</p>
            </div>
            <div class="insight-panel">
              <h4><Target size={20} /> Technical Analysis</h4>
              <p>{insights.critique.technical_analysis}</p>
            </div>
            <div class="insight-panel">
              <h4><Brain size={20} /> Psychological Analysis</h4>
              <p>{insights.critique.psychological_analysis}</p>
            </div>
          </div>

          <!-- Recommendations -->
          <div class="section recommendations">
            <h3>AI Recommendations</h3>
            <div class="recommendation-list">
              {#each insights.trade_score.recommendations as rec}
                <div class="recommendation-item">
                  <ChevronRight size={16} />
                  <span>{rec}</span>
                </div>
              {/each}
            </div>
          </div>
        </div>

      {:else if activeTab === 'patterns'}
        <div class="patterns-content">
          <h3>Detected Trading Patterns</h3>
          <div class="patterns-grid">
            {#each patterns as pattern}
              <div class="pattern-card" class:negative={pattern.impact_on_pnl < 0}>
                <div class="pattern-header">
                  <h4>{pattern.pattern_type}</h4>
                  <span class="frequency">Occurred {pattern.frequency}x</span>
                </div>
                <div class="pattern-impact">
                  <span>P&L Impact:</span>
                  <span class:positive={pattern.impact_on_pnl > 0} class:negative={pattern.impact_on_pnl < 0}>
                    {formatCurrency(pattern.impact_on_pnl)}
                  </span>
                </div>
                <p class="pattern-description">{pattern.description}</p>
                <div class="pattern-recommendation">
                  <strong>Recommendation:</strong> {pattern.recommendations}
                </div>
              </div>
            {/each}
          </div>

          <!-- Streaks Analysis -->
          <div class="streaks-section">
            <h3>Trading Streaks</h3>
            <div class="streaks-grid">
              <div class="streak-card current-{insights.behavioral_insights.streaks.streak_type}">
                <h4>Current Streak</h4>
                <div class="streak-value">{insights.behavioral_insights.streaks.current_streak}</div>
                <span class="streak-type">{insights.behavioral_insights.streaks.streak_type}</span>
              </div>
              <div class="streak-card">
                <h4>Best Streak</h4>
                <div class="streak-value positive">{insights.behavioral_insights.streaks.best_streak}</div>
                <span class="streak-label">Consecutive Wins</span>
              </div>
              <div class="streak-card">
                <h4>Worst Streak</h4>
                <div class="streak-value negative">{insights.behavioral_insights.streaks.worst_streak}</div>
                <span class="streak-label">Consecutive Losses</span>
              </div>
            </div>
          </div>
        </div>

      {:else if activeTab === 'behavioral'}
        <div class="behavioral-content">
          <h3>Behavioral Analytics</h3>
          
          <!-- Improvement Areas -->
          <div class="improvement-section">
            <h4>Areas for Improvement</h4>
            <div class="improvement-list">
              {#each insights.behavioral_insights.improvement_areas as area}
                <div class="improvement-item">
                  <AlertTriangle size={16} />
                  <span>{area}</span>
                </div>
              {/each}
            </div>
          </div>

          <!-- Emotional Impact -->
          <div class="emotional-section">
            <h4>Emotional Trading Impact</h4>
            <div class="emotions-grid">
              {#each insights.emotional_analytics.dominant_emotions as emotion}
                <div class="emotion-card">
                  <h5>{emotion.emotion}</h5>
                  <div class="emotion-stats">
                    <div class="stat">
                      <span>Frequency</span>
                      <span>{emotion.frequency}%</span>
                    </div>
                    <div class="stat">
                      <span>P&L Impact</span>
                      <span class:positive={emotion.impact > 0} class:negative={emotion.impact < 0}>
                        {formatPercent(emotion.impact)}
                      </span>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
            <div class="emotion-insights">
              <p><strong>Best Performing Emotion:</strong> {insights.emotional_analytics.best_performing_emotion}</p>
              <p><strong>Worst Performing Emotion:</strong> {insights.emotional_analytics.worst_performing_emotion}</p>
            </div>
          </div>
        </div>

      {:else if activeTab === 'market'}
        <div class="market-content">
          <h3>Market Context Analysis</h3>
          
          <!-- Market Regime -->
          <div class="market-regime-section">
            <div class="regime-card {insights.market_context.regime}">
              <h4>Current Market Regime</h4>
              <div class="regime-display">
                <span class="regime-type">{insights.market_context.regime.toUpperCase()}</span>
                <span class="volatility">Volatility: {insights.market_context.volatility}</span>
              </div>
              <p class="regime-recommendation">{insights.market_context.recommendation}</p>
            </div>
          </div>

          <!-- Edge Strength by Strategy -->
          <div class="edge-strength-section">
            <h4>Strategy Performance Edge</h4>
            <div class="edge-table">
              <div class="edge-header">
                <span>Strategy</span>
                <span>Win Rate</span>
                <span>Profit Factor</span>
                <span>Sharpe Ratio</span>
                <span>Confidence</span>
              </div>
              {#each edgeStrength as edge}
                <div class="edge-row">
                  <span class="strategy-name">{edge.strategy}</span>
                  <span class:positive={edge.win_rate > 50}>{edge.win_rate.toFixed(1)}%</span>
                  <span class:positive={edge.profit_factor > 1}>{edge.profit_factor.toFixed(2)}</span>
                  <span class:positive={edge.sharpe_ratio > 1}>{edge.sharpe_ratio.toFixed(2)}</span>
                  <span class="confidence-level">{edge.confidence_level}%</span>
                </div>
              {/each}
            </div>
          </div>

          <!-- Market Levels -->
          <div class="market-levels">
            <h4>Key Market Levels</h4>
            <div class="levels-grid">
              <div class="levels-card">
                <h5>Support Levels</h5>
                {#each insights.market_context.support_levels as level}
                  <div class="level-item support">{level.toFixed(2)}</div>
                {/each}
              </div>
              <div class="levels-card">
                <h5>Resistance Levels</h5>
                {#each insights.market_context.resistance_levels as level}
                  <div class="level-item resistance">{level.toFixed(2)}</div>
                {/each}
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .ai-insights-page {
    padding: 2rem;
    max-width: 1400px;
    margin: 0 auto;
  }

  .page-header {
    margin-bottom: 2rem;
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .header-icon {
    color: #8b5cf6;
  }

  .header-title h1 {
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
  }

  .header-title p {
    color: #6b7280;
    margin: 0.25rem 0 0 0;
  }

  .refresh-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: #f3f4f6;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .refresh-button:hover {
    background: #e5e7eb;
  }

  .refresh-button.spinning svg {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* Score Section */
  .ai-score-section {
    margin-bottom: 3rem;
  }

  .score-cards {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 2rem;
  }

  .main-score-card {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .main-score-card h3 {
    font-size: 1.25rem;
    margin-bottom: 1.5rem;
    text-align: center;
  }

  .score-display {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
  }

  .score-breakdown {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .score-item {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem;
    background: #f9fafb;
    border-radius: 6px;
  }

  .insight-cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
  }

  .insight-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    position: relative;
    overflow: hidden;
  }

  .insight-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
  }

  .insight-card.behavioral::before {
    background: linear-gradient(90deg, #8b5cf6, #7c3aed);
  }

  .insight-card.market::before {
    background: linear-gradient(90deg, #3b82f6, #2563eb);
  }

  .insight-card.emotional::before {
    background: linear-gradient(90deg, #f59e0b, #f97316);
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .card-header h4 {
    font-size: 1rem;
    margin: 0;
  }

  .score-value {
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 0.5rem;
  }

  .score-label {
    color: #6b7280;
    font-size: 0.875rem;
    margin-bottom: 1rem;
  }

  .mini-stats {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.75rem;
    color: #9ca3af;
  }

  .regime-indicator {
    font-size: 1.125rem;
    font-weight: 600;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    text-align: center;
    margin-bottom: 0.5rem;
  }

  .regime-indicator.bull {
    background: #d1fae5;
    color: #065f46;
  }

  .regime-indicator.bear {
    background: #fee2e2;
    color: #991b1b;
  }

  .regime-indicator.sideways {
    background: #e0e7ff;
    color: #3730a3;
  }

  .emotion-display {
    font-size: 1.5rem;
    font-weight: 600;
    color: #374151;
    margin-bottom: 0.5rem;
  }

  /* Tabs */
  .tabs-container {
    margin-bottom: 2rem;
  }

  .tabs {
    display: flex;
    gap: 1rem;
    border-bottom: 2px solid #e5e7eb;
  }

  .tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem 1.5rem;
    background: none;
    border: none;
    cursor: pointer;
    color: #6b7280;
    font-weight: 500;
    transition: all 0.2s;
    position: relative;
  }

  .tab:hover {
    color: #374151;
  }

  .tab.active {
    color: #8b5cf6;
  }

  .tab.active::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    right: 0;
    height: 2px;
    background: #8b5cf6;
  }

  /* Tab Content */
  .tab-content {
    min-height: 400px;
  }

  .section {
    margin-bottom: 2rem;
  }

  .section h3 {
    font-size: 1.25rem;
    margin-bottom: 1rem;
  }

  /* Critique Section */
  .critique-card {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }

  .critique-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }

  .confidence-badge {
    background: #e0e7ff;
    color: #5b21b6;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .critique-tags {
    display: flex;
    gap: 0.5rem;
  }

  .tag {
    background: #f3f4f6;
    color: #374151;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
  }

  .critique-content h4 {
    font-size: 1rem;
    margin: 1.5rem 0 0.5rem 0;
  }

  .critique-content p {
    color: #4b5563;
    line-height: 1.6;
  }

  .recommendation {
    background: #f0fdf4;
    border-left: 4px solid #10b981;
    padding: 1rem;
    border-radius: 0 8px 8px 0;
    color: #064e3b;
  }

  /* Insights Grid */
  .insights-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
  }

  .insight-panel {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }

  .insight-panel h4 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1rem;
    margin-bottom: 0.75rem;
    color: #374151;
  }

  .insight-panel p {
    color: #6b7280;
    line-height: 1.6;
    font-size: 0.875rem;
  }

  /* Recommendations */
  .recommendation-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .recommendation-item {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.75rem;
    background: #f9fafb;
    border-radius: 8px;
  }

  .recommendation-item svg {
    flex-shrink: 0;
    margin-top: 2px;
    color: #8b5cf6;
  }

  /* Patterns */
  .patterns-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .pattern-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    border: 2px solid transparent;
    transition: all 0.2s;
  }

  .pattern-card.negative {
    border-color: #fee2e2;
  }

  .pattern-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  .pattern-header h4 {
    font-size: 1rem;
    margin: 0;
  }

  .frequency {
    background: #f3f4f6;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.75rem;
    color: #6b7280;
  }

  .pattern-impact {
    display: flex;
    justify-content: space-between;
    padding: 0.75rem;
    background: #f9fafb;
    border-radius: 6px;
    margin-bottom: 1rem;
  }

  .pattern-description {
    color: #6b7280;
    font-size: 0.875rem;
    line-height: 1.6;
    margin-bottom: 1rem;
  }

  .pattern-recommendation {
    font-size: 0.875rem;
    color: #374151;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }

  /* Streaks */
  .streaks-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
  }

  .streak-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }

  .streak-card h4 {
    font-size: 1rem;
    margin-bottom: 1rem;
    color: #6b7280;
  }

  .streak-value {
    font-size: 3rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 0.5rem;
  }

  .streak-type {
    text-transform: capitalize;
    font-size: 0.875rem;
    color: #6b7280;
  }

  .current-winning .streak-value {
    color: #10b981;
  }

  .current-losing .streak-value {
    color: #ef4444;
  }

  /* Behavioral */
  .improvement-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-bottom: 2rem;
  }

  .improvement-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: #fef3c7;
    border-radius: 8px;
    color: #92400e;
  }

  .improvement-item svg {
    color: #f59e0b;
  }

  /* Emotions */
  .emotions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .emotion-card {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }

  .emotion-card h5 {
    font-size: 0.875rem;
    margin-bottom: 0.75rem;
    color: #374151;
  }

  .emotion-stats {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .stat {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
  }

  .emotion-insights {
    background: #f9fafb;
    padding: 1rem;
    border-radius: 8px;
  }

  .emotion-insights p {
    margin: 0.5rem 0;
    font-size: 0.875rem;
  }

  /* Market */
  .market-regime-section {
    margin-bottom: 2rem;
  }

  .regime-card {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }

  .regime-display {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 1rem 0;
  }

  .regime-type {
    font-size: 1.5rem;
    font-weight: 700;
  }

  .volatility {
    background: #f3f4f6;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
  }

  .regime-recommendation {
    color: #6b7280;
    font-style: italic;
  }

  /* Edge Table */
  .edge-table {
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }

  .edge-header,
  .edge-row {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
    padding: 1rem;
    align-items: center;
  }

  .edge-header {
    background: #f9fafb;
    font-weight: 600;
    font-size: 0.875rem;
    color: #6b7280;
  }

  .edge-row {
    border-bottom: 1px solid #e5e7eb;
    transition: background 0.2s;
  }

  .edge-row:hover {
    background: #f9fafb;
  }

  .strategy-name {
    font-weight: 500;
  }

  .confidence-level {
    color: #6b7280;
  }

  /* Market Levels */
  .levels-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }

  .levels-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }

  .levels-card h5 {
    font-size: 1rem;
    margin-bottom: 1rem;
    color: #374151;
  }

  .level-item {
    padding: 0.5rem 1rem;
    margin-bottom: 0.5rem;
    border-radius: 6px;
    font-weight: 500;
    text-align: center;
  }

  .level-item.support {
    background: #d1fae5;
    color: #065f46;
  }

  .level-item.resistance {
    background: #fee2e2;
    color: #991b1b;
  }

  /* Utilities */
  .positive {
    color: #10b981;
  }

  .negative {
    color: #ef4444;
  }

  .loading-container,
  .error-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 400px;
    gap: 1rem;
  }

  .error-container h3 {
    margin: 0;
  }

  .error-container button {
    padding: 0.75rem 1.5rem;
    background: #8b5cf6;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .error-container button:hover {
    background: #7c3aed;
  }

  @media (max-width: 1024px) {
    .score-cards {
      grid-template-columns: 1fr;
    }

    .insight-cards {
      grid-template-columns: 1fr;
    }

    .insights-grid {
      grid-template-columns: 1fr;
    }

    .tabs {
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }
  }

  @media (max-width: 768px) {
    .ai-insights-page {
      padding: 1rem;
    }

    .header-content {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .patterns-grid {
      grid-template-columns: 1fr;
    }

    .streaks-grid {
      grid-template-columns: 1fr;
    }

    .edge-header,
    .edge-row {
      font-size: 0.75rem;
    }
  }
</style>