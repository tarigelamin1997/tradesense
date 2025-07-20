<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/api/client-safe';
    import Icon from '$lib/components/Icon.svelte';
    import ExperimentCard from '$lib/components/admin/ExperimentCard.svelte';
    import CreateExperimentModal from '$lib/components/admin/CreateExperimentModal.svelte';
    import ExperimentResults from '$lib/components/admin/ExperimentResults.svelte';
    
    let experiments = [];
    let loading = true;
    let error = null;
    let selectedExperiment = null;
    let showCreateModal = false;
    let filter = 'all';
    
    const statusColors = {
        draft: 'gray',
        running: 'green',
        paused: 'yellow',
        completed: 'blue',
        archived: 'gray'
    };
    
    async function loadExperiments() {
        try {
            loading = true;
            error = null;
            
            const params = new URLSearchParams();
            if (filter !== 'all') {
                params.append('status', filter);
            }
            params.append('include_archived', filter === 'archived');
            
            experiments = await api.get(`/experiments/list?${params}`);
            
        } catch (err) {
            error = err.message || 'Failed to load experiments';
        } finally {
            loading = false;
        }
    }
    
    async function createExperiment(experimentConfig) {
        try {
            await api.post('/experiments/create', experimentConfig);
            showCreateModal = false;
            await loadExperiments();
        } catch (err) {
            throw new Error(err.message || 'Failed to create experiment');
        }
    }
    
    async function startExperiment(experimentId) {
        try {
            await api.post(`/experiments/${experimentId}/start`);
            await loadExperiments();
        } catch (err) {
            alert(err.message || 'Failed to start experiment');
        }
    }
    
    async function stopExperiment(experimentId) {
        const reason = prompt('Reason for stopping the experiment:');
        if (reason === null) return;
        
        try {
            await api.post(`/experiments/${experimentId}/stop?reason=${encodeURIComponent(reason)}`);
            await loadExperiments();
        } catch (err) {
            alert(err.message || 'Failed to stop experiment');
        }
    }
    
    function getExperimentStats() {
        const stats = {
            total: experiments.length,
            running: 0,
            draft: 0,
            completed: 0
        };
        
        experiments.forEach(exp => {
            if (exp.status === 'running') stats.running++;
            else if (exp.status === 'draft') stats.draft++;
            else if (exp.status === 'completed') stats.completed++;
        });
        
        return stats;
    }
    
    onMount(() => {
        loadExperiments();
    });
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
        <div class="flex justify-between items-center">
            <div>
                <h1 class="text-3xl font-bold text-gray-900">A/B Experiments</h1>
                <p class="mt-2 text-gray-600">Manage and analyze your experiments</p>
            </div>
            <button
                on:click={() => showCreateModal = true}
                class="btn btn-primary"
            >
                <Icon name="plus" class="w-5 h-5 mr-2" />
                New Experiment
            </button>
        </div>
    </div>
    
    {#if loading}
        <div class="flex justify-center py-12">
            <div class="spinner"></div>
        </div>
    {:else if error}
        <div class="alert alert-error">{error}</div>
    {:else}
        <!-- Stats Overview -->
        {@const stats = getExperimentStats()}
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-lg bg-gray-100">
                        <Icon name="activity" class="w-6 h-6 text-gray-600" />
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Total</p>
                        <p class="text-2xl font-bold text-gray-900">{stats.total}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-lg bg-green-100">
                        <Icon name="play-circle" class="w-6 h-6 text-green-600" />
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Running</p>
                        <p class="text-2xl font-bold text-gray-900">{stats.running}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-lg bg-yellow-100">
                        <Icon name="edit-3" class="w-6 h-6 text-yellow-600" />
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Draft</p>
                        <p class="text-2xl font-bold text-gray-900">{stats.draft}</p>
                    </div>
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div class="flex items-center">
                    <div class="p-3 rounded-lg bg-blue-100">
                        <Icon name="check-circle" class="w-6 h-6 text-blue-600" />
                    </div>
                    <div class="ml-4">
                        <p class="text-sm font-medium text-gray-600">Completed</p>
                        <p class="text-2xl font-bold text-gray-900">{stats.completed}</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Filter Tabs -->
        <div class="mb-6">
            <div class="border-b border-gray-200">
                <nav class="-mb-px flex space-x-8">
                    <button
                        on:click={() => { filter = 'all'; loadExperiments(); }}
                        class="py-2 px-1 border-b-2 font-medium text-sm"
                        class:border-indigo-500={filter === 'all'}
                        class:text-indigo-600={filter === 'all'}
                        class:border-transparent={filter !== 'all'}
                        class:text-gray-500={filter !== 'all'}
                    >
                        All Experiments
                    </button>
                    <button
                        on:click={() => { filter = 'running'; loadExperiments(); }}
                        class="py-2 px-1 border-b-2 font-medium text-sm"
                        class:border-indigo-500={filter === 'running'}
                        class:text-indigo-600={filter === 'running'}
                        class:border-transparent={filter !== 'running'}
                        class:text-gray-500={filter !== 'running'}
                    >
                        Running
                    </button>
                    <button
                        on:click={() => { filter = 'draft'; loadExperiments(); }}
                        class="py-2 px-1 border-b-2 font-medium text-sm"
                        class:border-indigo-500={filter === 'draft'}
                        class:text-indigo-600={filter === 'draft'}
                        class:border-transparent={filter !== 'draft'}
                        class:text-gray-500={filter !== 'draft'}
                    >
                        Draft
                    </button>
                    <button
                        on:click={() => { filter = 'completed'; loadExperiments(); }}
                        class="py-2 px-1 border-b-2 font-medium text-sm"
                        class:border-indigo-500={filter === 'completed'}
                        class:text-indigo-600={filter === 'completed'}
                        class:border-transparent={filter !== 'completed'}
                        class:text-gray-500={filter !== 'completed'}
                    >
                        Completed
                    </button>
                    <button
                        on:click={() => { filter = 'archived'; loadExperiments(); }}
                        class="py-2 px-1 border-b-2 font-medium text-sm"
                        class:border-indigo-500={filter === 'archived'}
                        class:text-indigo-600={filter === 'archived'}
                        class:border-transparent={filter !== 'archived'}
                        class:text-gray-500={filter !== 'archived'}
                    >
                        Archived
                    </button>
                </nav>
            </div>
        </div>
        
        <!-- Experiments List -->
        {#if experiments.length === 0}
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                <Icon name="flask" class="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 class="text-lg font-medium text-gray-900 mb-2">
                    No experiments found
                </h3>
                <p class="text-gray-600 mb-6">
                    {#if filter === 'all'}
                        Create your first experiment to start testing
                    {:else}
                        No experiments with status "{filter}"
                    {/if}
                </p>
                {#if filter === 'all'}
                    <button
                        on:click={() => showCreateModal = true}
                        class="btn btn-primary"
                    >
                        Create Experiment
                    </button>
                {/if}
            </div>
        {:else}
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {#each experiments as experiment}
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                        <div class="flex justify-between items-start mb-4">
                            <div>
                                <h3 class="text-lg font-semibold text-gray-900">
                                    {experiment.name}
                                </h3>
                                <p class="text-sm text-gray-600 mt-1">
                                    ID: {experiment.id}
                                </p>
                            </div>
                            <span class="px-2.5 py-0.5 rounded-full text-xs font-medium bg-{statusColors[experiment.status]}-100 text-{statusColors[experiment.status]}-800">
                                {experiment.status}
                            </span>
                        </div>
                        
                        <div class="text-sm text-gray-600 space-y-2 mb-4">
                            <div class="flex justify-between">
                                <span>Variants:</span>
                                <span class="font-medium">{experiment.variants_count}</span>
                            </div>
                            <div class="flex justify-between">
                                <span>Metrics:</span>
                                <span class="font-medium">{experiment.metrics_count}</span>
                            </div>
                            <div class="flex justify-between">
                                <span>Created:</span>
                                <span class="font-medium">
                                    {new Date(experiment.created_at).toLocaleDateString()}
                                </span>
                            </div>
                            {#if experiment.started_at}
                                <div class="flex justify-between">
                                    <span>Started:</span>
                                    <span class="font-medium">
                                        {new Date(experiment.started_at).toLocaleDateString()}
                                    </span>
                                </div>
                            {/if}
                        </div>
                        
                        <div class="flex space-x-2">
                            <button
                                on:click={() => selectedExperiment = experiment}
                                class="btn btn-sm btn-secondary"
                            >
                                <Icon name="bar-chart" class="w-4 h-4 mr-1" />
                                View Details
                            </button>
                            
                            {#if experiment.status === 'draft'}
                                <button
                                    on:click={() => startExperiment(experiment.id)}
                                    class="btn btn-sm btn-primary"
                                >
                                    <Icon name="play" class="w-4 h-4 mr-1" />
                                    Start
                                </button>
                            {:else if experiment.status === 'running'}
                                <button
                                    on:click={() => stopExperiment(experiment.id)}
                                    class="btn btn-sm btn-danger"
                                >
                                    <Icon name="stop-circle" class="w-4 h-4 mr-1" />
                                    Stop
                                </button>
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>
        {/if}
    {/if}
</div>

<!-- Create Experiment Modal -->
{#if showCreateModal}
    <CreateExperimentModal
        on:create={e => createExperiment(e.detail)}
        on:close={() => showCreateModal = false}
    />
{/if}

<!-- Experiment Details Modal -->
{#if selectedExperiment}
    <ExperimentResults
        experimentId={selectedExperiment.id}
        on:close={() => selectedExperiment = null}
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
    
    .btn-danger {
        background-color: #dc2626;
        color: white;
    }
    
    .btn-danger:hover {
        background-color: #b91c1c;
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