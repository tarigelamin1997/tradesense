<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	
	let isOpen = false;
	let logs: Array<{
		id: number;
		timestamp: string;
		type: 'request' | 'response' | 'error' | 'info';
		method?: string;
		url?: string;
		status?: number;
		message?: string;
		details?: any;
	}> = [];
	let logId = 0;
	
	// API Configuration
	const apiConfig = {
		VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
		VITE_API_URL: import.meta.env.VITE_API_URL,
		VITE_WS_URL: import.meta.env.VITE_WS_URL,
		MODE: import.meta.env.MODE,
		DEV: import.meta.env.DEV,
		PROD: import.meta.env.PROD
	};
	
	// Original fetch
	let originalFetch: typeof fetch;
	
	function addLog(log: Omit<typeof logs[0], 'id' | 'timestamp'>) {
		logs = [
			{
				id: logId++,
				timestamp: new Date().toISOString(),
				...log
			},
			...logs
		].slice(0, 50); // Keep only last 50 logs
	}
	
	// Intercept fetch
	function interceptFetch() {
		if (!browser || !window.fetch) return;
		
		originalFetch = window.fetch;
		
		window.fetch = async function(...args) {
			const [input, init] = args;
			const url = input instanceof Request ? input.url : input.toString();
			const method = (init?.method || 'GET').toUpperCase();
			
			// Log request
			addLog({
				type: 'request',
				method,
				url,
				details: {
					headers: init?.headers,
					body: init?.body
				}
			});
			
			try {
				const response = await originalFetch.apply(this, args);
				const clonedResponse = response.clone();
				
				// Log response
				addLog({
					type: 'response',
					method,
					url,
					status: response.status,
					message: `${response.status} ${response.statusText}`,
					details: {
						headers: Object.fromEntries(response.headers.entries()),
						ok: response.ok
					}
				});
				
				// If it's an error response, try to get the body
				if (!response.ok) {
					try {
						const errorData = await clonedResponse.json();
						addLog({
							type: 'error',
							url,
							message: errorData.detail || errorData.message || 'Unknown error',
							details: errorData
						});
					} catch (e) {
						// Ignore JSON parse errors
					}
				}
				
				return response;
			} catch (error) {
				// Log error
				addLog({
					type: 'error',
					method,
					url,
					message: error instanceof Error ? error.message : 'Network error',
					details: error
				});
				throw error;
			}
		};
	}
	
	// Restore original fetch
	function restoreFetch() {
		if (browser && originalFetch) {
			window.fetch = originalFetch;
		}
	}
	
	onMount(() => {
		if (browser) {
			interceptFetch();
			
			// Add initial info log
			addLog({
				type: 'info',
				message: 'Debug panel initialized',
				details: apiConfig
			});
			
			// Listen for keyboard shortcut (Ctrl/Cmd + Shift + D)
			const handleKeydown = (e: KeyboardEvent) => {
				if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
					e.preventDefault();
					isOpen = !isOpen;
				}
			};
			
			window.addEventListener('keydown', handleKeydown);
			
			return () => {
				window.removeEventListener('keydown', handleKeydown);
				restoreFetch();
			};
		}
	});
	
	onDestroy(() => {
		restoreFetch();
	});
	
	function clearLogs() {
		logs = [];
		addLog({
			type: 'info',
			message: 'Logs cleared'
		});
	}
	
	function copyToClipboard(text: string) {
		navigator.clipboard.writeText(text);
	}
	
	function exportLogs() {
		const exportData = {
			timestamp: new Date().toISOString(),
			config: apiConfig,
			logs: logs
		};
		
		const json = JSON.stringify(exportData, null, 2);
		copyToClipboard(json);
		
		addLog({
			type: 'info',
			message: 'Logs copied to clipboard'
		});
	}
	
	function getLogColor(type: string) {
		switch (type) {
			case 'request': return '#3b82f6';
			case 'response': return '#10b981';
			case 'error': return '#ef4444';
			case 'info': return '#6b7280';
			default: return '#6b7280';
		}
	}
</script>

