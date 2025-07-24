<script lang="ts">
	import { onMount } from 'svelte';
	import { CheckCircle, XCircle, AlertCircle, Activity, Clock, TrendingUp } from 'lucide-svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	interface ServiceStatus {
		name: string;
		status: 'operational' | 'degraded' | 'down';
		responseTime: number;
		uptime: number;
		lastChecked: Date;
	}

	interface Incident {
		id: string;
		title: string;
		status: 'resolved' | 'monitoring' | 'investigating';
		severity: 'minor' | 'major' | 'critical';
		startTime: Date;
		endTime?: Date;
		updates: Array<{
			time: Date;
			message: string;
		}>;
	}

	let services: ServiceStatus[] = [];
	let incidents: Incident[] = [];
	let overallStatus: 'operational' | 'degraded' | 'down' = 'operational';
	let loading = true;
	let lastUpdate = new Date();

	const serviceList = [
		'Web Application',
		'API',
		'Database',
		'Authentication',
		'Analytics Engine',
		'File Storage',
		'Email Service',
		'WebSocket'
	];

	onMount(() => {
		loadStatus();
		const interval = setInterval(loadStatus, 30000); // Refresh every 30 seconds
		
		return () => clearInterval(interval);
	});

	async function loadStatus() {
		try {
			// In production, this would fetch from /api/status
			// For now, we'll simulate the data
			services = serviceList.map(name => ({
				name,
				status: Math.random() > 0.95 ? 'degraded' : 'operational',
				responseTime: Math.floor(Math.random() * 100) + 20,
				uptime: 99.5 + Math.random() * 0.49,
				lastChecked: new Date()
			}));

			// Check if any service is degraded/down
			const hasIssues = services.some(s => s.status !== 'operational');
			overallStatus = hasIssues ? 'degraded' : 'operational';

			// Simulate incidents
			incidents = [
				{
					id: '1',
					title: 'Scheduled Maintenance Window',
					status: 'resolved',
					severity: 'minor',
					startTime: new Date(Date.now() - 86400000),
					endTime: new Date(Date.now() - 82800000),
					updates: [
						{
							time: new Date(Date.now() - 82800000),
							message: 'Maintenance completed successfully.'
						},
						{
							time: new Date(Date.now() - 86400000),
							message: 'Starting scheduled maintenance.'
						}
					]
				}
			];

			lastUpdate = new Date();
		} catch (error) {
			console.error('Failed to load status:', error);
		} finally {
			loading = false;
		}
	}

	function getStatusIcon(status: string) {
		switch (status) {
			case 'operational':
				return CheckCircle;
			case 'degraded':
				return AlertCircle;
			case 'down':
				return XCircle;
			default:
				return AlertCircle;
		}
	}

	function getStatusColor(status: string) {
		switch (status) {
			case 'operational':
				return 'text-green-600 dark:text-green-400';
			case 'degraded':
				return 'text-yellow-600 dark:text-yellow-400';
			case 'down':
				return 'text-red-600 dark:text-red-400';
			default:
				return 'text-gray-600 dark:text-gray-400';
		}
	}

	function formatUptime(uptime: number) {
		return uptime.toFixed(2) + '%';
	}

	function formatResponseTime(time: number) {
		return time + 'ms';
	}
</script>

