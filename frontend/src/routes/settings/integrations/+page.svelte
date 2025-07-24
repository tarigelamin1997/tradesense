<script lang="ts">
	import { 
		Link, Check, X, Settings2, ExternalLink,
		AlertCircle, Shield, Loader2
	} from 'lucide-svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import Breadcrumb from '$lib/components/ui/Breadcrumb.svelte';

	interface Integration {
		id: string;
		name: string;
		description: string;
		category: string;
		icon: string;
		connected: boolean;
		lastSync?: Date;
		features: string[];
	}

	let integrations: Integration[] = [
		{
			id: 'interactive-brokers',
			name: 'Interactive Brokers',
			description: 'Connect your IBKR account for automatic trade imports and real-time data',
			category: 'Broker',
			icon: '🏦',
			connected: true,
			lastSync: new Date('2024-01-22T10:30:00'),
			features: ['Auto Import', 'Real-time Data', 'Portfolio Sync']
		},
		{
			id: 'td-ameritrade',
			name: 'TD Ameritrade',
			description: 'Sync your TDA/ThinkorSwim trades and portfolio data',
			category: 'Broker',
			icon: '📈',
			connected: false,
			features: ['Trade Import', 'Position Tracking', 'Options Data']
		},
		{
			id: 'tradingview',
			name: 'TradingView',
			description: 'Import alerts and sync your watchlists with TradingView',
			category: 'Analysis',
			icon: '📊',
			connected: false,
			features: ['Alert Import', 'Watchlist Sync', 'Chart Integration']
		},
		{
			id: 'discord',
			name: 'Discord',
			description: 'Send trade alerts and performance updates to Discord',
			category: 'Notifications',
			icon: '💬',
			connected: true,
			lastSync: new Date('2024-01-22T09:00:00'),
			features: ['Trade Alerts', 'Daily Summary', 'Custom Webhooks']
		},
		{
			id: 'google-sheets',
			name: 'Google Sheets',
			description: 'Export your trading data to Google Sheets for custom analysis',
			category: 'Export',
			icon: '📑',
			connected: false,
			features: ['Auto Export', 'Real-time Sync', 'Custom Templates']
		}
	];

	let activeCategory = 'all';
	let connecting = '';

	$: filteredIntegrations = integrations.filter(integration => 
		activeCategory === 'all' || integration.category.toLowerCase() === activeCategory
	);

	$: categories = ['all', ...new Set(integrations.map(i => i.category.toLowerCase()))];

	async function toggleConnection(integration: Integration) {
		connecting = integration.id;
		// Simulate API call
		await new Promise(resolve => setTimeout(resolve, 1500));
		
		const index = integrations.findIndex(i => i.id === integration.id);
		integrations[index].connected = !integrations[index].connected;
		if (integrations[index].connected) {
			integrations[index].lastSync = new Date();
		}
		integrations = integrations;
		connecting = '';
	}

	function formatLastSync(date?: Date) {
		if (!date) return 'Never';
		const now = new Date();
		const diff = now.getTime() - date.getTime();
		const minutes = Math.floor(diff / 60000);
		
		if (minutes < 1) return 'Just now';
		if (minutes < 60) return `${minutes} minutes ago`;
		const hours = Math.floor(minutes / 60);
		if (hours < 24) return `${hours} hours ago`;
		return date.toLocaleDateString();
	}
</script>

<svelte:head>
	<title>Integrations - Settings</title>
	<meta name="description" content="Connect TradeSense with your favorite trading platforms and tools." />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow-sm">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<Breadcrumb />
			<div class="flex items-center gap-3 mt-4">
				<Link class="h-6 w-6 text-gray-600 dark:text-gray-400" />
				<div>
					<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
						Integrations
					</h1>
					<p class="text-gray-600 dark:text-gray-400 mt-1">
						Connect your favorite tools and platforms
					</p>
				</div>
			</div>
		</div>
	</div>

	<!-- Category Filter -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
		<div class="flex gap-2 overflow-x-auto pb-2">
			{#each categories as category}
				<button
					on:click={() => activeCategory = category}
					class="px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-colors
						{activeCategory === category
							? 'bg-blue-600 text-white'
							: 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}"
				>
					{category.charAt(0).toUpperCase() + category.slice(1)}
				</button>
			{/each}
		</div>
	</div>

	<!-- Integrations Grid -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
			{#each filteredIntegrations as integration}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
					<div class="p-6">
						<div class="flex items-start justify-between mb-4">
							<div class="flex items-center gap-3">
								<span class="text-3xl">{integration.icon}</span>
								<div>
									<h3 class="font-semibold text-gray-900 dark:text-white">
										{integration.name}
									</h3>
									<span class="text-xs text-gray-500 dark:text-gray-400 uppercase">
										{integration.category}
									</span>
								</div>
							</div>
							{#if integration.connected}
								<span class="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
									<Check class="h-3 w-3" />
									Connected
								</span>
							{/if}
						</div>

						<p class="text-gray-600 dark:text-gray-400 text-sm mb-4">
							{integration.description}
						</p>

						<div class="space-y-2 mb-4">
							{#each integration.features as feature}
								<div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
									<Check class="h-3 w-3 text-green-500" />
									{feature}
								</div>
							{/each}
						</div>

						{#if integration.connected && integration.lastSync}
							<p class="text-xs text-gray-500 dark:text-gray-400 mb-4">
								Last synced: {formatLastSync(integration.lastSync)}
							</p>
						{/if}

						<div class="flex gap-3">
							<button
								on:click={() => toggleConnection(integration)}
								disabled={connecting === integration.id}
								class="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors
									{integration.connected
										? 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
										: 'bg-blue-600 text-white hover:bg-blue-700'}"
							>
								{#if connecting === integration.id}
									<Loader2 class="h-4 w-4 animate-spin" />
									{integration.connected ? 'Disconnecting...' : 'Connecting...'}
								{:else}
									{integration.connected ? 'Disconnect' : 'Connect'}
								{/if}
							</button>
							{#if integration.connected}
								<button
									class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
								>
									<Settings2 class="h-5 w-5" />
								</button>
							{/if}
						</div>
					</div>
				</div>
			{/each}
		</div>

		<!-- Help Section -->
		<div class="mt-12 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
			<div class="flex items-start gap-4">
				<AlertCircle class="h-6 w-6 text-blue-600 dark:text-blue-400 shrink-0" />
				<div>
					<h3 class="font-semibold text-gray-900 dark:text-white mb-2">
						Need help with integrations?
					</h3>
					<p class="text-gray-600 dark:text-gray-400 mb-4">
						Our integrations are designed to be secure and easy to set up. All connections use 
						industry-standard OAuth2 authentication and data is encrypted in transit.
					</p>
					<div class="flex flex-wrap gap-4">
						<a
							href="/docs/integrations"
							class="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline"
						>
							View Integration Docs
							<ExternalLink class="h-4 w-4" />
						</a>
						<a
							href="/support"
							class="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline"
						>
							Contact Support
							<ExternalLink class="h-4 w-4" />
						</a>
					</div>
				</div>
			</div>
		</div>

		<!-- Security Note -->
		<div class="mt-6 flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
			<Shield class="h-4 w-4" />
			<p>
				All integrations use secure OAuth2 authentication. We never store your passwords.
			</p>
		</div>
	</div>
</div>