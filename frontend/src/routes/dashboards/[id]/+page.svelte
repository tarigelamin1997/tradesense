<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { dndzone } from 'svelte-dnd-action';
  import { flip } from 'svelte/animate';
  import { 
    Plus, Save, Eye, EyeOff, Settings, X, Move, 
    Maximize2, BarChart2, PieChart, TrendingUp, 
    Table, Activity, DollarSign, Calendar, FileText,
    Download, FileImage, File
  } from 'lucide-svelte';
  import { 
    dashboardsApi, 
    type Dashboard, 
    type WidgetConfig,
    type WidgetType,
    type DataSource 
  } from '$lib/api/dashboards';
  import { billingApi } from '$lib/api/billing';
  import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
  import { widgetComponents, sampleDataGenerators, defaultWidgetSizes } from '$lib/components/dashboard/widgets';

  let dashboard: Dashboard | null = null;
  let loading = true;
  let saving = false;
  let error = '';
  let editMode = true;
  let showWidgetPanel = false;
  let selectedWidget: WidgetConfig | null = null;
  let userPlan: 'free' | 'pro' | 'enterprise' = 'free';
  let widgetTypes: WidgetType[] = [];
  let dataSources: DataSource[] = [];
  let eventSource: EventSource | null = null;
  let widgetData: Record<string, any> = {};
  let resizing = false;
  let resizeWidget: WidgetConfig | null = null;
  let resizeDirection: 'se' | 'e' | 's' = 'se';
  let resizeStartPos = { x: 0, y: 0 };
  let resizeStartSize = { width: 0, height: 0 };
  let showExportMenu = false;
  let exporting = false;

  const dashboardId = $page.params.id;

  // Grid settings
  const GRID_COLS = 12;
  const ROW_HEIGHT = 80;
  const MARGIN = 10;

  // Plan limits
  const planLimits = {
    free: { widgets: 4 },
    pro: { widgets: 10 },
    enterprise: { widgets: 999 }
  };

  // Widget icon mapping
  const widgetIcons: Record<string, any> = {
    line_chart: TrendingUp,
    bar_chart: BarChart2,
    pie_chart: PieChart,
    table: Table,
    metric_card: DollarSign,
    gauge: Activity,
    pnl_calendar: Calendar,
    text_markdown: FileText,
    candlestick: BarChart2,
    heatmap: Activity,
    drawdown_chart: TrendingUp,
    live_market: Activity
  };

  async function loadDashboard() {
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

      // Load dashboard and metadata
      const [dashboardData, typesData, sourcesData] = await Promise.all([
        dashboardsApi.get(dashboardId),
        dashboardsApi.getWidgetTypes(),
        dashboardsApi.getDataSources()
      ]);

      dashboard = dashboardData;
      widgetTypes = typesData;
      dataSources = sourcesData;

      // Load initial widget data
      await loadAllWidgetData();

      // Set up real-time updates if not in edit mode
      if (!editMode) {
        setupRealtimeUpdates();
      }
    } catch (err: any) {
      error = err.message || 'Failed to load dashboard';
      console.error('Error loading dashboard:', err);
    } finally {
      loading = false;
    }
  }

  async function loadAllWidgetData() {
    if (!dashboard) return;

    try {
      const data = await dashboardsApi.getDashboardData(dashboardId);
      widgetData = data.widget_data;
    } catch (err) {
      console.error('Error loading widget data:', err);
    }
  }

  async function saveDashboard() {
    if (!dashboard) return;

    try {
      saving = true;
      await dashboardsApi.update(dashboardId, {
        name: dashboard.name,
        description: dashboard.description,
        layout: dashboard.layout,
        tags: dashboard.tags,
        is_public: dashboard.is_public
      });

      // Save widget positions
      const positions = dashboard.widgets.map(w => ({
        widget_id: w.id,
        position: w.position
      }));
      await dashboardsApi.reorderWidgets(dashboardId, positions);
    } catch (err: any) {
      error = err.message || 'Failed to save dashboard';
    } finally {
      saving = false;
    }
  }

  async function addWidget(type: string) {
    if (!dashboard) return;
    if (dashboard.widgets.length >= planLimits[userPlan].widgets) {
      error = `Widget limit reached. Upgrade to ${userPlan === 'free' ? 'Pro' : 'Enterprise'} for more widgets.`;
      return;
    }

    const newWidget: Omit<WidgetConfig, 'id'> = {
      type,
      title: `New ${type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`,
      position: findEmptyPosition(type),
      data_source: 'trades',
      data_config: {},
      refresh_interval: 300,
      interactive: true,
      exportable: true,
      linked_widgets: [],
      custom_styles: {}
    };

    try {
      dashboard = await dashboardsApi.addWidget(dashboardId, newWidget);
      showWidgetPanel = false;
    } catch (err: any) {
      error = err.message || 'Failed to add widget';
    }
  }

  async function removeWidget(widgetId: string) {
    if (!dashboard || !confirm('Remove this widget?')) return;

    try {
      dashboard = await dashboardsApi.removeWidget(dashboardId, widgetId);
    } catch (err: any) {
      error = err.message || 'Failed to remove widget';
    }
  }

  async function updateWidget(widgetId: string, updates: Partial<WidgetConfig>) {
    if (!dashboard) return;

    try {
      dashboard = await dashboardsApi.updateWidget(dashboardId, widgetId, updates);
      // Reload data for this widget
      const data = await dashboardsApi.getWidgetData(dashboardId, widgetId);
      widgetData[widgetId] = data;
    } catch (err: any) {
      error = err.message || 'Failed to update widget';
    }
  }

  function findEmptyPosition(widgetType: string) {
    if (!dashboard) return { x: 0, y: 0, width: 4, height: 3 };

    const defaultSize = defaultWidgetSizes[widgetType] || { width: 4, height: 3 };
    
    // Find the lowest empty position
    let y = 0;
    while (true) {
      for (let x = 0; x <= GRID_COLS - defaultSize.width; x++) {
        const position = { x, y, ...defaultSize };
        if (!isPositionOccupied(position)) {
          return position;
        }
      }
      y++;
    }
  }

  function isPositionOccupied(newPos: any) {
    if (!dashboard) return false;

    return dashboard.widgets.some(widget => {
      const pos = widget.position;
      return !(
        newPos.x + newPos.width <= pos.x ||
        newPos.x >= pos.x + pos.width ||
        newPos.y + newPos.height <= pos.y ||
        newPos.y >= pos.y + pos.height
      );
    });
  }

  function handleDndConsider(e: CustomEvent) {
    if (!dashboard) return;
    dashboard.widgets = e.detail.items;
  }

  function handleDndFinalize(e: CustomEvent) {
    if (!dashboard) return;
    dashboard.widgets = e.detail.items;
    saveDashboard();
  }

  function toggleEditMode() {
    editMode = !editMode;
    if (editMode) {
      // Stop real-time updates in edit mode
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
    } else {
      // Start real-time updates in view mode
      setupRealtimeUpdates();
      loadAllWidgetData();
    }
  }

  function setupRealtimeUpdates() {
    if (eventSource) return;

    eventSource = dashboardsApi.streamDashboardData(dashboardId);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.widget_data) {
          widgetData = { ...widgetData, ...data.widget_data };
        }
      } catch (err) {
        console.error('Error parsing SSE data:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE error:', err);
      eventSource?.close();
      eventSource = null;
      // Retry after 5 seconds
      setTimeout(setupRealtimeUpdates, 5000);
    };
  }

  function renderWidget(widget: WidgetConfig) {
    return widgetComponents[widget.type] || null;
  }
  
  function getWidgetData(widget: WidgetConfig) {
    const data = widgetData[widget.id];
    if (data) return data;
    
    // Use sample data if no real data available
    const generator = sampleDataGenerators[widget.type];
    return generator ? generator() : null;
  }

  function handleClickOutside(event: MouseEvent) {
    const exportDropdown = document.querySelector('.export-dropdown');
    if (exportDropdown && !exportDropdown.contains(event.target as Node)) {
      showExportMenu = false;
    }
  }

  onMount(() => {
    loadDashboard();
    document.addEventListener('click', handleClickOutside);
    
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  });

  function startResize(e: MouseEvent, widget: WidgetConfig, direction: 'se' | 'e' | 's') {
    e.preventDefault();
    e.stopPropagation();
    
    resizing = true;
    resizeWidget = widget;
    resizeDirection = direction;
    resizeStartPos = { x: e.clientX, y: e.clientY };
    resizeStartSize = { width: widget.position.width, height: widget.position.height };
    
    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', stopResize);
    document.body.style.cursor = direction === 'e' ? 'ew-resize' : direction === 's' ? 'ns-resize' : 'nwse-resize';
  }
  
  function handleResize(e: MouseEvent) {
    if (!resizing || !resizeWidget) return;
    
    const deltaX = Math.round((e.clientX - resizeStartPos.x) / (window.innerWidth / GRID_COLS));
    const deltaY = Math.round((e.clientY - resizeStartPos.y) / ROW_HEIGHT);
    
    let newWidth = resizeStartSize.width;
    let newHeight = resizeStartSize.height;
    
    if (resizeDirection === 'e' || resizeDirection === 'se') {
      newWidth = Math.max(2, Math.min(GRID_COLS - resizeWidget.position.x, resizeStartSize.width + deltaX));
    }
    
    if (resizeDirection === 's' || resizeDirection === 'se') {
      newHeight = Math.max(2, resizeStartSize.height + deltaY);
    }
    
    // Check if new size would overlap with other widgets
    const testPosition = {
      ...resizeWidget.position,
      width: newWidth,
      height: newHeight
    };
    
    const wouldOverlap = dashboard!.widgets.some(w => {
      if (w.id === resizeWidget!.id) return false;
      const pos = w.position;
      return !(
        testPosition.x + testPosition.width <= pos.x ||
        testPosition.x >= pos.x + pos.width ||
        testPosition.y + testPosition.height <= pos.y ||
        testPosition.y >= pos.y + pos.height
      );
    });
    
    if (!wouldOverlap) {
      resizeWidget.position.width = newWidth;
      resizeWidget.position.height = newHeight;
      dashboard = dashboard; // Trigger reactivity
    }
  }
  
  function stopResize() {
    if (!resizing || !resizeWidget) return;
    
    resizing = false;
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', stopResize);
    document.body.style.cursor = '';
    
    // Save the new position
    updateWidget(resizeWidget.id, {
      position: resizeWidget.position
    });
    
    resizeWidget = null;
  }

  async function exportDashboard(format: 'pdf' | 'png' | 'jpg') {
    try {
      exporting = true;
      showExportMenu = false;
      
      // Import libraries dynamically
      const [html2canvas, { jsPDF }] = await Promise.all([
        import('html2canvas'),
        import('jspdf')
      ]);
      
      // Get the dashboard grid element
      const element = document.querySelector('.dashboard-grid');
      if (!element) throw new Error('Dashboard grid not found');
      
      // Temporarily hide edit mode elements
      const wasEditMode = editMode;
      if (editMode) {
        editMode = false;
        await new Promise(resolve => setTimeout(resolve, 100)); // Wait for DOM update
      }
      
      // Configure html2canvas options
      const canvas = await html2canvas.default(element as HTMLElement, {
        scale: 2, // Higher quality
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff',
        windowWidth: element.scrollWidth,
        windowHeight: element.scrollHeight
      });
      
      // Restore edit mode
      if (wasEditMode) {
        editMode = true;
      }
      
      // Generate filename
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `${dashboard?.name || 'dashboard'}_${timestamp}`;
      
      if (format === 'pdf') {
        // Create PDF
        const imgWidth = 210; // A4 width in mm
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        const pdf = new jsPDF.default({
          orientation: imgHeight > imgWidth ? 'portrait' : 'landscape',
          unit: 'mm'
        });
        
        const pageHeight = pdf.internal.pageSize.height;
        let heightLeft = imgHeight;
        let position = 0;
        
        // Add first page
        pdf.addImage(
          canvas.toDataURL('image/png'),
          'PNG',
          0,
          position,
          imgWidth,
          imgHeight
        );
        heightLeft -= pageHeight;
        
        // Add additional pages if needed
        while (heightLeft > 0) {
          position = heightLeft - imgHeight;
          pdf.addPage();
          pdf.addImage(
            canvas.toDataURL('image/png'),
            'PNG',
            0,
            position,
            imgWidth,
            imgHeight
          );
          heightLeft -= pageHeight;
        }
        
        // Add metadata
        pdf.setProperties({
          title: dashboard?.name || 'TradeSense Dashboard',
          subject: 'Trading Dashboard Export',
          author: 'TradeSense',
          keywords: 'trading, dashboard, analytics',
          creator: 'TradeSense'
        });
        
        pdf.save(`${filename}.pdf`);
      } else {
        // Export as image
        const link = document.createElement('a');
        link.download = `${filename}.${format}`;
        link.href = canvas.toDataURL(`image/${format}`, 0.95);
        link.click();
      }
      
      // Show success message
      error = '';
    } catch (err: any) {
      error = `Export failed: ${err.message}`;
      console.error('Export error:', err);
    } finally {
      exporting = false;
    }
  }

  onDestroy(() => {
    if (eventSource) {
      eventSource.close();
    }
    // Clean up resize listeners
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', stopResize);
  });
