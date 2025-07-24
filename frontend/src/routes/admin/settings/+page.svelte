<script lang="ts">
	import { 
		Settings, Shield, Bell, Database, Mail, 
		Globe, Zap, Save, AlertCircle, CheckCircle
	} from 'lucide-svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	let loading = false;
	let saveSuccess = false;
	let activeTab = 'general';

	// Settings state
	let settings = {
		general: {
			siteName: 'TradeSense',
			siteUrl: 'https://tradesense.com',
			contactEmail: 'support@tradesense.com',
			timezone: 'America/New_York',
			maintenanceMode: false
		},
		security: {
			requireMfa: false,
			passwordMinLength: 8,
			sessionTimeout: 30,
			maxLoginAttempts: 5,
			ipWhitelist: ''
		},
		email: {
			smtpHost: 'smtp.sendgrid.net',
			smtpPort: 587,
			smtpUser: 'apikey',
			smtpPassword: '••••••••••••',
			fromEmail: 'noreply@tradesense.com',
			fromName: 'TradeSense'
		},
		api: {
			rateLimit: 1000,
			rateLimitWindow: 3600,
			maxUploadSize: 10,
			enableWebhooks: true,
			corsOrigins: 'https://app.tradesense.com'
		},
		features: {
			enableSignups: true,
			enableGuestAccess: false,
			enableApiAccess: true,
			enableExport: true,
			enableAiInsights: true
		},
		integrations: {
			enableInteractiveBrokers: true,
			enableThinkorSwim: true,
			enableMetatrader: true,
			enableTradingview: false,
			googleAnalyticsId: '',
			sentryDsn: ''
		}
	};

	const tabs = [
		{ id: 'general', label: 'General', icon: Settings },
		{ id: 'security', label: 'Security', icon: Shield },
		{ id: 'email', label: 'Email', icon: Mail },
		{ id: 'api', label: 'API', icon: Zap },
		{ id: 'features', label: 'Features', icon: Globe },
		{ id: 'integrations', label: 'Integrations', icon: Database }
	];

	async function saveSettings() {
		loading = true;
		// Simulate API call
		await new Promise(resolve => setTimeout(resolve, 1000));
		loading = false;
		saveSuccess = true;
		setTimeout(() => saveSuccess = false, 3000);
	}
</script>

