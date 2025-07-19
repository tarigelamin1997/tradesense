<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { Plus, Copy, Trash2, Share2, Lock, Globe, Layout } from 'lucide-svelte';
  import { dashboardsApi, type Dashboard, type DashboardTemplate } from '$lib/api/dashboards.js';
  import { billingApi } from '$lib/api/billing.js';
  import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
  import { formatDistanceToNow } from 'date-fns';

  let loading = true;
  let dashboards: Dashboard[] = [];
  let templates: DashboardTemplate[] = [];
  let showCreateModal = false;
  let userPlan: 'free' | 'pro' | 'enterprise' = 'free';
  let error = '';
  
  // Create dashboard form
  let newDashboardName = '';
  let selectedTemplate = 'custom';
  let isCreating = false;

  // Limits by plan
  const planLimits = {
    free: { dashboards: 1, widgets: 4 },
    pro: { dashboards: 5, widgets: 10 },
    enterprise: { dashboards: 999, widgets: 999 }
  };

  async function loadDashboards() {
    try {
      loading = true;
      error = '';

      // Get user plan
      try {
        const subscription = await billingApi.getSubscription();
        if (subscription?.plan_id.includes('enterprise')) userPlan = 'enterprise';
        else if (subscription?.plan_id.includes('pro')) userPlan = 'pro';
      } catch (e) {
        // Default to free
      }

      // Load dashboards and templates
      const [dashboardsData, templatesData] = await Promise.all([
        dashboardsApi.list(),
        dashboardsApi.getTemplates()
      ]);

      dashboards = dashboardsData.dashboards;
      templates = templatesData;
    } catch (err: any) {
      error = err.message || 'Failed to load dashboards';
      console.error('Error loading dashboards:', err);
    } finally {
      loading = false;
    }
  }

  async function createDashboard() {
    if (!newDashboardName.trim()) return;

    try {
      isCreating = true;
      const dashboard = await dashboardsApi.create(
        newDashboardName.trim(),
        selectedTemplate
      );
      goto(`/dashboards/${dashboard.id}`);
    } catch (err: any) {
      error = err.message || 'Failed to create dashboard';
    } finally {
      isCreating = false;
    }
  }

  async function cloneDashboard(dashboard: Dashboard) {
    const name = prompt('Enter name for cloned dashboard:', `${dashboard.name} (Copy)`);
    if (!name) return;

    try {
      await dashboardsApi.clone(dashboard.id, name);
      await loadDashboards();
    } catch (err: any) {
      error = err.message || 'Failed to clone dashboard';
    }
  }

  async function deleteDashboard(dashboard: Dashboard) {
    if (!confirm(`Delete dashboard "${dashboard.name}"? This cannot be undone.`)) return;

    try {
      await dashboardsApi.delete(dashboard.id);
      await loadDashboards();
    } catch (err: any) {
      error = err.message || 'Failed to delete dashboard';
    }
  }

  function canCreateMore() {
    return dashboards.length < planLimits[userPlan].dashboards;
  }

  onMount(() => {
    loadDashboards();
  });
</script>

<svelte:head>
  <title>Dashboards - TradeSense</title>
</svelte:head>

