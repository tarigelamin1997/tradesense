<script>
    import { createEventDispatcher } from 'svelte';
    
    export let backup = null;
    
    const dispatch = createEventDispatcher();
    
    function handleRestore() {
        dispatch('restore', backup);
    }
    
    function handleClose() {
        dispatch('close');
    }
</script>

{#if backup}
<div class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div class="p-6">
            <div class="flex items-center mb-4">
                <svg class="h-6 w-6 text-yellow-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <h2 class="text-xl font-semibold">Restore Backup</h2>
            </div>
            
            <p class="text-gray-600 mb-4">
                Are you sure you want to restore this backup? This will replace all current data with the backup data.
            </p>
            
            <div class="bg-gray-50 rounded p-3 mb-4">
                <p class="text-sm font-medium">Backup Details:</p>
                <p class="text-sm text-gray-600">ID: {backup.id}</p>
                <p class="text-sm text-gray-600">Created: {new Date(backup.created_at).toLocaleString()}</p>
            </div>
            
            <div class="flex justify-end space-x-3">
                <button
                    type="button"
                    on:click={handleClose}
                    class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                    Cancel
                </button>
                <button
                    type="button"
                    on:click={handleRestore}
                    class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                    Restore Backup
                </button>
            </div>
        </div>
    </div>
</div>
{/if}