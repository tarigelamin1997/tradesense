<script lang="ts">
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import { dev } from '$app/environment';
	import { onMount } from 'svelte';
	
	let isSSRError = false;
	let errorCode = '';
	
	$: {
		// Check if this is an SSR-specific error
		errorCode = ($page.error as any)?.code || '';
		isSSRError = errorCode?.startsWith('SSR_');
	}
	
	// Log client-side errors for debugging
	onMount(() => {
		if (dev && $page.error) {
			console.error('Client-side error:', $page.error);
		}
	});
</script>

<svelte:head>
	<title>{$page.status} - TradeSense</title>
</svelte:head>

<div class="error-container">
	<h1>{$page.status}</h1>
	
	{#if isSSRError}
		<div class="ssr-error">
			<p class="error-title">Server Rendering Error</p>
			<p class="error-message">The application encountered an issue during server-side rendering.</p>
			{#if browser}
				<p class="error-recovery">The page should work correctly now that it's loaded in your browser.</p>
			{/if}
		</div>
	{:else}
		<p>{$page.error?.message || 'An unexpected error occurred'}</p>
	{/if}
	
	{#if dev && ($page.error?.stack || errorCode)}
		<details class="debug-info">
			<summary>Debug Information (development only)</summary>
			{#if errorCode}
				<p><strong>Error Code:</strong> {errorCode}</p>
			{/if}
			{#if $page.error?.stack}
				<pre>{$page.error.stack}</pre>
			{/if}
		</details>
	{/if}
	
	<div class="actions">
		{#if $page.status === 404}
			<a href="/" class="primary-action">Go to Dashboard</a>
		{:else if isSSRError && browser}
			<button on:click={() => window.location.href = '/'} class="primary-action">
				Go to Dashboard
			</button>
		{:else}
			<button on:click={() => browser && window.location.reload()} class="primary-action">
				Try Again
			</button>
		{/if}
	</div>
	
	{#if $page.status === 500 && !isSSRError}
		<p class="help-text">If this error persists, please contact support.</p>
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
	
	.ssr-error {
		background-color: #fef3c7;
		border: 1px solid #f59e0b;
		border-radius: 8px;
		padding: 1.5rem;
		margin-bottom: 2rem;
		max-width: 600px;
	}
	
	.error-title {
		font-weight: 600;
		color: #92400e;
		margin-bottom: 0.5rem;
	}
	
	.error-message {
		color: #78350f;
		margin-bottom: 0.5rem;
	}
	
	.error-recovery {
		color: #78350f;
		font-style: italic;
	}
	
	.debug-info {
		margin: 2rem 0;
		padding: 1rem;
		background-color: #f3f4f6;
		border-radius: 8px;
		max-width: 800px;
		text-align: left;
	}
	
	.debug-info summary {
		cursor: pointer;
		font-weight: 500;
		margin-bottom: 0.5rem;
	}
	
	.debug-info pre {
		overflow-x: auto;
		font-size: 0.875rem;
		margin-top: 1rem;
	}
	
	.actions {
		margin: 2rem 0;
	}
	
	.primary-action {
		background: #10b981;
		color: white;
		padding: 0.75rem 1.5rem;
		border-radius: 6px;
		text-decoration: none;
		border: none;
		cursor: pointer;
		font-size: 1rem;
		transition: background 0.2s;
		display: inline-block;
	}
	
	.primary-action:hover {
		background: #059669;
	}
	
	.help-text {
		color: #6b7280;
		font-size: 0.875rem;
		margin-top: 1rem;
	}
</style>