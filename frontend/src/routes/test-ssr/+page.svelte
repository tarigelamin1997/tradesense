<script lang="ts">
	import { browser } from '$app/environment';
	
	// This will be set during SSR and hydration
	const renderTime = new Date().toISOString();
	const isBrowser = browser;
</script>

<h1>SSR Test Page</h1>
<p>This page tests if basic SSR is working on Vercel.</p>

<ul>
	<li>Rendered at: {renderTime}</li>
	<li>Is browser: {isBrowser}</li>
	<li>Environment: {import.meta.env.MODE}</li>
</ul>

<p>If you can see this page, basic SSR is working!</p>

<style>
	h1 {
		color: #333;
		margin-bottom: 1rem;
	}
	
	ul {
		background: #f5f5f5;
		padding: 1rem;
		border-radius: 4px;
		list-style-type: none;
	}
	
	li {
		margin: 0.5rem 0;
		font-family: monospace;
	}
</style>