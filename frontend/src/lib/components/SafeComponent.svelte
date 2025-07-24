<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import ErrorBoundary from './ErrorBoundary.svelte';
	
	export let name = 'Component';
	
	let error: Error | null = null;
	let hasError = false;
	
	function handleError(event: ErrorEvent) {
		console.error(`Error in ${name}:`, event.error);
		error = event.error;
		hasError = true;
		event.preventDefault();
	}
	
	function handleUnhandledRejection(event: PromiseRejectionEvent) {
		console.error(`Unhandled promise rejection in ${name}:`, event.reason);
		error = new Error(event.reason);
		hasError = true;
		event.preventDefault();
	}
	
	function reset() {
		error = null;
		hasError = false;
	}
	
	onMount(() => {
		window.addEventListener('error', handleError);
		window.addEventListener('unhandledrejection', handleUnhandledRejection);
	});
	
	onDestroy(() => {
		window.removeEventListener('error', handleError);
		window.removeEventListener('unhandledrejection', handleUnhandledRejection);
	});
</script>

{#if hasError}
	<ErrorBoundary {error} {reset} />
{:else}
	<slot />
{/if}