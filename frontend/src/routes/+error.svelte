<script>
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
</script>

<svelte:head>
	<title>{$page.status} - TradeSense</title>
</svelte:head>

<div class="error-container">
	<h1>{$page.status}</h1>
	<p>{$page.error?.message || 'An unexpected error occurred'}</p>
	
	{#if $page.status === 404}
		<a href="/">Go to Dashboard</a>
	{:else}
		<button on:click={() => browser && window.location.reload()}>Try Again</button>
	{/if}
</div>

<style>
	.error-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 50vh;
		text-align: center;
		padding: 2rem;
	}
	
	h1 {
		font-size: 4rem;
		margin-bottom: 1rem;
		color: #666;
	}
	
	p {
		font-size: 1.25rem;
		color: #666;
		margin-bottom: 2rem;
	}
	
	a, button {
		background: #10b981;
		color: white;
		padding: 0.75rem 1.5rem;
		border-radius: 6px;
		text-decoration: none;
		border: none;
		cursor: pointer;
		font-size: 1rem;
		transition: background 0.2s;
	}
	
	a:hover, button:hover {
		background: #059669;
	}
</style>