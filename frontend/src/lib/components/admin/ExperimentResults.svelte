<script>
    import { createEventDispatcher } from 'svelte';
    
    export let experimentId;
    
    const dispatch = createEventDispatcher();
    
    function handleClose() {
        dispatch('close');
    }
</script>

<div class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div class="p-6">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-semibold">Experiment Results</h2>
                <button
                    on:click={handleClose}
                    class="text-gray-400 hover:text-gray-500"
                >
                    <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
            
            <div class="text-center py-12">
                <p class="text-gray-500">Experiment results for ID: {experimentId}</p>
                <p class="text-sm text-gray-400 mt-2">Results view not yet implemented</p>
            </div>
        </div>
    </div>
</div>