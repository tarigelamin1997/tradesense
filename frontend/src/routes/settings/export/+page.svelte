<script lang="ts">
	import { 
		Download, FileSpreadsheet, FileText, Calendar,
		Filter, Clock, CheckCircle, AlertCircle
	} from 'lucide-svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	let exportType = 'trades';
	let format = 'csv';
	let dateRange = 'all';
	let customStartDate = '';
	let customEndDate = '';
	let includeOptions = {
		trades: true,
		analytics: true,
		notes: true,
		tags: true,
		performance: true
	};
	
	let exporting = false;
	let exportHistory = [
		{
			id: '1',
			type: 'Full Export',
			format: 'CSV',
			date: new Date('2024-01-20T10:00:00'),
			size: '2.4 MB',
			status: 'completed'
		},
		{
			id: '2',
			type: 'Trades Only',
			format: 'Excel',
			date: new Date('2024-01-15T14:30:00'),
			size: '1.1 MB',
			status: 'completed'
		},
		{
			id: '3',
			type: 'Tax Report',
			format: 'PDF',
			date: new Date('2024-01-01T09:00:00'),
			size: '342 KB',
			status: 'completed'
		}
	];

	const exportTypes = [
		{ value: 'trades', label: 'Trade History', icon: FileSpreadsheet },
		{ value: 'performance', label: 'Performance Report', icon: FileText },
		{ value: 'tax', label: 'Tax Report', icon: FileText },
		{ value: 'full', label: 'Full Account Export', icon: Download }
	];

	const formats = [
		{ value: 'csv', label: 'CSV', description: 'Compatible with Excel, Google Sheets' },
		{ value: 'excel', label: 'Excel', description: 'Native Excel format with formatting' },
		{ value: 'pdf', label: 'PDF', description: 'Formatted report for printing' },
		{ value: 'json', label: 'JSON', description: 'For developers and APIs' }
	];

	const dateRanges = [
		{ value: 'all', label: 'All Time' },
		{ value: 'ytd', label: 'Year to Date' },
		{ value: 'last_year', label: 'Last Year' },
		{ value: 'last_quarter', label: 'Last Quarter' },
		{ value: 'last_month', label: 'Last Month' },
		{ value: 'custom', label: 'Custom Range' }
	];

	async function startExport() {
		exporting = true;
		// Simulate export process
		await new Promise(resolve => setTimeout(resolve, 2000));
		
		// Add to history
		exportHistory = [
			{
				id: Date.now().toString(),
				type: exportTypes.find(t => t.value === exportType)?.label || 'Export',
				format: format.toUpperCase(),
				date: new Date(),
				size: '1.8 MB',
				status: 'completed'
			},
			...exportHistory
		];
		
		exporting = false;
		// In production, this would trigger a download
	}

	function downloadExport(exportItem: any) {
		// In production, this would download the actual file
		console.log('Downloading:', exportItem);
	}

	function formatDate(date: Date) {
		return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
	}
</script>

