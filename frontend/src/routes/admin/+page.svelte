<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import Icon from '$lib/components/Icon.svelte';
    import Chart from '$lib/components/Chart.svelte';
    import analytics from '$lib/analytics';
    
    let stats = null;
    let loading = true;
    let error = null;
    
    // Chart data
    let userGrowthData = null;
    let revenueData = null;
    
    async function loadDashboard() {
        try {
            loading = true;
            error = null;
            
            const response = await api.get('/admin/dashboard/stats');
            stats = response;
            
            // Prepare chart data
            prepareChartData();
            
            // Track admin dashboard view
            analytics.trackFeature('admin_dashboard');
            
        } catch (err) {
            error = err.message || 'Failed to load dashboard';
        } finally {
            loading = false;
        }
    }
    
    function prepareChartData() {
        // User growth chart (mock data for now)
        userGrowthData = {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'New Users',
                data: [12, 19, 15, 25, 22, 30, 28],
                borderColor: 'rgb(99, 102, 241)',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.4
            }]
        };
        
        // Revenue chart (mock data for now)
        revenueData = {
            labels: ['Free', 'Pro', 'Premium'],
            datasets: [{
                data: [
                    stats?.subscriptions?.breakdown?.free?.count || 0,
                    stats?.subscriptions?.breakdown?.pro?.count || 0,
                    stats?.subscriptions?.breakdown?.premium?.count || 0
                ],
                backgroundColor: [
                    'rgb(156, 163, 175)',
                    'rgb(99, 102, 241)',
                    'rgb(139, 92, 246)'
                ]
            }]
        };
    }
    
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }
    
    function formatNumber(num) {
        return new Intl.NumberFormat('en-US').format(num);
    }
    
    function getPercentageChange(current, previous) {
        if (!previous) return 0;
        return ((current - previous) / previous * 100).toFixed(1);
    }
    
    onMount(() => {
        loadDashboard();
        
        // Refresh every 30 seconds
        const interval = setInterval(loadDashboard, 30000);
        
        return () => clearInterval(interval);
    });
</script>

