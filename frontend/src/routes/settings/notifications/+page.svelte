<script lang="ts">
	import { 
		Bell, Mail, MessageSquare, Smartphone, Monitor,
		Volume2, Zap, TrendingUp, AlertCircle, Check
	} from 'lucide-svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	let saving = false;
	let saved = false;

	// Notification preferences
	let preferences = {
		email: {
			enabled: true,
			trades: true,
			performance: true,
			insights: false,
			system: true,
			frequency: 'realtime'
		},
		push: {
			enabled: true,
			trades: true,
			performance: false,
			insights: true,
			system: true
		},
		sms: {
			enabled: false,
			trades: false,
			alerts: false,
			phoneNumber: ''
		},
		desktop: {
			enabled: true,
			sound: true,
			trades: true,
			alerts: true
		},
		trading: {
			priceAlerts: true,
			stopLoss: true,
			takeProfit: true,
			largePositions: true,
			threshold: 1000
		}
	};

	// Notification channels info
	const channels = [
		{
			id: 'email',
			name: 'Email Notifications',
			description: 'Receive updates via email',
			icon: Mail,
			color: 'blue'
		},
		{
			id: 'push',
			name: 'Push Notifications',
			description: 'Mobile app notifications',
			icon: Smartphone,
			color: 'green'
		},
		{
			id: 'sms',
			name: 'SMS Alerts',
			description: 'Critical alerts via text',
			icon: MessageSquare,
			color: 'purple'
		},
		{
			id: 'desktop',
			name: 'Desktop Notifications',
			description: 'Browser notifications',
			icon: Monitor,
			color: 'orange'
		}
	];

	async function savePreferences() {
		saving = true;
		// Simulate API call
		await new Promise(resolve => setTimeout(resolve, 1000));
		saving = false;
		saved = true;
		setTimeout(() => saved = false, 3000);
	}

	async function testNotification(channel: string) {
		// Simulate sending test notification
		if (channel === 'desktop' && 'Notification' in window) {
			if (Notification.permission === 'granted') {
				new Notification('TradeSense Test', {
					body: 'Desktop notifications are working!',
					icon: '/favicon.png'
				});
			} else if (Notification.permission !== 'denied') {
				const permission = await Notification.requestPermission();
				if (permission === 'granted') {
					new Notification('TradeSense Test', {
						body: 'Desktop notifications are now enabled!',
						icon: '/favicon.png'
					});
				}
			}
		}
	}
</script>

