<script lang="ts">
	import { 
		TrendingUp, Users, DollarSign, Activity,
		BarChart3, PieChart, Calendar, Download
	} from 'lucide-svelte';
	import { onMount } from 'svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
	import SkeletonLoader from '$lib/components/ui/SkeletonLoader.svelte';

	let loading = true;
	let dateRange = '7d';

	// Mock data - in production this would come from API
	let analytics = {
		users: {
			total: 10234,
			active: 3456,
			new: 234,
			growth: 12.5
		},
		revenue: {
			total: 125430,
			mrr: 45600,
			growth: 8.3,
			churn: 2.1
		},
		trades: {
			total: 5234567,
			today: 12345,
			avgPerUser: 512
		},
		engagement: {
			dau: 2345,
			mau: 8765,
			avgSessionTime: '12m 34s',
			retention: 78.5
		}
	};

	onMount(() => {
		// Simulate loading
		setTimeout(() => {
			loading = false;
		}, 1000);
	});

	const kpiCards = [
		{
			title: 'Total Users',
			value: analytics.users.total.toLocaleString(),
			change: `+${analytics.users.growth}%`,
			icon: Users,
			color: 'blue'
		},
		{
			title: 'Monthly Revenue',
			value: `$${analytics.revenue.mrr.toLocaleString()}`,
			change: `+${analytics.revenue.growth}%`,
			icon: DollarSign,
			color: 'green'
		},
		{
			title: 'Total Trades',
			value: analytics.trades.total.toLocaleString(),
			change: `+${analytics.trades.today.toLocaleString()} today`,
			icon: Activity,
			color: 'purple'
		},
		{
			title: 'User Retention',
			value: `${analytics.engagement.retention}%`,
			change: 'Last 30 days',
			icon: TrendingUp,
			color: 'orange'
		}
	];

	function exportData() {
		// In production, this would trigger a CSV/Excel export
		console.log('Exporting analytics data...');
	}
</script>

<svelte:head>
	<title>Analytics - Admin Dashboard</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow-sm">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
						Platform Analytics
					</h1>
					<p class="text-gray-600 dark:text-gray-400 mt-1">
						Monitor platform performance and user metrics
					</p>
				</div>
				<div class="flex items-center gap-4">
					<select
						bind:value={dateRange}
						class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
					>
						<option value="24h">Last 24 hours</option>
						<option value="7d">Last 7 days</option>
						<option value="30d">Last 30 days</option>
						<option value="90d">Last 90 days</option>
					</select>
					<button
						on:click={exportData}
						class="flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
					>
						<Download class="h-4 w-4" />
						Export
					</button>
				</div>
			</div>
		</div>
	</div>

	<!-- Content -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		{#if loading}
			<!-- Loading State -->
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
				{#each Array(4) as _}
					<SkeletonLoader type="card" height="140px" />
				{/each}
			</div>
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
				<SkeletonLoader type="chart" height="400px" />
				<SkeletonLoader type="chart" height="400px" />
			</div>
		{:else}
			<!-- KPI Cards -->
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
				{#each kpiCards as kpi}
					<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
						<div class="flex items-center justify-between mb-4">
							<div class="p-2 bg-{kpi.color}-100 dark:bg-{kpi.color}-900/30 rounded-lg">
								<svelte:component this={kpi.icon} class="h-6 w-6 text-{kpi.color}-600 dark:text-{kpi.color}-400" />
							</div>
							<span class="text-sm text-green-600 dark:text-green-400">
								{kpi.change}
							</span>
						</div>
						<h3 class="text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">
							{kpi.title}
						</h3>
						<p class="text-2xl font-bold text-gray-900 dark:text-white">
							{kpi.value}
						</p>
					</div>
				{/each}
			</div>

			<!-- Charts -->
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
				<!-- User Growth Chart -->
				<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
					<div class="flex items-center justify-between mb-6">
						<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
							User Growth
						</h3>
						<BarChart3 class="h-5 w-5 text-gray-400" />
					</div>
					<div class="h-64 flex items-center justify-center text-gray-400">
						<!-- Chart would go here -->
						<p>User growth chart</p>
					</div>
				</div>

				<!-- Revenue Chart -->
				<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
					<div class="flex items-center justify-between mb-6">
						<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
							Revenue Trends
						</h3>
						<TrendingUp class="h-5 w-5 text-gray-400" />
					</div>
					<div class="h-64 flex items-center justify-center text-gray-400">
						<!-- Chart would go here -->
						<p>Revenue chart</p>
					</div>
				</div>
			</div>

			<!-- Additional Metrics -->
			<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
				<!-- User Distribution -->
				<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
						User Distribution
					</h3>
					<div class="space-y-3">
						<div class="flex items-center justify-between">
							<span class="text-gray-600 dark:text-gray-400">Free Users</span>
							<span class="font-medium text-gray-900 dark:text-white">4,234</span>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-gray-600 dark:text-gray-400">Starter</span>
							<span class="font-medium text-gray-900 dark:text-white">3,456</span>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-gray-600 dark:text-gray-400">Professional</span>
							<span class="font-medium text-gray-900 dark:text-white">2,123</span>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-gray-600 dark:text-gray-400">Enterprise</span>
							<span class="font-medium text-gray-900 dark:text-white">421</span>
						</div>
					</div>
				</div>

				<!-- Top Features -->
				<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
						Most Used Features
					</h3>
					<div class="space-y-3">
						<div>
							<div class="flex items-center justify-between mb-1">
								<span class="text-gray-600 dark:text-gray-400">Trade Import</span>
								<span class="text-sm text-gray-500">89%</span>
							</div>
							<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
								<div class="bg-blue-600 h-2 rounded-full" style="width: 89%"></div>
							</div>
						</div>
						<div>
							<div class="flex items-center justify-between mb-1">
								<span class="text-gray-600 dark:text-gray-400">Analytics</span>
								<span class="text-sm text-gray-500">76%</span>
							</div>
							<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
								<div class="bg-blue-600 h-2 rounded-full" style="width: 76%"></div>
							</div>
						</div>
						<div>
							<div class="flex items-center justify-between mb-1">
								<span class="text-gray-600 dark:text-gray-400">AI Insights</span>
								<span class="text-sm text-gray-500">62%</span>
							</div>
							<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
								<div class="bg-blue-600 h-2 rounded-full" style="width: 62%"></div>
							</div>
						</div>
					</div>
				</div>

				<!-- Recent Activity -->
				<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
						Platform Activity
					</h3>
					<div class="space-y-3">
						<div class="flex items-center justify-between">
							<span class="text-gray-600 dark:text-gray-400">Active Now</span>
							<span class="font-medium text-green-600 dark:text-green-400">234 users</span>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-gray-600 dark:text-gray-400">Trades Today</span>
							<span class="font-medium text-gray-900 dark:text-white">12,345</span>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-gray-600 dark:text-gray-400">New Signups</span>
							<span class="font-medium text-gray-900 dark:text-white">45</span>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-gray-600 dark:text-gray-400">Support Tickets</span>
							<span class="font-medium text-gray-900 dark:text-white">8 open</span>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>