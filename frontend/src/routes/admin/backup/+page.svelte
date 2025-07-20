<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/api/ssr-safe';
    import Icon from '$lib/components/Icon.svelte';
    import BackupScheduleModal from '$lib/components/admin/BackupScheduleModal.svelte';
    import RestoreModal from '$lib/components/admin/RestoreModal.svelte';
    
    let backups = [];
    let schedules = [];
    let stats = [];
    let dashboard = { recent_backups: [], upcoming_backups: [] };
    let loading = true;
    let error = null;
    let activeTab = 'backups';
    let showScheduleModal = false;
    let showRestoreModal = false;
    let selectedBackup = null;
    
    const statusColors = {
        pending: 'yellow',
        running: 'blue',
        completed: 'green',
        failed: 'red',
        cancelled: 'gray'
    };
    
    const backupTypes = {
        database: { icon: 'database', color: 'blue' },
        files: { icon: 'folder', color: 'green' },
        full: { icon: 'package', color: 'purple' }
    };
    
    async function loadData() {
        try {
            loading = true;
            error = null;
            
            // Load based on active tab
            if (activeTab === 'backups') {
                backups = await api.get('/backup/list');
            } else if (activeTab === 'schedules') {
                schedules = await api.get('/backup/schedules/list');
            } else if (activeTab === 'stats') {
                stats = await api.get('/backup/stats/overview');
                dashboard = await api.get('/backup/status/dashboard');
            }
            
        } catch (err) {
            error = err.message || 'Failed to load backup data';
        } finally {
            loading = false;
        }
    }
    
    async function createBackup(type) {
        if (!confirm(`Create a ${type} backup now?`)) return;
        
        try {
            const result = await api.post('/backup/create', {
                backup_type: type,
                destination: 'local',
                compress: true
            });
            
            alert(result.message);
            await loadData();
            
        } catch (err) {
            alert(err.message || 'Failed to create backup');
        }
    }
    
    async function verifyBackup(backupId) {
        try {
            const result = await api.post(`/backup/${backupId}/verify`);
            
            if (result.status === 'passed') {
                alert('Backup verification passed!');
            } else {
                alert(`Backup verification failed: ${JSON.stringify(result.checks)}`);
            }
            
        } catch (err) {
            alert(err.message || 'Failed to verify backup');
        }
    }
    
    async function cleanupBackups() {
        if (!confirm('Clean up old backups according to retention policy?')) return;
        
        try {
            const result = await api.delete('/backup/cleanup');
            alert(`Cleanup completed. Deleted ${result.deleted.local} local and ${result.deleted.remote} remote backups.`);
            await loadData();
            
        } catch (err) {
            alert(err.message || 'Failed to cleanup backups');
        }
    }
    
    async function createSchedule(schedule) {
        try {
            await api.post('/backup/schedules/create', schedule);
            showScheduleModal = false;
            await loadData();
        } catch (err) {
            throw new Error(err.message || 'Failed to create schedule');
        }
    }
    
    async function toggleSchedule(scheduleId, isActive) {
        try {
            await api.put(`/backup/schedules/${scheduleId}`, {
                is_active: !isActive
            });
            await loadData();
        } catch (err) {
            alert(err.message || 'Failed to update schedule');
        }
    }
    
    async function deleteSchedule(scheduleId) {
        if (!confirm('Delete this backup schedule?')) return;
        
        try {
            await api.delete(`/backup/schedules/${scheduleId}`);
            await loadData();
        } catch (err) {
            alert(err.message || 'Failed to delete schedule');
        }
    }
    
    function formatBytes(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function formatDuration(seconds) {
        if (!seconds) return '0s';
        if (seconds < 60) return `${Math.round(seconds)}s`;
        if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
        return `${(seconds / 3600).toFixed(1)}h`;
    }
    
    onMount(() => {
        loadData();
        
        // Refresh every 30 seconds
        const interval = setInterval(loadData, 30000);
        return () => clearInterval(interval);
    });
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
        <div class="flex justify-between items-center">
            <div>
                <h1 class="text-3xl font-bold text-gray-900">Backup Management</h1>
                <p class="mt-2 text-gray-600">Manage system backups and recovery</p>
            </div>
            <div class="flex space-x-2">
                <button
                    on:click={() => createBackup('database')}
                    class="btn btn-secondary"
                >
                    <Icon name="database" class="w-5 h-5 mr-2" />
                    Backup Database
                </button>
                <button
                    on:click={() => createBackup('full')}
                    class="btn btn-primary"
                >
                    <Icon name="package" class="w-5 h-5 mr-2" />
                    Full Backup
                </button>
            </div>
        </div>
    </div>
    
    <!-- Tabs -->
    <div class="mb-6">
        <div class="border-b border-gray-200">
            <nav class="-mb-px flex space-x-8">
                <button
                    on:click={() => { activeTab = 'backups'; loadData(); }}
                    class="py-2 px-1 border-b-2 font-medium text-sm"
                    class:border-indigo-500={activeTab === 'backups'}
                    class:text-indigo-600={activeTab === 'backups'}
                    class:border-transparent={activeTab !== 'backups'}
                    class:text-gray-500={activeTab !== 'backups'}
                >
                    Backups
                </button>
                <button
                    on:click={() => { activeTab = 'schedules'; loadData(); }}
                    class="py-2 px-1 border-b-2 font-medium text-sm"
                    class:border-indigo-500={activeTab === 'schedules'}
                    class:text-indigo-600={activeTab === 'schedules'}
                    class:border-transparent={activeTab !== 'schedules'}
                    class:text-gray-500={activeTab !== 'schedules'}
                >
                    Schedules
                </button>
                <button
                    on:click={() => { activeTab = 'stats'; loadData(); }}
                    class="py-2 px-1 border-b-2 font-medium text-sm"
                    class:border-indigo-500={activeTab === 'stats'}
                    class:text-indigo-600={activeTab === 'stats'}
                    class:border-transparent={activeTab !== 'stats'}
                    class:text-gray-500={activeTab !== 'stats'}
                >
                    Statistics
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
        <!-- Backups Tab -->
        {#if activeTab === 'backups'}
            <div class="bg-white rounded-lg shadow-sm border border-gray-200">
                <div class="p-6 border-b border-gray-200">
                    <div class="flex justify-between items-center">
                        <h2 class="text-lg font-semibold text-gray-900">Recent Backups</h2>
                        <button
                            on:click={cleanupBackups}
                            class="btn btn-sm btn-secondary"
                        >
                            <Icon name="trash-2" class="w-4 h-4 mr-1" />
                            Cleanup Old
                        </button>
                    </div>
                </div>
                
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Backup
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Type
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Status
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Size
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Created
                                </th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                            {#each backups as backup}
                                <tr>
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <div class="text-sm font-medium text-gray-900">
                                            {backup.backup_name}
                                        </div>
                                        {#if backup.remote_path}
                                            <div class="text-xs text-gray-500">
                                                <Icon name="cloud" class="w-3 h-3 inline" />
                                                Remote backup available
                                            </div>
                                        {/if}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <div class="flex items-center">
                                            <Icon 
                                                name={backupTypes[backup.backup_type].icon} 
                                                class="w-5 h-5 text-{backupTypes[backup.backup_type].color}-500 mr-2" 
                                            />
                                            <span class="text-sm text-gray-900 capitalize">
                                                {backup.backup_type}
                                            </span>
                                        </div>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-{statusColors[backup.status]}-100 text-{statusColors[backup.status]}-800">
                                            {backup.status}
                                        </span>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                        {formatBytes(backup.file_size)}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(backup.created_at).toLocaleString()}
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        <div class="flex space-x-2">
                                            {#if backup.status === 'completed'}
                                                <button
                                                    on:click={() => verifyBackup(backup.id)}
                                                    class="text-indigo-600 hover:text-indigo-900"
                                                    title="Verify backup"
                                                >
                                                    <Icon name="check-circle" class="w-5 h-5" />
                                                </button>
                                                <button
                                                    on:click={() => { selectedBackup = backup; showRestoreModal = true; }}
                                                    class="text-green-600 hover:text-green-900"
                                                    title="Restore from backup"
                                                >
                                                    <Icon name="rotate-ccw" class="w-5 h-5" />
                                                </button>
                                            {/if}
                                            {#if backup.error_message}
                                                <span class="text-red-600" title={backup.error_message}>
                                                    <Icon name="alert-circle" class="w-5 h-5" />
                                                </span>
                                            {/if}
                                        </div>
                                    </td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            </div>
        {/if}
        
        <!-- Schedules Tab -->
        {#if activeTab === 'schedules'}
            <div class="bg-white rounded-lg shadow-sm border border-gray-200">
                <div class="p-6 border-b border-gray-200">
                    <div class="flex justify-between items-center">
                        <h2 class="text-lg font-semibold text-gray-900">Backup Schedules</h2>
                        <button
                            on:click={() => showScheduleModal = true}
                            class="btn btn-sm btn-primary"
                        >
                            <Icon name="plus" class="w-4 h-4 mr-1" />
                            Add Schedule
                        </button>
                    </div>
                </div>
                
                <div class="p-6">
                    <div class="space-y-4">
                        {#each schedules as schedule}
                            <div class="border border-gray-200 rounded-lg p-4">
                                <div class="flex justify-between items-start">
                                    <div class="flex-1">
                                        <div class="flex items-center">
                                            <h3 class="text-lg font-medium text-gray-900">
                                                {schedule.name}
                                            </h3>
                                            <span class="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-{schedule.is_active ? 'green' : 'gray'}-100 text-{schedule.is_active ? 'green' : 'gray'}-800">
                                                {schedule.is_active ? 'Active' : 'Inactive'}
                                            </span>
                                        </div>
                                        <div class="mt-2 text-sm text-gray-600">
                                            <p>Type: {schedule.backup_type}</p>
                                            <p>Destination: {schedule.destination}</p>
                                            <p>Schedule: {JSON.stringify(schedule.schedule_config)}</p>
                                            {#if schedule.last_run_at}
                                                <p>Last run: {new Date(schedule.last_run_at).toLocaleString()}</p>
                                            {/if}
                                            {#if schedule.next_run_at}
                                                <p>Next run: {new Date(schedule.next_run_at).toLocaleString()}</p>
                                            {/if}
                                        </div>
                                    </div>
                                    <div class="flex space-x-2">
                                        <button
                                            on:click={() => toggleSchedule(schedule.id, schedule.is_active)}
                                            class="text-indigo-600 hover:text-indigo-900"
                                        >
                                            <Icon name={schedule.is_active ? 'pause' : 'play'} class="w-5 h-5" />
                                        </button>
                                        <button
                                            on:click={() => deleteSchedule(schedule.id)}
                                            class="text-red-600 hover:text-red-900"
                                        >
                                            <Icon name="trash-2" class="w-5 h-5" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            </div>
        {/if}
        
        <!-- Statistics Tab -->
        {#if activeTab === 'stats'}
            <!-- Stats Overview -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                {#each stats as stat}
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4 capitalize">
                            {stat.backup_type} Backups
                        </h3>
                        <div class="space-y-2 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-600">Total:</span>
                                <span class="font-medium">{stat.total_count}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-600">Success:</span>
                                <span class="font-medium text-green-600">{stat.success_count}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-600">Failed:</span>
                                <span class="font-medium text-red-600">{stat.failed_count}</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-600">Success Rate:</span>
                                <span class="font-medium">{stat.success_rate}%</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-600">Total Size:</span>
                                <span class="font-medium">{stat.total_size_gb} GB</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-600">Avg Duration:</span>
                                <span class="font-medium">{stat.avg_duration_minutes} min</span>
                            </div>
                        </div>
                    </div>
                {/each}
            </div>
            
            <!-- Dashboard -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Recent Status -->
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">Recent Backup Status</h3>
                    <div class="space-y-3">
                        {#each dashboard.recent_backups as backup}
                            <div class="flex items-center justify-between">
                                <div class="flex items-center">
                                    <Icon 
                                        name={backupTypes[backup.backup_type].icon} 
                                        class="w-5 h-5 text-{backupTypes[backup.backup_type].color}-500 mr-2" 
                                    />
                                    <span class="text-sm text-gray-900">
                                        {backup.backup_type}
                                    </span>
                                    <span class="ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-{statusColors[backup.status]}-100 text-{statusColors[backup.status]}-800">
                                        {backup.status}
                                    </span>
                                </div>
                                <div class="text-sm text-gray-500">
                                    {backup.count} backups
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
                
                <!-- Upcoming Backups -->
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">Upcoming Backups</h3>
                    <div class="space-y-3">
                        {#each dashboard.upcoming_backups as backup}
                            <div class="flex items-center justify-between">
                                <div>
                                    <p class="text-sm font-medium text-gray-900">
                                        {backup.name}
                                    </p>
                                    <p class="text-xs text-gray-500">
                                        {backup.backup_type} → {backup.destination}
                                    </p>
                                </div>
                                <div class="text-sm text-gray-600">
                                    {backup.hours_until_next.toFixed(1)}h
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            </div>
        {/if}
    {/if}
</div>

<!-- Schedule Modal -->
{#if showScheduleModal}
    <BackupScheduleModal
        on:create={e => createSchedule(e.detail)}
        on:close={() => showScheduleModal = false}
    />
{/if}

<!-- Restore Modal -->
{#if showRestoreModal && selectedBackup}
    <RestoreModal
        backup={selectedBackup}
        on:close={() => { showRestoreModal = false; selectedBackup = null; }}
    />
{/if}

<style>
    .spinner {
        width: 2rem;
        height: 2rem;
        border-width: 4px;
        border-color: #c7d2fe;
        border-top-color: #4f46e5;
        border-radius: 9999px;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .btn {
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-weight: 500;
        transition: background-color 0.2s, color 0.2s;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    
    .btn-primary {
        background-color: #4f46e5;
        color: white;
    }
    
    .btn-primary:hover {
        background-color: #4338ca;
    }
    
    .btn-secondary {
        background-color: #e5e7eb;
        color: #1f2937;
    }
    
    .btn-secondary:hover {
        background-color: #d1d5db;
    }
    
    .btn-sm {
        padding: 0.375rem 0.75rem;
        font-size: 0.875rem;
    }
    
    .alert {
        padding: 1rem;
        border-radius: 0.375rem;
    }
    
    .alert-error {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
</style>