<div class="container">
  <header class="page-header">
    <div>
      <h1>Custom Dashboards</h1>
      <p>Build personalized trading dashboards with drag-and-drop widgets</p>
    </div>
    <button
      class="create-button"
      on:click={() => showCreateModal = true}
      disabled={!canCreateMore()}
    >
      <Plus size={20} />
      Create Dashboard
    </button>
  </header>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  {#if !canCreateMore() && userPlan !== 'enterprise'}
    <div class="upgrade-banner">
      <p>
        You've reached the limit of {planLimits[userPlan].dashboards} dashboard{planLimits[userPlan].dashboards > 1 ? 's' : ''} 
        for your {userPlan} plan.
      </p>
      <a href="/pricing" class="upgrade-link">Upgrade to create more →</a>
    </div>
  {/if}

  {#if loading}
    <div class="dashboard-grid">
      {#each Array(3) as _}
        <LoadingSkeleton type="card" height="200px" />
      {/each}
    </div>
  {:else if dashboards.length === 0}
    <div class="empty-state">
      <Layout size={48} />
      <h2>No dashboards yet</h2>
      <p>Create your first custom dashboard to visualize your trading data</p>
      <button class="primary-button" on:click={() => showCreateModal = true}>
        Create Your First Dashboard
      </button>
    </div>
  {:else}
    <div class="dashboard-grid">
      {#each dashboards as dashboard}
        <div class="dashboard-card">
          <div class="card-header">
            <h3>{dashboard.name}</h3>
            <div class="card-badges">
              {#if dashboard.is_public}
                <Globe size={16} />
              {:else}
                <Lock size={16} />
              {/if}
            </div>
          </div>
          
          {#if dashboard.description}
            <p class="card-description">{dashboard.description}</p>
          {/if}

          <div class="card-stats">
            <span>{dashboard.widgets.length} widgets</span>
            <span>•</span>
            <span>Updated {formatDistanceToNow(new Date(dashboard.updated_at))} ago</span>
          </div>

          <div class="card-actions">
            <a href={`/dashboards/${dashboard.id}`} class="action-button primary">
              Open Dashboard
            </a>
            <button 
              class="action-button" 
              on:click={() => cloneDashboard(dashboard)}
              title="Clone dashboard"
            >
              <Copy size={16} />
            </button>
            <button 
              class="action-button" 
              on:click={() => deleteDashboard(dashboard)}
              title="Delete dashboard"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<!-- Create Dashboard Modal -->
{#if showCreateModal}
  <div class="modal-overlay" on:click={() => showCreateModal = false}>
    <div class="modal" on:click|stopPropagation>
      <h2>Create New Dashboard</h2>
      
      <form on:submit|preventDefault={createDashboard}>
        <div class="form-group">
          <label for="name">Dashboard Name</label>
          <input
            id="name"
            type="text"
            bind:value={newDashboardName}
            placeholder="My Trading Dashboard"
            required
            maxlength="100"
          />
        </div>

        <div class="form-group">
          <label>Choose a Template</label>
          <div class="template-grid">
            {#each templates as template}
              <label class="template-option">
                <input
                  type="radio"
                  name="template"
                  value={template.id}
                  bind:group={selectedTemplate}
                />
                <div class="template-card">
                  <h4>{template.name}</h4>
                  <p>{template.description}</p>
                </div>
              </label>
            {/each}
          </div>
        </div>

        <div class="modal-actions">
          <button type="button" class="secondary-button" on:click={() => showCreateModal = false}>
            Cancel
          </button>
          <button type="submit" class="primary-button" disabled={isCreating}>
            {isCreating ? 'Creating...' : 'Create Dashboard'}
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<style>
  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }

  .page-header h1 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
  }

  .page-header p {
    color: #666;
  }

  .create-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: #10b981;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .create-button:hover:not(:disabled) {
    background: #059669;
    transform: translateY(-1px);
  }

  .create-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .upgrade-banner {
    background: #fef3c7;
    border: 1px solid #f59e0b;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .upgrade-banner p {
    margin: 0;
    color: #92400e;
  }

  .upgrade-link {
    color: #dc2626;
    text-decoration: none;
    font-weight: 500;
  }

  .upgrade-link:hover {
    text-decoration: underline;
  }

  .dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
  }

  .dashboard-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.2s;
  }

  .dashboard-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .card-header h3 {
    font-size: 1.25rem;
    margin: 0;
  }

  .card-badges {
    display: flex;
    gap: 0.5rem;
    color: #6b7280;
  }

  .card-description {
    color: #6b7280;
    margin-bottom: 1rem;
    font-size: 0.875rem;
  }

  .card-stats {
    display: flex;
    gap: 0.5rem;
    color: #9ca3af;
    font-size: 0.875rem;
    margin-bottom: 1rem;
  }

  .card-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .action-button {
    padding: 0.5rem 1rem;
    border: 1px solid #e5e7eb;
    background: white;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
    color: #374151;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
  }

  .action-button:hover {
    background: #f9fafb;
    border-color: #d1d5db;
  }

  .action-button.primary {
    background: #10b981;
    color: white;
    border-color: #10b981;
    flex: 1;
    justify-content: center;
  }

  .action-button.primary:hover {
    background: #059669;
  }

  .empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #6b7280;
  }

  .empty-state h2 {
    margin: 1rem 0;
    color: #1f2937;
  }

  .empty-state p {
    margin-bottom: 2rem;
  }

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
    border-radius: 12px;
    padding: 2rem;
    max-width: 600px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
  }

  .modal h2 {
    margin-bottom: 1.5rem;
  }

  .form-group {
    margin-bottom: 1.5rem;
  }

  .form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: #374151;
  }

  .form-group input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    font-size: 1rem;
  }

  .template-grid {
    display: grid;
    gap: 1rem;
  }

  .template-option {
    cursor: pointer;
  }

  .template-option input {
    display: none;
  }

  .template-card {
    padding: 1rem;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    transition: all 0.2s;
  }

  .template-option input:checked + .template-card {
    border-color: #10b981;
    background: #f0fdf4;
  }

  .template-card h4 {
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
  }

  .template-card p {
    margin: 0;
    font-size: 0.875rem;
    color: #6b7280;
  }

  .modal-actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
    margin-top: 2rem;
  }

  .primary-button,
  .secondary-button {
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
  }

  .primary-button {
    background: #10b981;
    color: white;
  }

  .primary-button:hover:not(:disabled) {
    background: #059669;
  }

  .primary-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .secondary-button {
    background: #f3f4f6;
    color: #374151;
  }

  .secondary-button:hover {
    background: #e5e7eb;
  }

  .error {
    background: #fee;
    color: #dc2626;
    padding: 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
  }

  @media (max-width: 768px) {
    .container {
      padding: 1rem;
    }

    .page-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .dashboard-grid {
      grid-template-columns: 1fr;
    }

    .upgrade-banner {
      flex-direction: column;
      gap: 1rem;
      text-align: center;
    }
  }
</style>