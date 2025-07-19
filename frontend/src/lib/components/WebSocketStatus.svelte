<script lang="ts">
	import { websocket, wsConnected } from '$lib/stores/websocket';
	import { Wifi, WifiOff, AlertCircle } from 'lucide-svelte';
	
	$: status = $websocket.status;
	$: error = $websocket.error;
</script>

<div class="ws-status" class:connected={$wsConnected}>
	{#if status === 'connected'}
		<Wifi size={16} />
		<span>Live</span>
	{:else if status === 'connecting'}
		<div class="spinner" />
		<span>Connecting...</span>
	{:else if status === 'error'}
		<AlertCircle size={16} />
		<span title={error || 'Connection error'}>Error</span>
	{:else}
		<WifiOff size={16} />
		<span>Offline</span>
	{/if}
</div>

<style>
	.ws-status {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: #fee;
		color: #dc2626;
		border-radius: 20px;
		font-size: 0.875rem;
		font-weight: 500;
		transition: all 0.3s;
	}
	
	.ws-status.connected {
		background: #d1fae5;
		color: #059669;
	}
	
	.spinner {
		width: 16px;
		height: 16px;
		border: 2px solid #f3f4f6;
		border-top-color: #3b82f6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}
	
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>