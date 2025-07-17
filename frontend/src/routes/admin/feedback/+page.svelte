<script lang="ts">
  import { onMount } from 'svelte';
  import { 
    TrendingUp, TrendingDown, AlertCircle, CheckCircle, 
    Clock, Users, DollarSign, Filter, Search, ChevronDown
  } from 'lucide-svelte';
  import { feedbackApi } from '$lib/api/feedback';
  import type { 
    FeedbackAnalytics, FeedbackItem, FeedbackHeatmapData,
    ImpactAnalysis 
  } from '$lib/api/feedback';
  import MetricCard from '$lib/components/MetricCard.svelte';

  let analytics: FeedbackAnalytics | null = null;
  let feedbackList: FeedbackItem[] = [];
  let heatmapData: FeedbackHeatmapData[] = [];
  let impactAnalysis: ImpactAnalysis | null = null;
  let resolutionStats: any = null;
  let loading = true;
  let selectedPattern: string | null = null;
  let patternDetails: any = null;

  // Filters
  let statusFilter = '';
  let typeFilter = '';
  let severityFilter = '';
  let searchQuery = '';

  // Real-time updates
  let recentFeedback: FeedbackItem[] = [];
  let criticalIssues: FeedbackItem[] = [];

  onMount(async () => {
    await loadDashboardData();
    // Refresh data every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  });

  async function loadDashboardData() {
    try {
      const dashboardData = await feedbackApi.getDashboard();
      
      analytics = await feedbackApi.getAnalytics();
      recentFeedback = dashboardData.recent_feedback;
      criticalIssues = dashboardData.critical_issues;
      heatmapData = dashboardData.feedback_heatmap;
      impactAnalysis = dashboardData.impact_analysis;
      resolutionStats = dashboardData.resolution_stats;
      
      await loadFeedbackList();
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      loading = false;
    }
  }

  async function loadFeedbackList() {
    try {
      feedbackList = await feedbackApi.list({
        status: statusFilter || undefined,
        type: typeFilter || undefined,
        severity: severityFilter || undefined
      });
    } catch (error) {
      console.error('Failed to load feedback list:', error);
    }
  }

  async function viewPatternDetails(patternId: string) {
    selectedPattern = patternId;
    patternDetails = await feedbackApi.getPatternDetails(patternId);
  }

  async function updateStatus(feedbackId: string, newStatus: string) {
    try {
      await feedbackApi.updateStatus(feedbackId, newStatus);
      await loadDashboardData();
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  }

  async function trainPatternDetection() {
    try {
      const result = await feedbackApi.trainPatternDetection();
      alert(`Pattern detection updated! ${result.patterns_discovered} new patterns found.`);
      await loadDashboardData();
    } catch (error) {
      console.error('Failed to train pattern detection:', error);
    }
  }

  $: filteredFeedback = feedbackList.filter(item => {
    if (searchQuery && !item.title.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  function getSeverityColor(severity: string): string {
    const colors = {
      critical: '#ef4444',
      high: '#f97316',
      medium: '#eab308',
      low: '#3b82f6'
    };
    return colors[severity] || '#6b7280';
  }

  function getStatusBadgeClass(status: string): string {
    const classes = {
      new: 'badge-new',
      investigating: 'badge-investigating',
      in_progress: 'badge-progress',
      resolved: 'badge-resolved',
      closed: 'badge-closed'
    };
    return classes[status] || '';
  }
</script>

<div class="feedback-dashboard">
  <div class="dashboard-header">
    <h1>Feedback Analytics Dashboard</h1>
    <div class="header-actions">
      <button class="train-button" on:click={trainPatternDetection}>
        🤖 Retrain Pattern Detection
      </button>
    </div>
  </div>

  {#if loading}
    <div class="loading">Loading dashboard data...</div>
  {:else if analytics}
    <!-- Key Metrics -->
    <div class="metrics-grid">
      <MetricCard
        title="Total Feedback"
        value={resolutionStats?.total_feedback || 0}
        icon={Users}
        trend={0}
      />
      <MetricCard
        title="Resolution Rate"
        value={`${resolutionStats?.resolution_rate?.toFixed(1) || 0}%`}
        icon={CheckCircle}
        trend={5}
      />
      <MetricCard
        title="Avg Resolution Time"
        value={`${analytics.resolution_time.average_hours.toFixed(1)}h`}
        icon={Clock}
        trend={-10}
      />
      <MetricCard
        title="Revenue at Risk"
        value={`$${impactAnalysis?.revenue_at_risk?.toFixed(0) || 0}`}
        icon={DollarSign}
        trend={0}
        trendDirection="negative"
      />
    </div>

    <!-- Critical Issues Alert -->
    {#if criticalIssues.length > 0}
      <div class="critical-alert">
        <AlertCircle size={20} />
        <span>{criticalIssues.length} Critical Issues Require Immediate Attention</span>
      </div>
    {/if}

    <!-- Main Content Grid -->
    <div class="content-grid">
      <!-- Top Issues -->
      <div class="panel">
        <h2>Top Issues</h2>
        <div class="issues-list">
          {#each analytics.top_issues as issue}
            <div class="issue-item">
              <div class="issue-info">
                <span class="issue-title">{issue.title}</span>
                <span 
                  class="severity-badge" 
                  style="background: {getSeverityColor(issue.severity)}"
                >
                  {issue.severity}
                </span>
              </div>
              <div class="issue-stats">
                <span class="count">{issue.count} reports</span>
                <button 
                  class="view-pattern"
                  on:click={() => viewPatternDetails(issue.pattern_id)}
                >
                  View Pattern
                </button>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <!-- Trending Issues -->
      <div class="panel">
        <h2>Trending Issues</h2>
        <div class="trending-list">
          {#each analytics.trending_issues as trend}
            <div class="trending-item">
              <div class="trend-info">
                <TrendingUp size={16} color="#ef4444" />
                <span>{trend.title}</span>
              </div>
              <span class="growth-rate">+{(trend.growth_rate * 100).toFixed(0)}%</span>
            </div>
          {/each}
        </div>
      </div>

      <!-- Feedback Heatmap -->
      <div class="panel full-width">
        <h2>Feedback Heatmap by Page</h2>
        <div class="heatmap">
          {#each heatmapData.slice(0, 10) as page}
            <div class="heatmap-row">
              <span class="page-url">{page.page}</span>
              <div class="issue-bars">
                {#each Object.entries(page.severity_breakdown) as [severity, count]}
                  <div 
                    class="severity-bar"
                    style="background: {getSeverityColor(severity)}; width: {(count / page.issue_count) * 100}%"
                    title="{severity}: {count}"
                  />
                {/each}
              </div>
              <span class="total-count">{page.issue_count}</span>
            </div>
          {/each}
        </div>
      </div>
    </div>

    <!-- Feedback List -->
    <div class="panel feedback-list-panel">
      <div class="panel-header">
        <h2>All Feedback</h2>
        <div class="filters">
          <select bind:value={statusFilter} on:change={loadFeedbackList}>
            <option value="">All Status</option>
            <option value="new">New</option>
            <option value="investigating">Investigating</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
          <select bind:value={typeFilter} on:change={loadFeedbackList}>
            <option value="">All Types</option>
            <option value="bug">Bug</option>
            <option value="feature">Feature</option>
            <option value="performance">Performance</option>
            <option value="ux">UX</option>
            <option value="other">Other</option>
          </select>
          <select bind:value={severityFilter} on:change={loadFeedbackList}>
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <div class="search-box">
            <Search size={16} />
            <input 
              type="text" 
              placeholder="Search feedback..."
              bind:value={searchQuery}
            />
          </div>
        </div>
      </div>

      <div class="feedback-table">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Type</th>
              <th>Severity</th>
              <th>Status</th>
              <th>User</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each filteredFeedback as item}
              <tr>
                <td class="id">#{item.id.slice(0, 8)}</td>
                <td class="title">{item.title}</td>
                <td>
                  <span class="type-badge">{item.type}</span>
                </td>
                <td>
                  <span 
                    class="severity-badge"
                    style="background: {getSeverityColor(item.severity)}"
                  >
                    {item.severity}
                  </span>
                </td>
                <td>
                  <span class="status-badge {getStatusBadgeClass(item.status)}">
                    {item.status.replace('_', ' ')}
                  </span>
                </td>
                <td>{item.subscription_tier || 'Guest'}</td>
                <td>{new Date(item.created_at).toLocaleDateString()}</td>
                <td>
                  <div class="actions">
                    <select 
                      value={item.status}
                      on:change={(e) => updateStatus(item.id, e.target.value)}
                    >
                      <option value="new">New</option>
                      <option value="investigating">Investigating</option>
                      <option value="in_progress">In Progress</option>
                      <option value="resolved">Resolved</option>
                      <option value="closed">Closed</option>
                    </select>
                  </div>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {/if}

  <!-- Pattern Details Modal -->
  {#if selectedPattern && patternDetails}
    <div class="modal-overlay" on:click={() => selectedPattern = null}>
      <div class="modal" on:click|stopPropagation>
        <h2>Pattern Analysis</h2>
        <div class="pattern-details">
          <div class="pattern-info">
            <p><strong>Pattern ID:</strong> {selectedPattern}</p>
            <p><strong>Type:</strong> {patternDetails.pattern.pattern_type}</p>
            <p><strong>Occurrences:</strong> {patternDetails.pattern.occurrences}</p>
            <p><strong>Affected Users:</strong> {patternDetails.pattern.affected_users}</p>
          </div>
          
          <h3>Suggested Fixes</h3>
          <ul class="suggested-fixes">
            {#each patternDetails.suggested_fixes as fix}
              <li>{fix}</li>
            {/each}
          </ul>

          <h3>Related Feedback</h3>
          <div class="related-feedback">
            {#each patternDetails.related_feedback.slice(0, 5) as feedback}
              <div class="feedback-preview">
                <strong>{feedback.title}</strong>
                <p>{feedback.description.slice(0, 200)}...</p>
                <small>{new Date(feedback.created_at).toLocaleDateString()}</small>
              </div>
            {/each}
          </div>
        </div>
        <button class="close-modal" on:click={() => selectedPattern = null}>
          Close
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  .feedback-dashboard {
    max-width: 1400px;
    margin: 0 auto;
    padding: 2rem;
  }

  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  .dashboard-header h1 {
    margin: 0;
    font-size: 2rem;
    font-weight: 700;
  }

  .header-actions {
    display: flex;
    gap: 1rem;
  }

  .train-button {
    padding: 0.75rem 1.5rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .train-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  .loading {
    text-align: center;
    padding: 4rem;
    color: #6b7280;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .critical-alert {
    background: #fee2e2;
    color: #991b1b;
    padding: 1rem;
    border-radius: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 2rem;
    font-weight: 600;
  }

  .content-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    margin-bottom: 2rem;
  }

  .panel {
    background: white;
    border-radius: 0.75rem;
    padding: 1.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  }

  .panel.full-width {
    grid-column: 1 / -1;
  }

  .panel h2 {
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
    font-weight: 600;
  }

  .issues-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .issue-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: #f9fafb;
    border-radius: 0.5rem;
  }

  .issue-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .issue-title {
    font-weight: 500;
    color: #111827;
  }

  .severity-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .issue-stats {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .count {
    color: #6b7280;
    font-size: 0.875rem;
  }

  .view-pattern {
    padding: 0.375rem 0.75rem;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    cursor: pointer;
    transition: background 0.2s;
  }

  .view-pattern:hover {
    background: #5a67d8;
  }

  .trending-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .trending-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem;
    background: #fef3c7;
    border-radius: 0.375rem;
  }

  .trend-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .growth-rate {
    font-weight: 600;
    color: #d97706;
  }

  .heatmap {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .heatmap-row {
    display: grid;
    grid-template-columns: 300px 1fr 60px;
    align-items: center;
    gap: 1rem;
  }

  .page-url {
    font-size: 0.875rem;
    color: #374151;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .issue-bars {
    display: flex;
    height: 20px;
    border-radius: 0.25rem;
    overflow: hidden;
  }

  .severity-bar {
    height: 100%;
    transition: width 0.3s;
  }

  .total-count {
    text-align: right;
    font-weight: 600;
    color: #6b7280;
  }

  .feedback-list-panel {
    margin-top: 2rem;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }

  .filters {
    display: flex;
    gap: 1rem;
    align-items: center;
  }

  .filters select {
    padding: 0.5rem 1rem;
    border: 1px solid #e5e7eb;
    border-radius: 0.375rem;
    font-size: 0.875rem;
  }

  .search-box {
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
    border: 1px solid #e5e7eb;
    border-radius: 0.375rem;
    background: white;
  }

  .search-box input {
    border: none;
    outline: none;
    margin-left: 0.5rem;
    font-size: 0.875rem;
  }

  .feedback-table {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  th {
    text-align: left;
    padding: 0.75rem;
    border-bottom: 2px solid #e5e7eb;
    font-weight: 600;
    color: #374151;
    font-size: 0.875rem;
  }

  td {
    padding: 0.75rem;
    border-bottom: 1px solid #f3f4f6;
    font-size: 0.875rem;
  }

  .id {
    font-family: monospace;
    color: #6b7280;
  }

  .title {
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .type-badge {
    padding: 0.25rem 0.5rem;
    background: #e5e7eb;
    border-radius: 0.25rem;
    font-size: 0.75rem;
  }

  .status-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .badge-new { background: #dbeafe; color: #1e40af; }
  .badge-investigating { background: #fef3c7; color: #d97706; }
  .badge-progress { background: #e0e7ff; color: #4338ca; }
  .badge-resolved { background: #d1fae5; color: #065f46; }
  .badge-closed { background: #e5e7eb; color: #374151; }

  .actions select {
    padding: 0.25rem 0.5rem;
    border: 1px solid #e5e7eb;
    border-radius: 0.25rem;
    font-size: 0.75rem;
  }

  /* Modal */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal {
    background: white;
    border-radius: 0.75rem;
    padding: 2rem;
    max-width: 600px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
  }

  .modal h2 {
    margin: 0 0 1.5rem 0;
  }

  .pattern-info {
    background: #f9fafb;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1.5rem;
  }

  .pattern-info p {
    margin: 0.25rem 0;
  }

  .suggested-fixes {
    list-style: none;
    padding: 0;
    margin: 0 0 1.5rem 0;
  }

  .suggested-fixes li {
    padding: 0.75rem;
    background: #eef2ff;
    border-left: 3px solid #667eea;
    margin-bottom: 0.5rem;
  }

  .related-feedback {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .feedback-preview {
    padding: 1rem;
    background: #f9fafb;
    border-radius: 0.5rem;
  }

  .feedback-preview strong {
    display: block;
    margin-bottom: 0.5rem;
    color: #111827;
  }

  .feedback-preview p {
    color: #6b7280;
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
  }

  .feedback-preview small {
    color: #9ca3af;
    font-size: 0.75rem;
  }

  .close-modal {
    width: 100%;
    padding: 0.75rem;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }

  .close-modal:hover {
    background: #5a67d8;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .content-grid {
      grid-template-columns: 1fr;
    }

    .metrics-grid {
      grid-template-columns: 1fr 1fr;
    }

    .filters {
      flex-wrap: wrap;
    }

    .heatmap-row {
      grid-template-columns: 150px 1fr 40px;
    }
  }
</style>