{#if browser}
	<!-- Toggle Button -->
	<button
		on:click={() => isOpen = !isOpen}
		class="debug-toggle"
		title="Toggle Debug Panel (Ctrl+Shift+D)"
		aria-label="Toggle Debug Panel"
	>
		<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
			<path d="M12 2a10 10 0 1 0 10 10H12V2z"/>
			<path d="M12 12L20.4 3.6"/>
			<circle cx="12" cy="12" r="3"/>
		</svg>
		{#if logs.filter(l => l.type === 'error').length > 0}
			<span class="error-badge">{logs.filter(l => l.type === 'error').length}</span>
		{/if}
	</button>
	
	<!-- Debug Panel -->
	{#if isOpen}
		<div class="debug-panel">
			<div class="panel-header">
				<h3>Debug Panel</h3>
				<div class="actions">
					<button on:click={clearLogs} title="Clear logs">Clear</button>
					<button on:click={exportLogs} title="Export logs">Export</button>
					<button on:click={() => isOpen = false} title="Close">×</button>
				</div>
			</div>
			
			<div class="panel-content">
				<!-- Configuration Section -->
				<div class="config-section">
					<h4>API Configuration</h4>
					<div class="config-grid">
						{#each Object.entries(apiConfig) as [key, value]}
							<div class="config-item">
								<span class="key">{key}:</span>
								<span class="value" title={String(value)}>{value || 'Not set'}</span>
							</div>
						{/each}
					</div>
				</div>
				
				<!-- Logs Section -->
				<div class="logs-section">
					<h4>Network Logs ({logs.length})</h4>
					<div class="logs-container">
						{#each logs as log (log.id)}
							<div class="log-entry" style="border-left-color: {getLogColor(log.type)}">
								<div class="log-header">
									<span class="log-time">{new Date(log.timestamp).toLocaleTimeString()}</span>
									<span class="log-type" style="color: {getLogColor(log.type)}">{log.type.toUpperCase()}</span>
									{#if log.method}
										<span class="log-method">{log.method}</span>
									{/if}
									{#if log.status}
										<span class="log-status" class:error={log.status >= 400}>{log.status}</span>
									{/if}
								</div>
								{#if log.url}
									<div class="log-url">{log.url}</div>
								{/if}
								{#if log.message}
									<div class="log-message">{log.message}</div>
								{/if}
								{#if log.details}
									<details>
										<summary>Details</summary>
										<pre>{JSON.stringify(log.details, null, 2)}</pre>
									</details>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			</div>
		</div>
	{/if}
{/if}

<style>
	.debug-toggle {
		position: fixed;
		bottom: 20px;
		right: 20px;
		width: 48px;
		height: 48px;
		border-radius: 50%;
		background: #1f2937;
		color: white;
		border: 2px solid #374151;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 9998;
		box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
		transition: all 0.2s;
	}
	
	.debug-toggle:hover {
		background: #374151;
		transform: scale(1.05);
	}
	
	.error-badge {
		position: absolute;
		top: -4px;
		right: -4px;
		background: #ef4444;
		color: white;
		font-size: 10px;
		font-weight: bold;
		padding: 2px 6px;
		border-radius: 10px;
		min-width: 18px;
		text-align: center;
	}
	
	.debug-panel {
		position: fixed;
		bottom: 80px;
		right: 20px;
		width: 500px;
		max-width: calc(100vw - 40px);
		height: 600px;
		max-height: calc(100vh - 100px);
		background: #1f2937;
		border: 1px solid #374151;
		border-radius: 8px;
		box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.3);
		z-index: 9997;
		display: flex;
		flex-direction: column;
		color: #e5e7eb;
	}
	
	.panel-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 12px 16px;
		border-bottom: 1px solid #374151;
		background: #111827;
		border-radius: 8px 8px 0 0;
	}
	
	.panel-header h3 {
		margin: 0;
		font-size: 16px;
		font-weight: 600;
		color: white;
	}
	
	.actions {
		display: flex;
		gap: 8px;
	}
	
	.actions button {
		background: #374151;
		color: #e5e7eb;
		border: none;
		padding: 4px 12px;
		border-radius: 4px;
		cursor: pointer;
		font-size: 14px;
		transition: background 0.2s;
	}
	
	.actions button:hover {
		background: #4b5563;
	}
	
	.panel-content {
		flex: 1;
		overflow-y: auto;
		padding: 16px;
	}
	
	.config-section {
		margin-bottom: 20px;
		padding-bottom: 20px;
		border-bottom: 1px solid #374151;
	}
	
	.config-section h4 {
		margin: 0 0 12px 0;
		font-size: 14px;
		font-weight: 600;
		color: #9ca3af;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.config-grid {
		display: grid;
		gap: 8px;
	}
	
	.config-item {
		display: flex;
		align-items: center;
		font-size: 13px;
		font-family: monospace;
	}
	
	.config-item .key {
		color: #9ca3af;
		margin-right: 8px;
	}
	
	.config-item .value {
		color: #60a5fa;
		word-break: break-all;
		flex: 1;
	}
	
	.logs-section h4 {
		margin: 0 0 12px 0;
		font-size: 14px;
		font-weight: 600;
		color: #9ca3af;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.logs-container {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	
	.log-entry {
		background: #111827;
		border: 1px solid #374151;
		border-left-width: 3px;
		border-radius: 4px;
		padding: 8px 12px;
		font-size: 12px;
		font-family: monospace;
	}
	
	.log-header {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 4px;
	}
	
	.log-time {
		color: #6b7280;
		font-size: 11px;
	}
	
	.log-type {
		font-weight: 600;
		font-size: 11px;
	}
	
	.log-method {
		color: #a78bfa;
		font-weight: 600;
	}
	
	.log-status {
		color: #10b981;
		font-weight: 600;
	}
	
	.log-status.error {
		color: #ef4444;
	}
	
	.log-url {
		color: #60a5fa;
		word-break: break-all;
		margin-bottom: 4px;
	}
	
	.log-message {
		color: #e5e7eb;
		margin-top: 4px;
	}
	
	details {
		margin-top: 8px;
	}
	
	summary {
		cursor: pointer;
		color: #9ca3af;
		font-size: 11px;
		user-select: none;
	}
	
	pre {
		margin: 4px 0 0 0;
		padding: 8px;
		background: #030712;
		border-radius: 4px;
		overflow-x: auto;
		font-size: 11px;
		color: #d1d5db;
		line-height: 1.4;
	}
	
	@media (max-width: 640px) {
		.debug-panel {
			width: calc(100vw - 20px);
			right: 10px;
			bottom: 70px;
		}
		
		.debug-toggle {
			right: 10px;
			bottom: 10px;
		}
	}
</style>