</script>

<svelte:head>
  <title>{dashboard?.name || 'Dashboard'} - TradeSense</title>
</svelte:head>

{#if loading}
  <div class="loading-container">
    <LoadingSkeleton type="text" lines={2} width="300px" />
    <div class="skeleton-grid">
      {#each Array(4) as _}
        <LoadingSkeleton type="card" height="200px" />
      {/each}
    </div>
  </div>
{:else if error && !dashboard}
  <div class="error-container">
    <p>{error}</p>
    <a href="/dashboards">← Back to Dashboards</a>
  </div>
{:else if dashboard}
  <div class="dashboard-builder">
    <!-- Header -->
    <header class="builder-header">
      <div class="header-left">
        <h1>{dashboard.name}</h1>
        {#if dashboard.description}
          <p>{dashboard.description}</p>
        {/if}
      </div>
      <div class="header-actions">
        {#if editMode}
          <button class="icon-button" on:click={() => showWidgetPanel = !showWidgetPanel} title="Add Widget">
            <Plus size={20} />
          </button>
          <button class="icon-button" on:click={saveDashboard} disabled={saving} title="Save">
            <Save size={20} />
          </button>
        {/if}
        <button class="icon-button" on:click={toggleEditMode} title="{editMode ? 'Preview' : 'Edit'} Mode">
          {#if editMode}
            <Eye size={20} />
          {:else}
            <EyeOff size={20} />
          {/if}
        </button>
        <div class="export-dropdown">
          <button 
            class="icon-button" 
            on:click={() => showExportMenu = !showExportMenu}
            disabled={exporting}
            title="Export Dashboard"
          >
            <Download size={20} />
          </button>
          {#if showExportMenu}
            <div class="export-menu">
              <button class="export-option" on:click={() => exportDashboard('pdf')}>
                <File size={16} />
                <span>Export as PDF</span>
              </button>
              <button class="export-option" on:click={() => exportDashboard('png')}>
                <FileImage size={16} />
                <span>Export as PNG</span>
              </button>
              <button class="export-option" on:click={() => exportDashboard('jpg')}>
                <FileImage size={16} />
                <span>Export as JPG</span>
              </button>
            </div>
          {/if}
        </div>
      </div>
    </header>

    {#if error}
      <div class="error">{error}</div>
    {/if}

    {#if exporting}
      <div class="export-overlay">
        <div class="export-spinner">
          <div class="spinner"></div>
          <p>Generating export...</p>
        </div>
      </div>
    {/if}

    <!-- Widget Panel -->
    {#if showWidgetPanel && editMode}
      <div class="widget-panel">
        <h3>Add Widget</h3>
        <p class="widget-limit">
          {dashboard.widgets.length} / {planLimits[userPlan].widgets} widgets used
        </p>
        <div class="widget-types">
          {#each widgetTypes as widgetType}
            <button 
              class="widget-type-button"
              on:click={() => addWidget(widgetType.id)}
              disabled={dashboard.widgets.length >= planLimits[userPlan].widgets}
            >
              <svelte:component this={widgetIcons[widgetType.id] || BarChart2} size={24} />
              <span>{widgetType.name}</span>
            </button>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Dashboard Grid -->
    <div 
      class="dashboard-grid"
      class:edit-mode={editMode}
      class:resizing={resizing}
      style="--grid-cols: {GRID_COLS}; --row-height: {ROW_HEIGHT}px; --margin: {MARGIN}px;"
    >
      {#if editMode}
        <div
          use:dndzone={{
            items: dashboard.widgets,
            flipDurationMs: 200,
            dropTargetStyle: {}
          }}
          on:consider={handleDndConsider}
          on:finalize={handleDndFinalize}
          class="dnd-container"
        >
          {#each dashboard.widgets as widget (widget.id)}
            {@const widgetComponent = renderWidget(widget)}
            {@const data = getWidgetData(widget)}
            <div 
              class="widget-container"
              animate:flip={{ duration: 200 }}
              style="
                grid-column: {widget.position.x + 1} / span {widget.position.width};
                grid-row: {widget.position.y + 1} / span {widget.position.height};
              "
            >
              <div class="widget">
                <div class="widget-header">
                  <h4>{widget.title}</h4>
                  <div class="widget-actions">
                    <button class="widget-action" on:click={() => selectedWidget = widget}>
                      <Settings size={16} />
                    </button>
                    <button class="widget-action drag-handle">
                      <Move size={16} />
                    </button>
                    <button class="widget-action" on:click={() => removeWidget(widget.id)}>
                      <X size={16} />
                    </button>
                  </div>
                </div>
                <div class="widget-content">
                  {#if widgetComponent && data}
                    <svelte:component 
                      this={widgetComponent} 
                      {...data}
                    />
                  {:else if widgetComponent}
                    <div class="widget-placeholder">
                      <svelte:component this={widgetIcons[widget.type] || BarChart2} size={48} />
                      <p>Configure widget settings</p>
                    </div>
                  {/if}
                </div>
                {#if editMode}
                  <div class="resize-handles">
                    <div 
                      class="resize-handle resize-handle-se"
                      on:mousedown={(e) => startResize(e, widget, 'se')}
                      title="Resize"
                    >
                      <svg width="12" height="12" viewBox="0 0 12 12">
                        <path d="M1 11 L11 1 M6 11 L11 6" stroke="currentColor" stroke-width="1.5" fill="none"/>
                      </svg>
                    </div>
                    <div 
                      class="resize-handle resize-handle-e"
                      on:mousedown={(e) => startResize(e, widget, 'e')}
                      title="Resize horizontally"
                    ></div>
                    <div 
                      class="resize-handle resize-handle-s"
                      on:mousedown={(e) => startResize(e, widget, 's')}
                      title="Resize vertically"
                    ></div>
                  </div>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <!-- View Mode - No drag and drop -->
        {#each dashboard.widgets as widget}
          {@const widgetComponent = renderWidget(widget)}
          {@const data = getWidgetData(widget)}
          <div 
            class="widget-container"
            style="
              grid-column: {widget.position.x + 1} / span {widget.position.width};
              grid-row: {widget.position.y + 1} / span {widget.position.height};
            "
          >
            <div class="widget">
              <div class="widget-header">
                <h4>{widget.title}</h4>
              </div>
              <div class="widget-content">
                {#if widgetComponent && data}
                  <svelte:component 
                    this={widgetComponent} 
                    {...data}
                  />
                {:else if widgetComponent}
                  <LoadingSkeleton type="chart" height="100%" />
                {/if}
              </div>
            </div>
          </div>
        {/each}
      {/if}

      <!-- Grid lines in edit mode -->
      {#if editMode}
        <div class="grid-overlay">
          {#each Array(20) as _, row}
            {#each Array(GRID_COLS) as _, col}
              <div 
                class="grid-cell"
                style="
                  grid-column: {col + 1};
                  grid-row: {row + 1};
                "
              />
            {/each}
          {/each}
        </div>
      {/if}
    </div>
  </div>

  <!-- Widget Settings Modal -->
  {#if selectedWidget}
    <div class="modal-overlay" on:click={() => selectedWidget = null}>
      <div class="modal" on:click|stopPropagation>
        <h3>Widget Settings</h3>
        <form on:submit|preventDefault={() => {
          if (selectedWidget) {
            updateWidget(selectedWidget.id, selectedWidget);
            selectedWidget = null;
          }
        }}>
          <div class="form-group">
            <label for="widget-title">Title</label>
            <input
              id="widget-title"
              type="text"
              bind:value={selectedWidget.title}
            />
          </div>

          <div class="form-group">
            <label for="data-source">Data Source</label>
            <select id="data-source" bind:value={selectedWidget.data_source}>
              {#each dataSources as source}
                <option value={source.id}>{source.name}</option>
              {/each}
            </select>
          </div>

          <div class="form-group">
            <label for="refresh-interval">Refresh Interval (seconds)</label>
            <input
              id="refresh-interval"
              type="number"
              min="0"
              step="30"
              bind:value={selectedWidget.refresh_interval}
            />
            <small>Set to 0 to disable auto-refresh</small>
          </div>

          <div class="modal-actions">
            <button type="button" class="secondary-button" on:click={() => selectedWidget = null}>
              Cancel
            </button>
            <button type="submit" class="primary-button">
              Save Settings
            </button>
          </div>
        </form>
      </div>
    </div>
  {/if}
{/if}

<style>
  .dashboard-builder {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: #f9fafb;
  }

  .loading-container,
  .error-container {
    padding: 2rem;
    text-align: center;
  }

  .skeleton-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    margin-top: 2rem;
  }

  .builder-header {
    background: white;
    border-bottom: 1px solid #e5e7eb;
    padding: 1rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .header-left h1 {
    font-size: 1.5rem;
    margin: 0;
  }

  .header-left p {
    color: #6b7280;
    margin: 0.25rem 0 0 0;
    font-size: 0.875rem;
  }

  .header-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .icon-button {
    padding: 0.5rem;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .icon-button:hover {
    background: #f3f4f6;
    border-color: #d1d5db;
  }

  .icon-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .widget-panel {
    background: white;
    border-bottom: 1px solid #e5e7eb;
    padding: 1.5rem 2rem;
  }

  .widget-panel h3 {
    margin: 0 0 0.5rem 0;
  }

  .widget-limit {
    color: #6b7280;
    font-size: 0.875rem;
    margin-bottom: 1rem;
  }

  .widget-types {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .widget-type-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem;
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
    min-width: 100px;
  }

  .widget-type-button:hover:not(:disabled) {
    border-color: #10b981;
    background: #f0fdf4;
  }

  .widget-type-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .widget-type-button span {
    font-size: 0.875rem;
    color: #374151;
  }

  .dashboard-grid {
    flex: 1;
    padding: 2rem;
    overflow: auto;
    position: relative;
    display: grid;
    grid-template-columns: repeat(var(--grid-cols), 1fr);
    grid-auto-rows: var(--row-height);
    gap: var(--margin);
  }

  .dnd-container {
    display: contents;
  }

  .grid-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: grid;
    grid-template-columns: repeat(var(--grid-cols), 1fr);
    grid-auto-rows: var(--row-height);
    gap: var(--margin);
    pointer-events: none;
    z-index: 0;
  }

  .grid-cell {
    border: 1px dashed #e5e7eb;
    border-radius: 4px;
  }

  .widget-container {
    position: relative;
    z-index: 1;
  }

  .widget {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transition: all 0.2s;
    position: relative;
  }

  .edit-mode .widget:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .dashboard-grid.resizing .widget {
    transition: none;
  }

  .dashboard-grid.resizing .grid-overlay {
    z-index: 2;
  }
  
  .dashboard-grid.resizing .grid-cell {
    border-color: #9ca3af;
  }

  .widget-header {
    padding: 1rem;
    border-bottom: 1px solid #e5e7eb;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .widget-header h4 {
    margin: 0;
    font-size: 1rem;
  }

  .widget-actions {
    display: flex;
    gap: 0.25rem;
  }

  .widget-action {
    padding: 0.25rem;
    background: transparent;
    border: none;
    cursor: pointer;
    color: #6b7280;
    transition: all 0.2s;
  }

  .widget-action:hover {
    color: #374151;
    background: #f3f4f6;
    border-radius: 4px;
  }

  .drag-handle {
    cursor: move;
  }

  .widget-content {
    flex: 1;
    padding: 1rem;
    overflow: auto;
  }

  .widget-placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #9ca3af;
    text-align: center;
  }

  .widget-placeholder p {
    margin-top: 1rem;
    font-size: 0.875rem;
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
    max-width: 500px;
    width: 90%;
  }

  .modal h3 {
    margin: 0 0 1.5rem 0;
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

  .form-group input,
  .form-group select {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    font-size: 1rem;
  }

  .form-group small {
    display: block;
    margin-top: 0.25rem;
    color: #6b7280;
    font-size: 0.875rem;
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

  .primary-button:hover {
    background: #059669;
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
    margin: 1rem 2rem;
  }

  .resize-handles {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
  }

  .resize-handle {
    position: absolute;
    background: #10b981;
    opacity: 0;
    transition: opacity 0.2s;
    pointer-events: all;
  }

  .widget:hover .resize-handle {
    opacity: 0.7;
  }

  .resize-handle:hover {
    opacity: 1 !important;
  }

  .resize-handle-se {
    bottom: 0;
    right: 0;
    width: 20px;
    height: 20px;
    cursor: nwse-resize;
    border-radius: 0 0 8px 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
  }

  .resize-handle-e {
    top: 50%;
    right: 0;
    width: 8px;
    height: 40px;
    transform: translateY(-50%);
    cursor: ew-resize;
    border-radius: 0 4px 4px 0;
  }

  .resize-handle-s {
    left: 50%;
    bottom: 0;
    width: 40px;
    height: 8px;
    transform: translateX(-50%);
    cursor: ns-resize;
    border-radius: 0 0 4px 4px;
  }

  .export-dropdown {
    position: relative;
  }

  .export-menu {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 0.5rem;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    min-width: 180px;
    z-index: 100;
  }

  .export-option {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 0.75rem 1rem;
    background: none;
    border: none;
    cursor: pointer;
    color: #374151;
    font-size: 0.875rem;
    transition: all 0.2s;
    text-align: left;
  }

  .export-option:hover {
    background: #f3f4f6;
    color: #10b981;
  }

  .export-option:first-child {
    border-radius: 8px 8px 0 0;
  }

  .export-option:last-child {
    border-radius: 0 0 8px 8px;
  }

  .export-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
  }

  .export-spinner {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  }

  .spinner {
    width: 50px;
    height: 50px;
    border: 3px solid #e5e7eb;
    border-top-color: #10b981;
    border-radius: 50%;
    margin: 0 auto 1rem;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .export-spinner p {
    margin: 0;
    color: #374151;
    font-weight: 500;
  }

  @media (max-width: 768px) {
    .dashboard-grid {
      padding: 1rem;
    }

    .widget-panel {
      padding: 1rem;
    }

    .widget-types {
      gap: 0.5rem;
    }

    .widget-type-button {
      min-width: 80px;
      padding: 0.75rem;
      font-size: 0.75rem;
    }
    
    .resize-handle {
      display: none;
    }
  }
</style>