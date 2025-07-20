<script>
    import { createEventDispatcher } from 'svelte';
    
    const dispatch = createEventDispatcher();
    
    let schedule = {
        enabled: false,
        frequency: 'daily',
        time: '03:00',
        retention_days: 30
    };
    
    function handleSave() {
        dispatch('save', schedule);
    }
    
    function handleClose() {
        dispatch('close');
    }
</script>

<div class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div class="p-6">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-semibold">Backup Schedule</h2>
                <button
                    on:click={handleClose}
                    class="text-gray-400 hover:text-gray-500"
                >
                    <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            
            <form on:submit|preventDefault={handleSave} class="space-y-4">
                <div>
                    <label class="flex items-center">
                        <input
                            type="checkbox"
                            bind:checked={schedule.enabled}
                            class="rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
                        />
                        <span class="ml-2 text-sm font-medium text-gray-700">Enable automatic backups</span>
                    </label>
                </div>
                
                {#if schedule.enabled}
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Frequency
                        </label>
                        <select
                            bind:value={schedule.frequency}
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        >
                            <option value="hourly">Hourly</option>
                            <option value="daily">Daily</option>
                            <option value="weekly">Weekly</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Time
                        </label>
                        <input
                            type="time"
                            bind:value={schedule.time}
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Retention (days)
                        </label>
                        <input
                            type="number"
                            bind:value={schedule.retention_days}
                            min="1"
                            max="365"
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                    </div>
                {/if}
                
                <div class="flex justify-end space-x-3 pt-4">
                    <button
                        type="button"
                        on:click={handleClose}
                        class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                        Save Schedule
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<style>
    input[type="time"], input[type="number"], select {
        border: 1px solid #d1d5db;
        padding: 0.5rem 0.75rem;
    }
</style>