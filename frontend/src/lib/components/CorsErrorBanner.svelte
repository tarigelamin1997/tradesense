<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	
	let showBanner = false;
	let corsError = false;
	let deploymentUrl = '';
	
	onMount(() => {
		if (browser) {
			deploymentUrl = window.location.origin;
			
			// Check if we're on a problematic Vercel URL
			if (deploymentUrl.includes('vercel.app') && 
			    !deploymentUrl.includes('tradesense.vercel.app') &&
			    !deploymentUrl.includes('frontend-og3gd5s4j')) {
				showBanner = true;
			}
		}
	});
	
	export function handleCorsError() {
		corsError = true;
		showBanner = true;
	}
</script>

{#if showBanner}
	<div class="cors-banner">
		<div class="container">
			<div class="content">
				<svg class="icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<circle cx="12" cy="12" r="10"></circle>
					<line x1="12" y1="8" x2="12" y2="12"></line>
					<line x1="12" y1="16" x2="12.01" y2="16"></line>
				</svg>
				<div class="message-content">
					<strong>CORS Configuration Issue Detected</strong>
					{#if corsError}
						<p>The backend is blocking requests from this URL: <code>{deploymentUrl}</code></p>
					{:else}
						<p>This deployment URL may experience connection issues.</p>
					{/if}
				</div>
				<button on:click={() => showBanner = false} class="close-btn" aria-label="Close">
					<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<line x1="18" y1="6" x2="6" y2="18"></line>
						<line x1="6" y1="6" x2="18" y2="18"></line>
					</svg>
				</button>
			</div>
			<div class="solutions">
				<h4>Solutions:</h4>
				<ol>
					<li><strong>Wait for backend update</strong> - The backend services are being updated to accept this URL (ETA: 5-10 minutes)</li>
					<li><strong>Use the main URL</strong> - Visit <a href="https://tradesense.vercel.app">https://tradesense.vercel.app</a> instead</li>
					<li><strong>Run locally</strong> - Clone the repo and run <code>npm run dev</code></li>
					<li><strong>Browser extension</strong> - Temporarily install a CORS unblock extension</li>
				</ol>
			</div>
			<div class="status">
				<strong>Deployment Status:</strong> Backend CORS update in progress... 
				<button on:click={() => window.location.reload()} class="retry-btn">Retry</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.cors-banner {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		background: #fef3c7;
		border-bottom: 2px solid #f59e0b;
		color: #92400e;
		z-index: 10000;
		padding: 1rem 0;
		box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
		max-height: 50vh;
		overflow-y: auto;
	}
	
	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 0 1rem;
	}
	
	.content {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
		margin-bottom: 1rem;
	}
	
	.icon {
		flex-shrink: 0;
		color: #f59e0b;
		margin-top: 2px;
	}
	
	.message-content {
		flex: 1;
	}
	
	.message-content strong {
		display: block;
		margin-bottom: 0.25rem;
		color: #92400e;
		font-size: 1.1rem;
	}
	
	.message-content p {
		margin: 0;
		font-size: 0.95rem;
	}
	
	.message-content code {
		background: rgba(0, 0, 0, 0.1);
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		font-family: monospace;
		font-size: 0.875rem;
	}
	
	.close-btn {
		background: none;
		border: none;
		color: #92400e;
		cursor: pointer;
		padding: 0.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		opacity: 0.7;
		transition: opacity 0.2s;
	}
	
	.close-btn:hover {
		opacity: 1;
	}
	
	.solutions {
		background: rgba(255, 255, 255, 0.5);
		padding: 1rem;
		border-radius: 0.5rem;
		margin-bottom: 1rem;
	}
	
	.solutions h4 {
		margin: 0 0 0.5rem 0;
		color: #92400e;
		font-size: 1rem;
	}
	
	.solutions ol {
		margin: 0;
		padding-left: 1.5rem;
	}
	
	.solutions li {
		margin-bottom: 0.5rem;
		font-size: 0.9rem;
	}
	
	.solutions strong {
		color: #92400e;
	}
	
	.solutions a {
		color: #2563eb;
		text-decoration: underline;
	}
	
	.solutions code {
		background: rgba(0, 0, 0, 0.1);
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		font-family: monospace;
		font-size: 0.875rem;
	}
	
	.status {
		display: flex;
		align-items: center;
		gap: 1rem;
		font-size: 0.9rem;
		padding: 0.5rem 1rem;
		background: rgba(255, 255, 255, 0.3);
		border-radius: 0.375rem;
	}
	
	.retry-btn {
		background: #f59e0b;
		color: white;
		border: none;
		padding: 0.375rem 1rem;
		border-radius: 0.375rem;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.2s;
	}
	
	.retry-btn:hover {
		background: #d97706;
	}
	
	@media (max-width: 640px) {
		.content {
			flex-wrap: wrap;
		}
		
		.solutions {
			font-size: 0.85rem;
		}
		
		.status {
			flex-wrap: wrap;
			gap: 0.5rem;
		}
	}
</style>