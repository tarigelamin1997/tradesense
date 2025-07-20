<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/api/client';
    import Icon from '$lib/components/Icon.svelte';
    import { slide } from 'svelte/transition';
    
    export let compact = false;
    
    let checklist = [];
    let loading = true;
    let expanded = !compact;
    let progress = 0;
    
    async function loadChecklist() {
        try {
            loading = true;
            const response = await api.get('/onboarding/checklist');
            checklist = response.checklist;
            
            // Calculate progress
            const completed = checklist.filter(item => item.completed).length;
            progress = checklist.length > 0 ? Math.round((completed / checklist.length) * 100) : 0;
            
        } catch (err) {
            console.error('Failed to load onboarding checklist:', err);
        } finally {
            loading = false;
        }
    }
    
    function getStepIcon(stepId) {
        const icons = {
            profile_setup: 'user',
            trading_preferences: 'settings',
            first_trade: 'upload',
            analytics_tour: 'bar-chart-2',
            plan_selection: 'credit-card'
        };
        return icons[stepId] || 'check-square';
    }
    
    function getStepLink(stepId) {
        const links = {
            profile_setup: '/settings/profile',
            trading_preferences: '/settings/preferences',
            first_trade: '/trades/import',
            analytics_tour: '/analytics',
            plan_selection: '/subscription'
        };
        return links[stepId] || '#';
    }
    
    onMount(() => {
        loadChecklist();
    });
</script>

{#if !loading && checklist.length > 0 && progress < 100}
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden" transition:slide>
        <div class="p-4">
            <div class="flex items-center justify-between mb-3">
                <div class="flex items-center">
                    <Icon name="clipboard-list" class="w-5 h-5 text-indigo-600 mr-2" />
                    <h3 class="text-sm font-medium text-gray-900">Getting Started</h3>
                </div>
                {#if compact}
                    <button
                        on:click={() => expanded = !expanded}
                        class="text-gray-400 hover:text-gray-600"
                    >
                        <Icon name={expanded ? 'chevron-up' : 'chevron-down'} class="w-5 h-5" />
                    </button>
                {/if}
            </div>
            
            <!-- Progress bar -->
            <div class="mb-3">
                <div class="flex justify-between text-xs text-gray-600 mb-1">
                    <span>{checklist.filter(item => item.completed).length} of {checklist.length} completed</span>
                    <span>{progress}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div 
                        class="bg-indigo-600 rounded-full h-2 transition-all duration-500"
                        style="width: {progress}%"
                    ></div>
                </div>
            </div>
            
            {#if !compact || expanded}
                <div class="space-y-2" transition:slide>
                    {#each checklist as item}
                        <a
                            href={getStepLink(item.id)}
                            class="flex items-center p-2 rounded-md hover:bg-gray-50 transition-colors
                                   {item.completed ? 'opacity-60' : ''}"
                        >
                            <div class="flex-shrink-0 mr-3">
                                {#if item.completed}
                                    <div class="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
                                        <Icon name="check" class="w-4 h-4 text-green-600" />
                                    </div>
                                {:else}
                                    <div class="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center">
                                        <Icon name={getStepIcon(item.id)} class="w-4 h-4 text-gray-400" />
                                    </div>
                                {/if}
                            </div>
                            <div class="flex-1">
                                <p class="text-sm font-medium text-gray-900 {item.completed ? 'line-through' : ''}">
                                    {item.title}
                                </p>
                                <p class="text-xs text-gray-500">{item.description}</p>
                            </div>
                            {#if item.required && !item.completed}
                                <span class="text-xs text-orange-600 font-medium">Required</span>
                            {/if}
                        </a>
                    {/each}
                </div>
            {/if}
        </div>
        
        {#if progress === 100}
            <div class="bg-green-50 border-t border-green-200 p-3">
                <p class="text-sm text-green-800 text-center">
                    🎉 Congratulations! You've completed all setup steps.
                </p>
            </div>
        {:else if !compact}
            <div class="bg-gray-50 border-t border-gray-200 p-3">
                <a 
                    href="/onboarding"
                    class="text-sm text-indigo-600 hover:text-indigo-700 font-medium text-center block"
                >
                    Resume setup →
                </a>
            </div>
        {/if}
    </div>
{/if}