<svelte:head>
	<title>Notifications - Settings</title>
	<meta name="description" content="Manage your TradeSense notification preferences." />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow-sm">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-3">
					<Bell class="h-6 w-6 text-gray-600 dark:text-gray-400" />
					<div>
						<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
							Notifications
						</h1>
						<p class="text-gray-600 dark:text-gray-400 mt-1">
							Control how and when you receive updates
						</p>
					</div>
				</div>
				<button
					on:click={savePreferences}
					disabled={saving}
					class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
				>
					{#if saving}
						<LoadingSpinner size="sm" color="white" />
						Saving...
					{:else if saved}
						<Check class="h-5 w-5" />
						Saved
					{:else}
						Save Changes
					{/if}
				</button>
			</div>
		</div>
	</div>

	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Notification Channels -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
			{#each channels as channel}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
					<div class="flex items-start justify-between mb-4">
						<div class="flex items-center gap-3">
							<div class="p-2 bg-{channel.color}-100 dark:bg-{channel.color}-900/30 rounded-lg">
								<svelte:component this={channel.icon} class="h-6 w-6 text-{channel.color}-600 dark:text-{channel.color}-400" />
							</div>
							<div>
								<h3 class="font-semibold text-gray-900 dark:text-white">
									{channel.name}
								</h3>
								<p class="text-sm text-gray-600 dark:text-gray-400">
									{channel.description}
								</p>
							</div>
						</div>
						<label class="relative inline-flex items-center cursor-pointer">
							<input
								type="checkbox"
								bind:checked={preferences[channel.id].enabled}
								class="sr-only peer"
							/>
							<div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
						</label>
					</div>

					{#if channel.id === 'email'}
						<div class="space-y-3 pt-2">
							<label class="flex items-center justify-between">
								<span class="text-sm text-gray-700 dark:text-gray-300">Trade confirmations</span>
								<input
									type="checkbox"
									bind:checked={preferences.email.trades}
									disabled={!preferences.email.enabled}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</label>
							<label class="flex items-center justify-between">
								<span class="text-sm text-gray-700 dark:text-gray-300">Daily performance</span>
								<input
									type="checkbox"
									bind:checked={preferences.email.performance}
									disabled={!preferences.email.enabled}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</label>
							<label class="flex items-center justify-between">
								<span class="text-sm text-gray-700 dark:text-gray-300">AI insights</span>
								<input
									type="checkbox"
									bind:checked={preferences.email.insights}
									disabled={!preferences.email.enabled}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</label>
							<div class="pt-2">
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Email frequency
								</label>
								<select
									bind:value={preferences.email.frequency}
									disabled={!preferences.email.enabled}
									class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"
								>
									<option value="realtime">Real-time</option>
									<option value="hourly">Hourly digest</option>
									<option value="daily">Daily digest</option>
									<option value="weekly">Weekly summary</option>
								</select>
							</div>
						</div>
					{/if}

					{#if channel.id === 'push'}
						<div class="space-y-3 pt-2">
							<label class="flex items-center justify-between">
								<span class="text-sm text-gray-700 dark:text-gray-300">Trade updates</span>
								<input
									type="checkbox"
									bind:checked={preferences.push.trades}
									disabled={!preferences.push.enabled}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</label>
							<label class="flex items-center justify-between">
								<span class="text-sm text-gray-700 dark:text-gray-300">Performance milestones</span>
								<input
									type="checkbox"
									bind:checked={preferences.push.performance}
									disabled={!preferences.push.enabled}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</label>
							<label class="flex items-center justify-between">
								<span class="text-sm text-gray-700 dark:text-gray-300">AI insights</span>
								<input
									type="checkbox"
									bind:checked={preferences.push.insights}
									disabled={!preferences.push.enabled}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</label>
						</div>
					{/if}

					{#if channel.id === 'sms'}
						<div class="space-y-3 pt-2">
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Phone number
								</label>
								<input
									type="tel"
									bind:value={preferences.sms.phoneNumber}
									disabled={!preferences.sms.enabled}
									placeholder="+1 (555) 123-4567"
									class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"
								/>
							</div>
							<label class="flex items-center justify-between">
								<span class="text-sm text-gray-700 dark:text-gray-300">Critical trade alerts</span>
								<input
									type="checkbox"
									bind:checked={preferences.sms.trades}
									disabled={!preferences.sms.enabled}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</label>
							<label class="flex items-center justify-between">
								<span class="text-sm text-gray-700 dark:text-gray-300">Risk alerts</span>
								<input
									type="checkbox"
									bind:checked={preferences.sms.alerts}
									disabled={!preferences.sms.enabled}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</label>
						</div>
					{/if}

					{#if channel.id === 'desktop'}
						<div class="space-y-3 pt-2">
							<label class="flex items-center justify-between">
								<span class="text-sm text-gray-700 dark:text-gray-300">Play sound</span>
								<input
									type="checkbox"
									bind:checked={preferences.desktop.sound}
									disabled={!preferences.desktop.enabled}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</label>
							<label class="flex items-center justify-between">
								<span class="text-sm text-gray-700 dark:text-gray-300">Trade confirmations</span>
								<input
									type="checkbox"
									bind:checked={preferences.desktop.trades}
									disabled={!preferences.desktop.enabled}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</label>
							<label class="flex items-center justify-between">
								<span class="text-sm text-gray-700 dark:text-gray-300">Price alerts</span>
								<input
									type="checkbox"
									bind:checked={preferences.desktop.alerts}
									disabled={!preferences.desktop.enabled}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</label>
							<button
								on:click={() => testNotification('desktop')}
								disabled={!preferences.desktop.enabled}
								class="w-full px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
							>
								Test Desktop Notification
							</button>
						</div>
					{/if}
				</div>
			{/each}
		</div>

		<!-- Trading Alerts -->
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 mb-8">
			<div class="flex items-center gap-3 mb-6">
				<div class="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
					<TrendingUp class="h-6 w-6 text-red-600 dark:text-red-400" />
				</div>
				<div>
					<h3 class="font-semibold text-gray-900 dark:text-white">
						Trading Alerts
					</h3>
					<p class="text-sm text-gray-600 dark:text-gray-400">
						Get notified about important trading events
					</p>
				</div>
			</div>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
				<div class="space-y-4">
					<label class="flex items-center justify-between">
						<div>
							<span class="text-sm font-medium text-gray-700 dark:text-gray-300">Price alerts</span>
							<p class="text-xs text-gray-500 dark:text-gray-400">When price targets are reached</p>
						</div>
						<input
							type="checkbox"
							bind:checked={preferences.trading.priceAlerts}
							class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
						/>
					</label>
					<label class="flex items-center justify-between">
						<div>
							<span class="text-sm font-medium text-gray-700 dark:text-gray-300">Stop loss triggers</span>
							<p class="text-xs text-gray-500 dark:text-gray-400">When stop losses are hit</p>
						</div>
						<input
							type="checkbox"
							bind:checked={preferences.trading.stopLoss}
							class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
						/>
					</label>
					<label class="flex items-center justify-between">
						<div>
							<span class="text-sm font-medium text-gray-700 dark:text-gray-300">Take profit alerts</span>
							<p class="text-xs text-gray-500 dark:text-gray-400">When profit targets are reached</p>
						</div>
						<input
							type="checkbox"
							bind:checked={preferences.trading.takeProfit}
							class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
						/>
					</label>
				</div>

				<div class="space-y-4">
					<label class="flex items-center justify-between">
						<div>
							<span class="text-sm font-medium text-gray-700 dark:text-gray-300">Large position alerts</span>
							<p class="text-xs text-gray-500 dark:text-gray-400">Notify for positions above threshold</p>
						</div>
						<input
							type="checkbox"
							bind:checked={preferences.trading.largePositions}
							class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
						/>
					</label>
					{#if preferences.trading.largePositions}
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								Position size threshold ($)
							</label>
							<input
								type="number"
								bind:value={preferences.trading.threshold}
								min="100"
								step="100"
								class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"
							/>
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- Quiet Hours -->
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
			<div class="flex items-center gap-3 mb-6">
				<div class="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
					<Volume2 class="h-6 w-6 text-purple-600 dark:text-purple-400" />
				</div>
				<div>
					<h3 class="font-semibold text-gray-900 dark:text-white">
						Quiet Hours
					</h3>
					<p class="text-sm text-gray-600 dark:text-gray-400">
						Pause non-critical notifications during specific times
					</p>
				</div>
			</div>

			<div class="flex items-center gap-4">
				<input
					type="time"
					value="22:00"
					class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"
				/>
				<span class="text-gray-600 dark:text-gray-400">to</span>
				<input
					type="time"
					value="07:00"
					class="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white text-sm"
				/>
			</div>
		</div>
	</div>
</div>