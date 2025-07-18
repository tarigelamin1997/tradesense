<script>
	import { onMount } from 'svelte';
	
	let status = 'Loading...';
	let details = {};
	
	onMount(() => {
		status = 'Page loaded successfully!';
		details = {
			url: window.location.href,
			userAgent: navigator.userAgent,
			timestamp: new Date().toISOString()
		};
	});
</script>

<div style="padding: 2rem;">
	<h1>Debug Page</h1>
	<p>Status: {status}</p>
	<pre>{JSON.stringify(details, null, 2)}</pre>
	
	<h2>Navigation Links</h2>
	<ul>
		<li><a href="/">Home</a></li>
		<li><a href="/login">Login</a></li>
		<li><a href="/register">Register</a></li>
		<li><a href="/tradelog">Trade Log</a></li>
	</ul>
</div>