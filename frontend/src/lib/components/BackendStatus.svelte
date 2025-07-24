<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	
	let backendStatus: 'checking' | 'online' | 'offline' = 'checking';
	let showBanner = false;
	
	async function checkBackendStatus() {
		if (!browser) return;
		
		try {
			const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/docs`, {
				method: 'HEAD',
				mode: 'no-cors' // Use no-cors to avoid CORS errors
			});
			backendStatus = 'online';
			showBanner = false;
		} catch (error) {
			backendStatus = 'offline';
			showBanner = true;
		}
	}
	
	onMount(() => {
		checkBackendStatus();
		// Check every 10 seconds
		const interval = setInterval(checkBackendStatus, 10000);
		
		return () => clearInterval(interval);
	});
</script>

{#if showBanner && backendStatus === 'offline'}
	<div class="backend-banner">
		<div class="container">
			<div class="content">
				<svg class="icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<circle cx="12" cy="12" r="10"></circle>
					<line x1="12" y1="8" x2="12" y2="12"></line>
					<line x1="12" y1="16" x2="12.01" y2="16"></line>
				</svg>
				<span class="message">
					Backend server is not running. Please start the backend on port 8000.
				</span>
				<button on:click={() => showBanner = false} class="close-btn" aria-label="Close">
					<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<line x1="18" y1="6" x2="6" y2="18"></line>
						<line x1="6" y1="6" x2="18" y2="18"></line>
					</svg>
				</button>
			</div>
			<div class="instructions">
				Run: <code>cd backend && uvicorn main:app --reload</code>
			</div>
		</div>
	</div>
{/if}

<style>
	.backend-banner {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		background: #ef4444;
		color: white;
		z-index: 9999;
		padding: 0.75rem 0;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}
	
	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 0 1rem;
	}
	
	.content {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.5rem;
	}
	
	.icon {
		flex-shrink: 0;
	}
	
	.message {
		flex: 1;
		font-weight: 500;
	}
	
	.close-btn {
		background: none;
		border: none;
		color: white;
		cursor: pointer;
		padding: 0.25rem;
		display: flex;
		align-items: center;
		justify-content: center;
		opacity: 0.8;
		transition: opacity 0.2s;
	}
	
	.close-btn:hover {
		opacity: 1;
	}
	
	.instructions {
		font-size: 0.875rem;
		opacity: 0.9;
		margin-left: 2rem;
	}
	
	code {
		background: rgba(0, 0, 0, 0.2);
		padding: 0.125rem 0.5rem;
		border-radius: 0.25rem;
		font-family: monospace;
		font-size: 0.875rem;
	}
	
	@media (max-width: 640px) {
		.content {
			flex-wrap: wrap;
		}
		
		.instructions {
			margin-left: 0;
			margin-top: 0.5rem;
		}
	}
</style>