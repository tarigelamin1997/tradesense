<script lang="ts">
	import { 
		Key, Plus, Copy, Eye, EyeOff, Trash2, 
		AlertCircle, Shield, Calendar, Activity
	} from 'lucide-svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	interface ApiKey {
		id: string;
		name: string;
		key: string;
		lastUsed: Date | null;
		created: Date;
		permissions: string[];
		requestCount: number;
	}

	let apiKeys: ApiKey[] = [
		{
			id: '1',
			name: 'Production API',
			key: 'sk_live_...abc123',
			lastUsed: new Date('2024-01-22T10:00:00'),
			created: new Date('2024-01-01'),
			permissions: ['read:trades', 'write:trades', 'read:analytics'],
			requestCount: 1234
		},
		{
			id: '2',
			name: 'Testing Key',
			key: 'sk_test_...xyz789',
			lastUsed: null,
			created: new Date('2024-01-15'),
			permissions: ['read:trades'],
			requestCount: 0
		}
	];

	let showCreateModal = false;
	let showDeleteModal = false;
	let selectedKey: ApiKey | null = null;
	let showKey: Record<string, boolean> = {};
	let loading = false;
	let copied = '';

	// New key form
	let newKeyName = '';
	let newKeyPermissions = {
		'read:trades': true,
		'write:trades': false,
		'read:analytics': true,
		'write:analytics': false,
		'read:settings': false,
		'write:settings': false
	};

	function copyToClipboard(key: string, id: string) {
		navigator.clipboard.writeText(key);
		copied = id;
		setTimeout(() => copied = '', 2000);
	}

	async function createApiKey() {
		if (!newKeyName.trim()) return;
		
		loading = true;
		// Simulate API call
		await new Promise(resolve => setTimeout(resolve, 1000));
		
		const permissions = Object.entries(newKeyPermissions)
			.filter(([_, enabled]) => enabled)
			.map(([permission]) => permission);
		
		apiKeys = [...apiKeys, {
			id: Date.now().toString(),
			name: newKeyName,
			key: `sk_live_${Math.random().toString(36).substring(2, 15)}`,
			lastUsed: null,
			created: new Date(),
			permissions,
			requestCount: 0
		}];
		
		loading = false;
		showCreateModal = false;
		newKeyName = '';
		// Reset permissions
		Object.keys(newKeyPermissions).forEach(key => {
			newKeyPermissions[key] = key.includes('read');
		});
	}

	async function deleteApiKey() {
		if (!selectedKey) return;
		
		loading = true;
		await new Promise(resolve => setTimeout(resolve, 1000));
		
		apiKeys = apiKeys.filter(key => key.id !== selectedKey.id);
		loading = false;
		showDeleteModal = false;
		selectedKey = null;
	}

	function formatDate(date: Date | null) {
		if (!date) return 'Never';
		return date.toLocaleDateString();
	}

	function maskKey(key: string) {
		return key.substring(0, 10) + '...' + key.substring(key.length - 4);
	}
</script>