<svelte:head>
	<title>System Status - TradeSense</title>
	<meta name="description" content="Check the current operational status of TradeSense services and view incident history." />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Hero Section -->
	<section class="pt-20 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-gray-50 dark:from-gray-800 dark:to-gray-900">
		<div class="max-w-7xl mx-auto">
			<div class="text-center mb-12">
				<h1 class="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
					System Status
				</h1>
				<p class="text-xl text-gray-600 dark:text-gray-400">
					Current operational status of TradeSense services
				</p>
			</div>

			{#if loading}
				<div class="flex justify-center">
					<LoadingSpinner size="lg" />
				</div>
			{:else}
				<!-- Overall Status -->
				<div class="max-w-2xl mx-auto mb-8">
					<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6 border border-gray-200 dark:border-gray-700">
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-3">
								<svelte:component 
									this={getStatusIcon(overallStatus)} 
									class="h-8 w-8 {getStatusColor(overallStatus)}" 
								/>
								<div>
									<h2 class="text-2xl font-semibold text-gray-900 dark:text-white">
										{#if overallStatus === 'operational'}
											All Systems Operational
										{:else if overallStatus === 'degraded'}
											Partial Service Disruption
										{:else}
											Major Service Outage
										{/if}
									</h2>
									<p class="text-sm text-gray-600 dark:text-gray-400">
										Last updated: {lastUpdate.toLocaleTimeString()}
									</p>
								</div>
							</div>
							<button
								on:click={loadStatus}
								class="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
								title="Refresh status"
							>
								<Activity class="h-5 w-5" />
							</button>
						</div>
					</div>
				</div>
			{/if}
		</div>
	</section>

	{#if !loading}
		<!-- Service Status -->
		<section class="py-16 px-4 sm:px-6 lg:px-8">
			<div class="max-w-7xl mx-auto">
				<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-8">
					Service Status
				</h2>
				
				<div class="grid gap-4">
					{#each services as service}
						<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
							<div class="flex items-center justify-between">
								<div class="flex items-center gap-3">
									<svelte:component 
										this={getStatusIcon(service.status)} 
										class="h-6 w-6 {getStatusColor(service.status)}" 
									/>
									<h3 class="text-lg font-medium text-gray-900 dark:text-white">
										{service.name}
									</h3>
								</div>
								
								<div class="flex items-center gap-6 text-sm">
									<div class="text-right">
										<p class="text-gray-500 dark:text-gray-400">Response Time</p>
										<p class="font-medium text-gray-900 dark:text-white">
											{formatResponseTime(service.responseTime)}
										</p>
									</div>
									<div class="text-right">
										<p class="text-gray-500 dark:text-gray-400">Uptime (30d)</p>
										<p class="font-medium text-gray-900 dark:text-white">
											{formatUptime(service.uptime)}
										</p>
									</div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		</section>

		<!-- Recent Incidents -->
		<section class="py-16 px-4 sm:px-6 lg:px-8 bg-white dark:bg-gray-800">
			<div class="max-w-7xl mx-auto">
				<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-8">
					Recent Incidents
				</h2>
				
				{#if incidents.length === 0}
					<div class="text-center py-12">
						<CheckCircle class="h-12 w-12 text-green-600 dark:text-green-400 mx-auto mb-4" />
						<p class="text-gray-600 dark:text-gray-400">
							No recent incidents. All systems have been running smoothly.
						</p>
					</div>
				{:else}
					<div class="space-y-6">
						{#each incidents as incident}
							<div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
								<div class="flex items-start justify-between mb-4">
									<div>
										<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
											{incident.title}
										</h3>
										<div class="flex items-center gap-3 text-sm">
											<span class="px-2 py-1 rounded-full text-xs font-medium
												{incident.status === 'resolved' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : ''}
												{incident.status === 'monitoring' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' : ''}
												{incident.status === 'investigating' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' : ''}
											">
												{incident.status}
											</span>
											<span class="text-gray-500 dark:text-gray-400">
												Started: {incident.startTime.toLocaleString()}
											</span>
											{#if incident.endTime}
												<span class="text-gray-500 dark:text-gray-400">
													Duration: {Math.round((incident.endTime.getTime() - incident.startTime.getTime()) / 60000)} minutes
												</span>
											{/if}
										</div>
									</div>
								</div>
								
								<div class="space-y-3">
									{#each incident.updates as update}
										<div class="flex gap-3 text-sm">
											<Clock class="h-4 w-4 text-gray-400 shrink-0 mt-0.5" />
											<div>
												<p class="text-gray-500 dark:text-gray-400">
													{update.time.toLocaleString()}
												</p>
												<p class="text-gray-700 dark:text-gray-300">
													{update.message}
												</p>
											</div>
										</div>
									{/each}
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</section>

		<!-- Uptime Stats -->
		<section class="py-16 px-4 sm:px-6 lg:px-8">
			<div class="max-w-7xl mx-auto">
				<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-8 text-center">
					Uptime Statistics
				</h2>
				
				<div class="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
					<div class="text-center">
						<div class="flex items-center justify-center mb-2">
							<TrendingUp class="h-8 w-8 text-green-600 dark:text-green-400" />
						</div>
						<p class="text-3xl font-bold text-gray-900 dark:text-white mb-1">99.95%</p>
						<p class="text-gray-600 dark:text-gray-400">Last 90 days</p>
					</div>
					
					<div class="text-center">
						<div class="flex items-center justify-center mb-2">
							<Clock class="h-8 w-8 text-blue-600 dark:text-blue-400" />
						</div>
						<p class="text-3xl font-bold text-gray-900 dark:text-white mb-1">45ms</p>
						<p class="text-gray-600 dark:text-gray-400">Avg Response Time</p>
					</div>
					
					<div class="text-center">
						<div class="flex items-center justify-center mb-2">
							<Activity class="h-8 w-8 text-purple-600 dark:text-purple-400" />
						</div>
						<p class="text-3xl font-bold text-gray-900 dark:text-white mb-1">0</p>
						<p class="text-gray-600 dark:text-gray-400">Incidents This Month</p>
					</div>
				</div>
			</div>
		</section>
	{/if}

	<!-- Subscribe Section -->
	<section class="py-16 px-4 sm:px-6 lg:px-8 bg-blue-50 dark:bg-blue-900/20">
		<div class="max-w-4xl mx-auto text-center">
			<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
				Get Status Updates
			</h2>
			<p class="text-gray-600 dark:text-gray-400 mb-6">
				Subscribe to receive notifications about scheduled maintenance and service disruptions.
			</p>
			
			<form class="max-w-md mx-auto flex gap-3">
				<input
					type="email"
					placeholder="your@email.com"
					class="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				/>
				<button
					type="submit"
					class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
				>
					Subscribe
				</button>
			</form>
		</div>
	</section>
</div>