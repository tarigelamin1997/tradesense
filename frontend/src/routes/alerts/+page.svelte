<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/api/client';
    import Icon from '$lib/components/Icon.svelte';
    import CreateAlertModal from '$lib/components/alerts/CreateAlertModal.svelte';
    
    let alerts = [];
    let templates = [];
    let stats = null;
    let history = [];
    let loading = true;
    let error = null;
    let activeTab = 'alerts';
    let showCreateModal = false;
    let selectedTemplate = null;
    let selectedAlert = null;
    let showDetails = false;
    
    const statusColors = {
        active: 'green',
        triggered: 'blue',
        snoozed: 'yellow',
        disabled: 'gray',
        expired: 'red'
    };
    
    const priorityColors = {
        low: 'gray',
        medium: 'yellow',
        high: 'orange',
        critical: 'red'
    };
    
    async function loadData() {
        try {
            loading = true;
            error = null;
            
            // Load based on active tab
            if (activeTab === 'alerts') {
                const [alertsData, statsData] = await Promise.all([
                    api.get('/alerts/list'),
                    api.get('/alerts/stats/overview')
                ]);
                alerts = alertsData.alerts;
                stats = statsData.stats;
            } else if (activeTab === 'templates') {
                templates = (await api.get('/alerts/templates/list')).templates;
            } else if (activeTab === 'history') {
                history = (await api.get('/alerts/history/list')).history;
            }
            
        } catch (err) {
            error = err.message || 'Failed to load alerts data';
        } finally {
            loading = false;
        }
    }
    
    async function toggleAlert(alertId, currentStatus) {
        try {
            const enabled = currentStatus !== 'active';
            await api.post(`/alerts/${alertId}/toggle`, { enabled });
            await loadData();
        } catch (err) {
            alert(err.message || 'Failed to toggle alert');
        }
    }
    
    async function deleteAlert(alertId) {
        if (!confirm('Delete this alert?')) return;
        
        try {
            await api.delete(`/alerts/${alertId}`);
            await loadData();
        } catch (err) {
            alert(err.message || 'Failed to delete alert');
        }
    }
    
    async function testAlert(alertId) {
        try {
            const result = await api.post(`/alerts/test/${alertId}`);
            alert(`Test alert sent to: ${result.channels.join(', ')}`);
        } catch (err) {
            alert(err.message || 'Failed to test alert');
        }
    }
    
    function createFromTemplate(template) {
        selectedTemplate = template;
        showCreateModal = true;
    }
    
    function viewAlertDetails(alert) {
        selectedAlert = alert;
        showDetails = true;
    }
    
    function formatConditions(conditions) {
        return conditions.map(c => {
            const field = c.field.replace(/_/g, ' ');
            const op = {
                gt: '>',
                gte: '≥',
                lt: '<',
                lte: '≤',
                eq: '='
            }[c.operator] || c.operator;
            
            return `${field} ${op} ${c.value}`;
        }).join(' AND ');
    }
    
    function getAlertIcon(type) {
        const iconMap = {
            price_above: 'trending-up',
            price_below: 'trending-down',
            daily_pnl: 'dollar-sign',
            win_rate: 'award',
            loss_streak: 'alert-triangle',
            drawdown: 'activity',
            pattern_detected: 'compass',
            account_balance: 'credit-card'
        };
        
        return iconMap[type] || 'bell';
    }
    
    onMount(() => {
        loadData();
        
        // Set up WebSocket for real-time notifications
        const ws = new WebSocket(`${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`);
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'notification' && data.data.type === 'alert') {
                // Show notification
                showNotification(data.data);
                
                // Reload alerts to update trigger count
                if (activeTab === 'alerts') {
                    loadData();
                }
            }
        };
        
        return () => {
            ws.close();
        };
    });
    
    function showNotification(notification) {
        // You can implement a toast notification here
        console.log('Alert triggered:', notification);
    }
</script>

