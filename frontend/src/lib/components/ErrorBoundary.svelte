<script lang="ts">
	import { onMount } from 'svelte';
	import { AlertTriangle, RefreshCw, Home } from 'lucide-svelte';
	
	export let error: Error | null = null;
	export let reset: (() => void) | null = null;
	
	let errorDetails = false;
	
	onMount(() => {
		// Log error to monitoring service
		if (error) {
			console.error('Error Boundary caught:', error);
			// TODO: Send to error tracking service (Sentry, etc.)
		}
	});
	
	function handleReset() {
		if (reset) {
			reset();
		} else {
			location.reload();
		}
	}
</script>

<div class="min-h-[400px] flex items-center justify-center p-4">
	<div class="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
		<div class="flex items-center justify-center mb-4">
			<div class="bg-red-100 dark:bg-red-900/20 rounded-full p-3">
				<AlertTriangle class="h-8 w-8 text-red-600 dark:text-red-400" />
			</div>
		</div>
		
		<h2 class="text-xl font-semibold text-gray-900 dark:text-white text-center mb-2">
			Something went wrong
		</h2>
		
		<p class="text-gray-600 dark:text-gray-400 text-center mb-6">
			We encountered an unexpected error. Please try refreshing the page.
		</p>
		
		{#if error && errorDetails}
			<div class="mb-6 p-3 bg-gray-100 dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-700">
				<p class="text-sm font-mono text-gray-700 dark:text-gray-300 break-all">
					{error.message}
				</p>
				{#if error.stack}
					<details class="mt-2">
						<summary class="text-xs text-gray-500 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300">
							Stack trace
						</summary>
						<pre class="mt-2 text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">{error.stack}</pre>
					</details>
				{/if}
			</div>
		{/if}
		
		<div class="flex flex-col sm:flex-row gap-3">
			<button
				on:click={handleReset}
				class="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
			>
				<RefreshCw class="h-4 w-4" />
				Try Again
			</button>
			
			<a
				href="/"
				class="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
			>
				<Home class="h-4 w-4" />
				Go Home
			</a>
		</div>
		
		{#if error && !errorDetails}
			<button
				on:click={() => errorDetails = true}
				class="mt-4 text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 underline w-full text-center"
			>
				Show error details
			</button>
		{/if}
	</div>
</div>