<svelte:head>
	<title>API Keys - Settings</title>
	<meta name="description" content="Manage your TradeSense API keys for third-party integrations." />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow-sm">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-3">
					<Key class="h-6 w-6 text-gray-600 dark:text-gray-400" />
					<div>
						<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
							API Keys
						</h1>
						<p class="text-gray-600 dark:text-gray-400 mt-1">
							Manage access to your TradeSense data via API
						</p>
					</div>
				</div>
				<button
					on:click={() => showCreateModal = true}
					class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
				>
					<Plus class="h-5 w-5" />
					Create New Key
				</button>
			</div>
		</div>
	</div>

	<!-- API Keys List -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		{#if apiKeys.length === 0}
			<div class="bg-white dark:bg-gray-800 rounded-lg p-12 text-center">
				<Key class="h-12 w-12 text-gray-400 mx-auto mb-4" />
				<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
					No API keys yet
				</h3>
				<p class="text-gray-600 dark:text-gray-400 mb-6">
					Create your first API key to start integrating with TradeSense.
				</p>
				<button
					on:click={() => showCreateModal = true}
					class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
				>
					<Plus class="h-5 w-5" />
					Create Your First Key
				</button>
			</div>
		{:else}
			<div class="space-y-4">
				{#each apiKeys as apiKey}
					<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
						<div class="flex items-start justify-between mb-4">
							<div>
								<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
									{apiKey.name}
								</h3>
								<div class="flex items-center gap-4 mt-2 text-sm text-gray-600 dark:text-gray-400">
									<span class="flex items-center gap-1">
										<Calendar class="h-4 w-4" />
										Created {formatDate(apiKey.created)}
									</span>
									<span class="flex items-center gap-1">
										<Activity class="h-4 w-4" />
										{apiKey.requestCount} requests
									</span>
									<span>
										Last used: {formatDate(apiKey.lastUsed)}
									</span>
								</div>
							</div>
							<button
								on:click={() => {
									selectedKey = apiKey;
									showDeleteModal = true;
								}}
								class="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
							>
								<Trash2 class="h-5 w-5" />
							</button>
						</div>

						<!-- API Key Display -->
						<div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 mb-4">
							<div class="flex items-center justify-between">
								<code class="font-mono text-sm text-gray-900 dark:text-white">
									{showKey[apiKey.id] ? apiKey.key : maskKey(apiKey.key)}
								</code>
								<div class="flex items-center gap-2">
									<button
										on:click={() => showKey[apiKey.id] = !showKey[apiKey.id]}
										class="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
									>
										{#if showKey[apiKey.id]}
											<EyeOff class="h-4 w-4" />
										{:else}
											<Eye class="h-4 w-4" />
										{/if}
									</button>
									<button
										on:click={() => copyToClipboard(apiKey.key, apiKey.id)}
										class="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
									>
										{#if copied === apiKey.id}
											<Check class="h-4 w-4 text-green-600" />
										{:else}
											<Copy class="h-4 w-4" />
										{/if}
									</button>
								</div>
							</div>
						</div>

						<!-- Permissions -->
						<div>
							<p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								Permissions:
							</p>
							<div class="flex flex-wrap gap-2">
								{#each apiKey.permissions as permission}
									<span class="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded-md">
										{permission}
									</span>
								{/each}
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}

		<!-- Documentation Section -->
		<div class="mt-8 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
			<h3 class="font-semibold text-gray-900 dark:text-white mb-3">
				Getting Started with the API
			</h3>
			<p class="text-gray-600 dark:text-gray-400 mb-4">
				Use your API keys to integrate TradeSense with your applications and workflows.
			</p>
			<div class="space-y-3">
				<div class="font-mono text-sm bg-gray-100 dark:bg-gray-800 p-3 rounded">
					<p class="text-gray-500 dark:text-gray-400 mb-1"># Example API request</p>
					<p class="text-gray-900 dark:text-white">curl -H "Authorization: Bearer YOUR_API_KEY" \</p>
					<p class="text-gray-900 dark:text-white ml-4">https://api.tradesense.com/v1/trades</p>
				</div>
				<a
					href="/docs/api"
					class="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline"
				>
					View API Documentation →
				</a>
			</div>
		</div>

		<!-- Security Note -->
		<div class="mt-6 flex items-start gap-3 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
			<Shield class="h-5 w-5 text-yellow-600 dark:text-yellow-400 shrink-0 mt-0.5" />
			<div class="text-sm text-yellow-800 dark:text-yellow-200">
				<p class="font-medium mb-1">Keep your API keys secure</p>
				<p>Never share your API keys publicly or commit them to version control. Treat them like passwords.</p>
			</div>
		</div>
	</div>

	<!-- Create Modal -->
	{#if showCreateModal}
		<div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
			<div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
				<h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
					Create New API Key
				</h2>
				
				<div class="space-y-4">
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Key Name
						</label>
						<input
							type="text"
							bind:value={newKeyName}
							placeholder="e.g., Production API"
							class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
						/>
					</div>

					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Permissions
						</label>
						<div class="space-y-2">
							{#each Object.entries(newKeyPermissions) as [permission, enabled]}
								<label class="flex items-center gap-3">
									<input
										type="checkbox"
										bind:checked={newKeyPermissions[permission]}
										class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
									/>
									<span class="text-gray-700 dark:text-gray-300">{permission}</span>
								</label>
							{/each}
						</div>
					</div>
				</div>

				<div class="flex gap-3 mt-6">
					<button
						on:click={() => showCreateModal = false}
						class="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
					>
						Cancel
					</button>
					<button
						on:click={createApiKey}
						disabled={loading || !newKeyName.trim()}
						class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{#if loading}
							<LoadingSpinner size="sm" color="white" />
						{:else}
							Create Key
						{/if}
					</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- Delete Confirmation Modal -->
	{#if showDeleteModal && selectedKey}
		<div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
			<div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
				<div class="flex items-center gap-3 mb-4">
					<div class="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
						<AlertCircle class="h-6 w-6 text-red-600 dark:text-red-400" />
					</div>
					<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
						Delete API Key
					</h2>
				</div>
				
				<p class="text-gray-600 dark:text-gray-400 mb-6">
					Are you sure you want to delete <strong>{selectedKey.name}</strong>? 
					This action cannot be undone and any applications using this key will stop working.
				</p>

				<div class="flex gap-3">
					<button
						on:click={() => showDeleteModal = false}
						class="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
					>
						Cancel
					</button>
					<button
						on:click={deleteApiKey}
						disabled={loading}
						class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
					>
						{#if loading}
							<LoadingSpinner size="sm" color="white" />
						{:else}
							Delete Key
						{/if}
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>