<svelte:head>
	<title>System Settings - Admin Dashboard</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow-sm">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
						System Settings
					</h1>
					<p class="text-gray-600 dark:text-gray-400 mt-1">
						Configure platform-wide settings and features
					</p>
				</div>
				<button
					on:click={saveSettings}
					disabled={loading}
					class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
				>
					{#if loading}
						<LoadingSpinner size="sm" color="white" />
					{:else}
						<Save class="h-4 w-4" />
					{/if}
					Save Changes
				</button>
			</div>
		</div>
	</div>

	<!-- Success Message -->
	{#if saveSuccess}
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
			<div class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 flex items-center gap-3">
				<CheckCircle class="h-5 w-5 text-green-600 dark:text-green-400" />
				<p class="text-green-700 dark:text-green-400">Settings saved successfully!</p>
			</div>
		</div>
	{/if}

	<!-- Content -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<div class="lg:grid lg:grid-cols-4 lg:gap-8">
			<!-- Sidebar Navigation -->
			<nav class="mb-8 lg:mb-0">
				<ul class="space-y-1">
					{#each tabs as tab}
						<li>
							<button
								on:click={() => activeTab = tab.id}
								class="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors
									{activeTab === tab.id 
										? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' 
										: 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}"
							>
								<svelte:component this={tab.icon} class="h-5 w-5" />
								{tab.label}
							</button>
						</li>
					{/each}
				</ul>
			</nav>

			<!-- Settings Forms -->
			<div class="lg:col-span-3">
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
					{#if activeTab === 'general'}
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
							General Settings
						</h2>
						<div class="space-y-6">
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Site Name
								</label>
								<input
									type="text"
									bind:value={settings.general.siteName}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Site URL
								</label>
								<input
									type="url"
									bind:value={settings.general.siteUrl}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Contact Email
								</label>
								<input
									type="email"
									bind:value={settings.general.contactEmail}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Default Timezone
								</label>
								<select
									bind:value={settings.general.timezone}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								>
									<option value="America/New_York">Eastern Time</option>
									<option value="America/Chicago">Central Time</option>
									<option value="America/Denver">Mountain Time</option>
									<option value="America/Los_Angeles">Pacific Time</option>
									<option value="UTC">UTC</option>
								</select>
							</div>
							
							<div class="flex items-center gap-3">
								<input
									type="checkbox"
									id="maintenance"
									bind:checked={settings.general.maintenanceMode}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
								<label for="maintenance" class="text-sm text-gray-700 dark:text-gray-300">
									Enable Maintenance Mode
								</label>
							</div>
						</div>
					{:else if activeTab === 'security'}
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
							Security Settings
						</h2>
						<div class="space-y-6">
							<div class="flex items-center gap-3">
								<input
									type="checkbox"
									id="mfa"
									bind:checked={settings.security.requireMfa}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
								<label for="mfa" class="text-sm text-gray-700 dark:text-gray-300">
									Require MFA for all users
								</label>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Minimum Password Length
								</label>
								<input
									type="number"
									min="6"
									max="32"
									bind:value={settings.security.passwordMinLength}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Session Timeout (minutes)
								</label>
								<input
									type="number"
									min="5"
									max="1440"
									bind:value={settings.security.sessionTimeout}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Max Login Attempts
								</label>
								<input
									type="number"
									min="3"
									max="10"
									bind:value={settings.security.maxLoginAttempts}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									IP Whitelist (one per line)
								</label>
								<textarea
									bind:value={settings.security.ipWhitelist}
									rows="4"
									placeholder="Leave empty to allow all IPs"
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
						</div>
					{:else if activeTab === 'email'}
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
							Email Settings
						</h2>
						<div class="space-y-6">
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									SMTP Host
								</label>
								<input
									type="text"
									bind:value={settings.email.smtpHost}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									SMTP Port
								</label>
								<input
									type="number"
									bind:value={settings.email.smtpPort}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									SMTP Username
								</label>
								<input
									type="text"
									bind:value={settings.email.smtpUser}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									SMTP Password
								</label>
								<input
									type="password"
									bind:value={settings.email.smtpPassword}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									From Email
								</label>
								<input
									type="email"
									bind:value={settings.email.fromEmail}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									From Name
								</label>
								<input
									type="text"
									bind:value={settings.email.fromName}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
						</div>
					{:else if activeTab === 'api'}
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
							API Settings
						</h2>
						<div class="space-y-6">
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Rate Limit (requests per hour)
								</label>
								<input
									type="number"
									bind:value={settings.api.rateLimit}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Max Upload Size (MB)
								</label>
								<input
									type="number"
									bind:value={settings.api.maxUploadSize}
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
							
							<div class="flex items-center gap-3">
								<input
									type="checkbox"
									id="webhooks"
									bind:checked={settings.api.enableWebhooks}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
								<label for="webhooks" class="text-sm text-gray-700 dark:text-gray-300">
									Enable Webhooks
								</label>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									CORS Origins (comma separated)
								</label>
								<input
									type="text"
									bind:value={settings.api.corsOrigins}
									placeholder="https://app.example.com, https://www.example.com"
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
						</div>
					{:else if activeTab === 'features'}
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
							Feature Flags
						</h2>
						<div class="space-y-4">
							<div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
								<div>
									<p class="font-medium text-gray-900 dark:text-white">Enable Signups</p>
									<p class="text-sm text-gray-600 dark:text-gray-400">Allow new users to register</p>
								</div>
								<input
									type="checkbox"
									bind:checked={settings.features.enableSignups}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</div>
							
							<div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
								<div>
									<p class="font-medium text-gray-900 dark:text-white">Guest Access</p>
									<p class="text-sm text-gray-600 dark:text-gray-400">Allow limited access without account</p>
								</div>
								<input
									type="checkbox"
									bind:checked={settings.features.enableGuestAccess}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</div>
							
							<div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
								<div>
									<p class="font-medium text-gray-900 dark:text-white">API Access</p>
									<p class="text-sm text-gray-600 dark:text-gray-400">Enable API for third-party integrations</p>
								</div>
								<input
									type="checkbox"
									bind:checked={settings.features.enableApiAccess}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</div>
							
							<div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
								<div>
									<p class="font-medium text-gray-900 dark:text-white">Data Export</p>
									<p class="text-sm text-gray-600 dark:text-gray-400">Allow users to export their data</p>
								</div>
								<input
									type="checkbox"
									bind:checked={settings.features.enableExport}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</div>
							
							<div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
								<div>
									<p class="font-medium text-gray-900 dark:text-white">AI Insights</p>
									<p class="text-sm text-gray-600 dark:text-gray-400">Enable AI-powered trading insights</p>
								</div>
								<input
									type="checkbox"
									bind:checked={settings.features.enableAiInsights}
									class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
								/>
							</div>
						</div>
					{:else if activeTab === 'integrations'}
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
							Integrations
						</h2>
						<div class="space-y-6">
							<h3 class="text-sm font-medium text-gray-900 dark:text-white">Broker Integrations</h3>
							<div class="space-y-3 pl-4">
								<div class="flex items-center gap-3">
									<input
										type="checkbox"
										id="ib"
										bind:checked={settings.integrations.enableInteractiveBrokers}
										class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
									/>
									<label for="ib" class="text-sm text-gray-700 dark:text-gray-300">
										Interactive Brokers
									</label>
								</div>
								
								<div class="flex items-center gap-3">
									<input
										type="checkbox"
										id="tos"
										bind:checked={settings.integrations.enableThinkorSwim}
										class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
									/>
									<label for="tos" class="text-sm text-gray-700 dark:text-gray-300">
										TD Ameritrade ThinkorSwim
									</label>
								</div>
								
								<div class="flex items-center gap-3">
									<input
										type="checkbox"
										id="mt"
										bind:checked={settings.integrations.enableMetatrader}
										class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
									/>
									<label for="mt" class="text-sm text-gray-700 dark:text-gray-300">
										MetaTrader 4/5
									</label>
								</div>
								
								<div class="flex items-center gap-3">
									<input
										type="checkbox"
										id="tv"
										bind:checked={settings.integrations.enableTradingview}
										class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
									/>
									<label for="tv" class="text-sm text-gray-700 dark:text-gray-300">
										TradingView
									</label>
								</div>
							</div>
							
							<div class="pt-4">
								<h3 class="text-sm font-medium text-gray-900 dark:text-white mb-4">Analytics</h3>
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
										Google Analytics ID
									</label>
									<input
										type="text"
										bind:value={settings.integrations.googleAnalyticsId}
										placeholder="UA-XXXXXXXXX-X"
										class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
									/>
								</div>
							</div>
							
							<div>
								<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Sentry DSN
								</label>
								<input
									type="text"
									bind:value={settings.integrations.sentryDsn}
									placeholder="https://xxx@sentry.io/xxx"
									class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
								/>
							</div>
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>
</div>