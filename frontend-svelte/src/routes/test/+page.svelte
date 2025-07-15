<script>
	import { onMount } from 'svelte';
	import axios from 'axios';
	
	let status = 'Testing axios...';
	
	onMount(async () => {
		try {
			// Test that axios is loaded
			status = `Axios loaded: ${typeof axios === 'function'}`;
		} catch (error) {
			status = `Error: ${error.message}`;
		}
	});
</script>

<h1>Axios Test</h1>
<p>{status}</p>