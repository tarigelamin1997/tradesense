<script lang="ts">
	import LoadingSpinner from './LoadingSpinner.svelte';
	
	export let message = 'Loading...';
	export let fullHeight = true;
	export let centered = true;
</script>

<div
	class="flex flex-col items-center justify-center gap-4 {fullHeight ? 'min-h-[400px]' : ''} {centered ? 'w-full' : ''}"
>
	<LoadingSpinner size="lg" />
	<p class="text-gray-600 dark:text-gray-400 text-sm">{message}</p>
</div>