<svelte:head>
    <title>Trading Alerts - TradeSense</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
        <div class="flex justify-between items-center">
            <div>
                <h1 class="text-3xl font-bold text-gray-900">Trading Alerts</h1>
                <p class="mt-2 text-gray-600">
                    Stay informed with automated trading notifications
                </p>
            </div>
            <button
                on:click={() => { selectedTemplate = null; showCreateModal = true; }}
                class="btn btn-primary"
                disabled={stats && stats.alerts_remaining === 0}
            >
                <Icon name="plus" class="w-5 h-5 mr-2" />
                Create Alert
            </button>
        </div>
        
        {#if stats}
            <div class="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                    <div class="text-sm text-gray-600">Active Alerts</div>
                    <div class="mt-1 text-2xl font-semibold text-gray-900">
                        {stats.active_alerts}
                        <span class="text-sm text-gray-500">/ {stats.alert_limit}</span>
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                    <div class="text-sm text-gray-600">Total Triggers</div>
                    <div class="mt-1 text-2xl font-semibold text-gray-900">
                        {stats.total_triggers}
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                    <div class="text-sm text-gray-600">Last 24h</div>
                    <div class="mt-1 text-2xl font-semibold text-gray-900">
                        {stats.triggers_24h}
                    </div>
                </div>
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                    <div class="text-sm text-gray-600">Last 7d</div>
                    <div class="mt-1 text-2xl font-semibold text-gray-900">
                        {stats.triggers_7d}
                    </div>
                </div>
            </div>
        {/if}
    </div>
    
    <!-- Tabs -->
    <div class="mb-6">
        <div class="border-b border-gray-200">
            <nav class="-mb-px flex space-x-8">
                <button
                    on:click={() => { activeTab = 'alerts'; loadData(); }}
                    class="py-2 px-1 border-b-2 font-medium text-sm"
                    class:border-indigo-500={activeTab === 'alerts'}
                    class:text-indigo-600={activeTab === 'alerts'}
                    class:border-transparent={activeTab !== 'alerts'}
                    class:text-gray-500={activeTab !== 'alerts'}
                >
                    My Alerts
                </button>
                <button
                    on:click={() => { activeTab = 'templates'; loadData(); }}
                    class="py-2 px-1 border-b-2 font-medium text-sm"
                    class:border-indigo-500={activeTab === 'templates'}
                    class:text-indigo-600={activeTab === 'templates'}
                    class:border-transparent={activeTab !== 'templates'}
                    class:text-gray-500={activeTab !== 'templates'}
                >
                    Templates
                </button>
                <button
                    on:click={() => { activeTab = 'history'; loadData(); }}
                    class="py-2 px-1 border-b-2 font-medium text-sm"
                    class:border-indigo-500={activeTab === 'history'}
                    class:text-indigo-600={activeTab === 'history'}
                    class:border-transparent={activeTab !== 'history'}
                    class:text-gray-500={activeTab !== 'history'}
                >
                    History
                </button>
            </nav>
        </div>
    </div>
    
    {#if loading}
        <div class="flex justify-center py-12">
            <div class="spinner"></div>
        </div>
    {:else if error}
        <div class="alert alert-error">{error}</div>
    {:else}
        <!-- My Alerts Tab -->
        {#if activeTab === 'alerts'}
            {#if alerts.length === 0}
                <div class="text-center py-12">
                    <Icon name="bell-off" class="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <h3 class="text-lg font-medium text-gray-900 mb-2">No alerts yet</h3>
                    <p class="text-gray-600 mb-4">Create your first alert to get started</p>
                    <button
                        on:click={() => { activeTab = 'templates'; loadData(); }}
                        class="btn btn-primary"
                    >
                        Browse Templates
                    </button>
                </div>
            {:else}
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {#each alerts as alert}
                        <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                            <div class="p-4">
                                <div class="flex items-start justify-between mb-3">
                                    <div class="flex items-center">
                                        <Icon 
                                            name={getAlertIcon(alert.type)} 
                                            class="w-5 h-5 text-gray-600 mr-2" 
                                        />
                                        <h3 class="font-semibold text-gray-900">
                                            {alert.name}
                                        </h3>
                                    </div>
                                    <span class="px-2 py-1 text-xs rounded-full bg-{priorityColors[alert.priority]}-100 text-{priorityColors[alert.priority]}-800">
                                        {alert.priority}
                                    </span>
                                </div>
                                
                                {#if alert.description}
                                    <p class="text-sm text-gray-600 mb-3">
                                        {alert.description}
                                    </p>
                                {/if}
                                
                                <div class="space-y-2 text-sm">
                                    <div class="flex items-center justify-between">
                                        <span class="text-gray-500">Status:</span>
                                        <span class="px-2 py-1 text-xs rounded-full bg-{statusColors[alert.status]}-100 text-{statusColors[alert.status]}-800">
                                            {alert.status}
                                        </span>
                                    </div>
                                    
                                    <div class="flex items-center justify-between">
                                        <span class="text-gray-500">Triggers:</span>
                                        <span class="font-medium">{alert.trigger_count}</span>
                                    </div>
                                    
                                    {#if alert.last_triggered_at}
                                        <div class="flex items-center justify-between">
                                            <span class="text-gray-500">Last:</span>
                                            <span class="text-xs">
                                                {new Date(alert.last_triggered_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                    {/if}
                                    
                                    <div class="pt-2">
                                        <div class="text-xs text-gray-500 mb-1">Conditions:</div>
                                        <div class="text-xs font-mono bg-gray-50 p-2 rounded">
                                            {formatConditions(alert.conditions)}
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mt-4 flex items-center justify-between">
                                    <div class="flex space-x-1">
                                        {#each alert.channels as channel}
                                            <Icon 
                                                name={
                                                    channel === 'email' ? 'mail' :
                                                    channel === 'sms' ? 'message-square' :
                                                    channel === 'in_app' ? 'bell' :
                                                    'link'
                                                }
                                                class="w-4 h-4 text-gray-400"
                                                title={channel}
                                            />
                                        {/each}
                                    </div>
                                    
                                    <div class="flex space-x-2">
                                        <button
                                            on:click={() => toggleAlert(alert.id, alert.status)}
                                            class="text-indigo-600 hover:text-indigo-700"
                                            title={alert.status === 'active' ? 'Disable' : 'Enable'}
                                        >
                                            <Icon 
                                                name={alert.status === 'active' ? 'pause' : 'play'} 
                                                class="w-5 h-5" 
                                            />
                                        </button>
                                        <button
                                            on:click={() => testAlert(alert.id)}
                                            class="text-green-600 hover:text-green-700"
                                            title="Test alert"
                                        >
                                            <Icon name="zap" class="w-5 h-5" />
                                        </button>
                                        <button
                                            on:click={() => viewAlertDetails(alert)}
                                            class="text-gray-600 hover:text-gray-700"
                                            title="View details"
                                        >
                                            <Icon name="eye" class="w-5 h-5" />
                                        </button>
                                        <button
                                            on:click={() => deleteAlert(alert.id)}
                                            class="text-red-600 hover:text-red-700"
                                            title="Delete"
                                        >
                                            <Icon name="trash-2" class="w-5 h-5" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    {/each}
                </div>
            {/if}
        {/if}
        
        <!-- Templates Tab -->
        {#if activeTab === 'templates'}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {#each templates as template}
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                        <div class="flex items-start justify-between mb-3">
                            <h3 class="font-semibold text-gray-900">
                                {template.name}
                            </h3>
                            <span class="px-2 py-1 text-xs rounded-full bg-indigo-100 text-indigo-800">
                                {template.category}
                            </span>
                        </div>
                        
                        <p class="text-sm text-gray-600 mb-3">
                            {template.description}
                        </p>
                        
                        <div class="text-xs text-gray-500 mb-3">
                            Default conditions:
                            <div class="mt-1 font-mono bg-gray-50 p-2 rounded">
                                {formatConditions(template.default_conditions)}
                            </div>
                        </div>
                        
                        <button
                            on:click={() => createFromTemplate(template)}
                            class="btn btn-sm btn-primary w-full"
                        >
                            Use Template
                        </button>
                    </div>
                {/each}
            </div>
        {/if}
        
        <!-- History Tab -->
        {#if activeTab === 'history'}
            <div class="bg-white rounded-lg shadow-sm border border-gray-200">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Alert
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Type
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Triggered
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Channels
                            </th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Status
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        {#each history as item}
                            <tr>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                    {item.alert_name}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {item.alert_type.replace(/_/g, ' ')}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {new Date(item.triggered_at).toLocaleString()}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {item.channels_notified.join(', ')}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm">
                                    <div class="flex space-x-2">
                                        {#each Object.entries(item.notification_status) as [channel, status]}
                                            <span class="inline-flex items-center text-xs">
                                                <Icon 
                                                    name={status === 'success' ? 'check-circle' : 'x-circle'}
                                                    class="w-4 h-4 mr-1 text-{status === 'success' ? 'green' : 'red'}-500"
                                                />
                                                {channel}
                                            </span>
                                        {/each}
                                    </div>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        {/if}
    {/if}
</div>

<!-- Create Alert Modal -->
{#if showCreateModal}
    <CreateAlertModal
        template={selectedTemplate}
        onClose={() => { showCreateModal = false; selectedTemplate = null; }}
        onSuccess={() => { showCreateModal = false; loadData(); }}
    />
{/if}

<!-- Alert Details Modal -->
{#if showDetails && selectedAlert}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div class="p-6 border-b border-gray-200">
                <div class="flex items-center justify-between">
                    <h2 class="text-xl font-bold text-gray-900">Alert Details</h2>
                    <button
                        on:click={() => { showDetails = false; selectedAlert = null; }}
                        class="text-gray-500 hover:text-gray-700"
                    >
                        <Icon name="x" class="w-6 h-6" />
                    </button>
                </div>
            </div>
            
            <div class="p-6">
                <pre class="text-sm bg-gray-50 p-4 rounded overflow-x-auto">
{JSON.stringify(selectedAlert, null, 2)}
                </pre>
            </div>
        </div>
    </div>
{/if}

<style>
    .spinner {
        width: 2rem; height: 2rem; border-width: 4px; border-color: #c7d2fe; border-top-color: #4f46e5; border-radius: 9999px; animation: spin 1s linear infinite;
    }
    
    .btn {
        padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 500; transition: background-color 0.2s, color 0.2s; display: inline-flex; align-items: center; justify-content: center;
    }
    
    .btn-primary {
        background-color: #4f46e5;
        color: white;
    }
    
    .btn-primary:hover {
        background-color: #4338ca;
    }
    
    .btn-sm {
        padding: 0.25rem 0.75rem;
        font-size: 0.875rem;
    }
    
    .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    
    .alert {
        padding: 1rem; border-radius: 0.375rem;
    }
    
    .alert-error {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
</style>