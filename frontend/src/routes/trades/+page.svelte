<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	
	// Redirect to /tradelog
	onMount(() => {
		goto('/tradelog', { replaceState: true });
	});
</script>

<div style="padding: 2rem; text-align: center;">
	<p>Redirecting to Trade Log...</p>
</div>