<div class="space-y-6">
    <!-- Page Header -->
    <div class="flex justify-between items-center">
        <div>
            <h2 class="text-2xl font-bold text-gray-900">Admin Dashboard</h2>
            <p class="text-gray-600 mt-1">Monitor system health and user activity</p>
        </div>
        <button
            on:click={loadDashboard}
            disabled={loading}
            class="btn btn-secondary"
        >
            <Icon name="refresh" class="w-4 h-4 mr-2" />
            Refresh
        </button>
    </div>
    
    {#if loading && !stats}
        <div class="flex justify-center py-12">
            <div class="spinner"></div>
        </div>
    {:else if error}
        <div class="alert alert-error">
            {error}
        </div>
    {:else if stats}
        <!-- Key Metrics Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <!-- Total Users -->
            <div class="admin-card">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">Total Users</p>
                        <p class="text-2xl font-bold text-gray-900 mt-1">
                            {formatNumber(stats.users.total)}
                        </p>
                        <p class="text-sm text-green-600 mt-1">
                            +{stats.users.new_7d} this week
                        </p>
                    </div>
                    <div class="p-3 bg-indigo-100 rounded-lg">
                        <Icon name="users" class="w-6 h-6 text-indigo-600" />
                    </div>
                </div>
            </div>
            
            <!-- Monthly Revenue -->
            <div class="admin-card">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">Monthly Revenue</p>
                        <p class="text-2xl font-bold text-gray-900 mt-1">
                            {formatCurrency(stats.subscriptions.total_mrr)}
                        </p>
                        <p class="text-sm text-gray-500 mt-1">
                            {stats.users.paid} paid users
                        </p>
                    </div>
                    <div class="p-3 bg-green-100 rounded-lg">
                        <Icon name="currency-dollar" class="w-6 h-6 text-green-600" />
                    </div>
                </div>
            </div>
            
            <!-- Active Users -->
            <div class="admin-card">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">Active Today</p>
                        <p class="text-2xl font-bold text-gray-900 mt-1">
                            {formatNumber(stats.users.active_24h)}
                        </p>
                        <p class="text-sm text-gray-500 mt-1">
                            {Math.round(stats.users.active_24h / stats.users.total * 100)}% of total
                        </p>
                    </div>
                    <div class="p-3 bg-purple-100 rounded-lg">
                        <Icon name="activity" class="w-6 h-6 text-purple-600" />
                    </div>
                </div>
            </div>
            
            <!-- System Health -->
            <div class="admin-card">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-sm font-medium text-gray-600">System Health</p>
                        <p class="text-2xl font-bold text-gray-900 mt-1">
                            {stats.system.avg_response_time_ms}ms
                        </p>
                        <p class="text-sm {stats.system.errors_1h > 0 ? 'text-red-600' : 'text-green-600'} mt-1">
                            {stats.system.errors_1h} errors/hr
                        </p>
                    </div>
                    <div class="p-3 {stats.system.errors_1h > 10 ? 'bg-red-100' : 'bg-green-100'} rounded-lg">
                        <Icon name="heart" class="w-6 h-6 {stats.system.errors_1h > 10 ? 'text-red-600' : 'text-green-600'}" />
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Charts Row -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- User Growth Chart -->
            <div class="admin-card">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">User Growth</h3>
                {#if userGrowthData}
                    <Chart type="line" data={userGrowthData} height={250} />
                {/if}
            </div>
            
            <!-- Subscription Breakdown -->
            <div class="admin-card">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Subscription Breakdown</h3>
                {#if revenueData}
                    <Chart type="doughnut" data={revenueData} height={250} />
                {/if}
            </div>
        </div>
        
        <!-- Activity Tables -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Recent Signups -->
            <div class="admin-card">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Recent Signups</h3>
                <div class="overflow-x-auto">
                    <table class="admin-table">
                        <thead>
                            <tr>
                                <th>User</th>
                                <th>Plan</th>
                                <th>Joined</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-200">
                            {#each stats.recent_signups as user}
                                <tr>
                                    <td>
                                        <div>
                                            <div class="text-sm font-medium text-gray-900">
                                                {user.full_name}
                                            </div>
                                            <div class="text-sm text-gray-500">
                                                {user.email}
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <span class="px-2 py-1 text-xs font-medium rounded-full
                                                   {user.subscription_tier === 'premium' ? 'bg-purple-100 text-purple-800' :
                                                    user.subscription_tier === 'pro' ? 'bg-indigo-100 text-indigo-800' :
                                                    'bg-gray-100 text-gray-800'}">
                                            {user.subscription_tier}
                                        </span>
                                    </td>
                                    <td class="text-sm text-gray-500">
                                        {new Date(user.created_at).toLocaleDateString()}
                                    </td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <!-- Recent Issues -->
            <div class="admin-card">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Recent Issues</h3>
                {#if stats.recent_issues.length > 0}
                    <div class="space-y-3">
                        {#each stats.recent_issues as issue}
                            <div class="border-l-4 border-red-400 pl-4 py-2">
                                <div class="text-sm font-medium text-gray-900">
                                    {issue.type === 'error' ? 'Error' : issue.type}
                                </div>
                                <div class="text-sm text-gray-600 mt-1">
                                    {issue.message}
                                </div>
                                <div class="text-xs text-gray-500 mt-1">
                                    {new Date(issue.timestamp).toLocaleString()}
                                    {#if issue.user_id}
                                        • User: {issue.user_id}
                                    {/if}
                                </div>
                            </div>
                        {/each}
                    </div>
                {:else}
                    <p class="text-sm text-gray-500">No recent issues</p>
                {/if}
            </div>
        </div>
        
        <!-- System Stats -->
        <div class="admin-card">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">System Statistics</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                    <p class="text-sm text-gray-600">API Requests (1h)</p>
                    <p class="text-xl font-semibold text-gray-900">
                        {formatNumber(stats.system.api_requests_1h)}
                    </p>
                </div>
                <div>
                    <p class="text-sm text-gray-600">Database Size</p>
                    <p class="text-xl font-semibold text-gray-900">
                        {stats.system.database_size_mb.toFixed(1)} MB
                    </p>
                </div>
                <div>
                    <p class="text-sm text-gray-600">Total Trades</p>
                    <p class="text-xl font-semibold text-gray-900">
                        {formatNumber(stats.trades.total)}
                    </p>
                </div>
                <div>
                    <p class="text-sm text-gray-600">Trades Today</p>
                    <p class="text-xl font-semibold text-gray-900">
                        {formatNumber(stats.trades.trades_24h)}
                    </p>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .spinner {
        width: 2rem; height: 2rem; border-width: 4px; border-color: #c7d2fe; border-top-color: #4f46e5; border-radius: 9999px; animation: spin 1s linear infinite;
    }
</style>