<svelte:head>
	<title>Export Data - Settings</title>
	<meta name="description" content="Export your TradeSense trading data in various formats." />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow-sm">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex items-center gap-3">
				<Download class="h-6 w-6 text-gray-600 dark:text-gray-400" />
				<div>
					<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
						Export Data
					</h1>
					<p class="text-gray-600 dark:text-gray-400 mt-1">
						Download your trading data and reports
					</p>
				</div>
			</div>
		</div>
	</div>

	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
			<!-- Export Configuration -->
			<div class="lg:col-span-2 space-y-6">
				<!-- Export Type -->
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
						What to Export
					</h2>
					<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
						{#each exportTypes as type}
							<label class="flex items-center gap-3 p-4 rounded-lg border cursor-pointer transition-colors
								{exportType === type.value 
									? 'bg-blue-50 dark:bg-blue-900/30 border-blue-600' 
									: 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 hover:border-blue-600'}"
							>
								<input
									type="radio"
									bind:group={exportType}
									value={type.value}
									class="sr-only"
								/>
								<svelte:component this={type.icon} class="h-5 w-5 text-gray-600 dark:text-gray-400" />
								<span class="font-medium text-gray-900 dark:text-white">{type.label}</span>
							</label>
						{/each}
					</div>
				</div>

				<!-- Format Selection -->
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
						Export Format
					</h2>
					<div class="space-y-3">
						{#each formats as fmt}
							<label class="flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors
								{format === fmt.value 
									? 'bg-blue-50 dark:bg-blue-900/30 border-blue-600' 
									: 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 hover:border-blue-600'}"
							>
								<input
									type="radio"
									bind:group={format}
									value={fmt.value}
									class="mt-1"
								/>
								<div>
									<p class="font-medium text-gray-900 dark:text-white">{fmt.label}</p>
									<p class="text-sm text-gray-600 dark:text-gray-400">{fmt.description}</p>
								</div>
							</label>
						{/each}
					</div>
				</div>

				<!-- Date Range -->
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
						Date Range
					</h2>
					<div class="space-y-4">
						<select
							bind:value={dateRange}
							class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
						>
							{#each dateRanges as range}
								<option value={range.value}>{range.label}</option>
							{/each}
						</select>

						{#if dateRange === 'custom'}
							<div class="grid grid-cols-2 gap-4">
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
										Start Date
									</label>
									<input
										type="date"
										bind:value={customStartDate}
										class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
									/>
								</div>
								<div>
									<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
										End Date
									</label>
									<input
										type="date"
										bind:value={customEndDate}
										class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
									/>
								</div>
							</div>
						{/if}
					</div>
				</div>

				<!-- Include Options -->
				{#if exportType === 'trades' || exportType === 'full'}
					<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
							Include in Export
						</h2>
						<div class="space-y-3">
							{#each Object.entries(includeOptions) as [option, enabled]}
								<label class="flex items-center gap-3">
									<input
										type="checkbox"
										bind:checked={includeOptions[option]}
										class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
									/>
									<span class="text-gray-700 dark:text-gray-300 capitalize">
										{option.replace('_', ' ')}
									</span>
								</label>
							{/each}
						</div>
					</div>
				{/if}

				<!-- Export Button -->
				<button
					on:click={startExport}
					disabled={exporting}
					class="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
				>
					{#if exporting}
						<div class="flex items-center justify-center gap-2">
							<LoadingSpinner size="sm" color="white" />
							Preparing Export...
						</div>
					{:else}
						<div class="flex items-center justify-center gap-2">
							<Download class="h-5 w-5" />
							Start Export
						</div>
					{/if}
				</button>
			</div>

			<!-- Export History -->
			<div class="lg:col-span-1">
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
						Recent Exports
					</h2>
					{#if exportHistory.length === 0}
						<p class="text-gray-600 dark:text-gray-400 text-center py-8">
							No exports yet
						</p>
					{:else}
						<div class="space-y-3">
							{#each exportHistory as item}
								<div class="p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
									<div class="flex items-start justify-between mb-2">
										<div>
											<p class="font-medium text-gray-900 dark:text-white">
												{item.type}
											</p>
											<p class="text-xs text-gray-500 dark:text-gray-400">
												{item.format} • {item.size}
											</p>
										</div>
										{#if item.status === 'completed'}
											<CheckCircle class="h-4 w-4 text-green-600 dark:text-green-400" />
										{:else}
											<Clock class="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
										{/if}
									</div>
									<p class="text-xs text-gray-500 dark:text-gray-400 mb-2">
										{formatDate(item.date)}
									</p>
									<button
										on:click={() => downloadExport(item)}
										class="text-sm text-blue-600 dark:text-blue-400 hover:underline"
									>
										Download Again
									</button>
								</div>
							{/each}
						</div>
					{/if}
				</div>

				<!-- Help Section -->
				<div class="mt-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
					<div class="flex items-start gap-3">
						<AlertCircle class="h-5 w-5 text-blue-600 dark:text-blue-400 shrink-0" />
						<div class="text-sm">
							<p class="font-medium text-blue-900 dark:text-blue-200 mb-1">
								Export Tips
							</p>
							<ul class="text-blue-800 dark:text-blue-300 space-y-1">
								<li>• CSV format works with most spreadsheet apps</li>
								<li>• PDF exports include charts and formatting</li>
								<li>• Tax reports follow IRS Form 8949 format</li>
								<li>• Large exports may take a few minutes</li>
							</ul>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>