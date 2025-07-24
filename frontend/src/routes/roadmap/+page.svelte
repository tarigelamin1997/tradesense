<script lang="ts">
	import { 
		Map, Rocket, Target, CheckCircle, Circle,
		Clock, Users, MessageSquare, ThumbsUp
	} from 'lucide-svelte';

	interface RoadmapItem {
		id: string;
		title: string;
		description: string;
		status: 'completed' | 'in-progress' | 'planned';
		quarter: string;
		category: string;
		votes: number;
		progress?: number;
	}

	let roadmapItems: RoadmapItem[] = [
		// Q1 2024
		{
			id: '1',
			title: 'AI-Powered Trade Analysis',
			description: 'Machine learning algorithms to analyze your trading patterns and provide personalized insights.',
			status: 'completed',
			quarter: 'Q1 2024',
			category: 'AI & Analytics',
			votes: 234
		},
		{
			id: '2',
			title: 'Multi-Currency Support',
			description: 'Track and analyze trades across multiple currencies with automatic conversion.',
			status: 'completed',
			quarter: 'Q1 2024',
			category: 'Core Features',
			votes: 189
		},
		{
			id: '3',
			title: 'Mobile App Launch',
			description: 'Native iOS and Android apps for tracking trades on the go.',
			status: 'in-progress',
			quarter: 'Q1 2024',
			category: 'Platform',
			votes: 412,
			progress: 75
		},
		// Q2 2024
		{
			id: '4',
			title: 'Options Trading Support',
			description: 'Full support for options trading including Greeks calculation and strategy analysis.',
			status: 'in-progress',
			quarter: 'Q2 2024',
			category: 'Trading Features',
			votes: 356,
			progress: 40
		},
		{
			id: '5',
			title: 'Advanced Backtesting',
			description: 'Test your trading strategies against historical data with detailed performance metrics.',
			status: 'planned',
			quarter: 'Q2 2024',
			category: 'Analytics',
			votes: 278
		},
		{
			id: '6',
			title: 'Social Trading Features',
			description: 'Follow top traders, share strategies, and learn from the community.',
			status: 'planned',
			quarter: 'Q2 2024',
			category: 'Community',
			votes: 167
		},
		// Q3 2024
		{
			id: '7',
			title: 'Automated Trading Rules',
			description: 'Set up automated alerts and actions based on custom trading rules.',
			status: 'planned',
			quarter: 'Q3 2024',
			category: 'Automation',
			votes: 445
		},
		{
			id: '8',
			title: 'Advanced Risk Management',
			description: 'Sophisticated risk analysis tools including VaR, stress testing, and portfolio optimization.',
			status: 'planned',
			quarter: 'Q3 2024',
			category: 'Risk Management',
			votes: 323
		},
		// Q4 2024
		{
			id: '9',
			title: 'Crypto Trading Integration',
			description: 'Connect cryptocurrency exchanges and track crypto trades alongside traditional assets.',
			status: 'planned',
			quarter: 'Q4 2024',
			category: 'Integrations',
			votes: 567
		},
		{
			id: '10',
			title: 'Team Collaboration',
			description: 'Tools for trading teams to collaborate, share insights, and manage permissions.',
			status: 'planned',
			quarter: 'Q4 2024',
			category: 'Enterprise',
			votes: 145
		}
	];

	let selectedQuarter = 'all';
	let selectedCategory = 'all';

	$: quarters = ['all', ...new Set(roadmapItems.map(item => item.quarter))];
	$: categories = ['all', ...new Set(roadmapItems.map(item => item.category))];

	$: filteredItems = roadmapItems.filter(item => {
		const matchesQuarter = selectedQuarter === 'all' || item.quarter === selectedQuarter;
		const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory;
		return matchesQuarter && matchesCategory;
	});

	$: groupedItems = filteredItems.reduce((acc, item) => {
		if (!acc[item.quarter]) {
			acc[item.quarter] = [];
		}
		acc[item.quarter].push(item);
		return acc;
	}, {} as Record<string, RoadmapItem[]>);

	function getStatusIcon(status: string) {
		switch (status) {
			case 'completed': return CheckCircle;
			case 'in-progress': return Clock;
			case 'planned': return Circle;
			default: return Circle;
		}
	}

	function getStatusColor(status: string) {
		switch (status) {
			case 'completed': return 'text-green-600 dark:text-green-400';
			case 'in-progress': return 'text-blue-600 dark:text-blue-400';
			case 'planned': return 'text-gray-400 dark:text-gray-600';
			default: return 'text-gray-400 dark:text-gray-600';
		}
	}

	function voteForItem(id: string) {
		const index = roadmapItems.findIndex(item => item.id === id);
		if (index !== -1) {
			roadmapItems[index].votes++;
			roadmapItems = roadmapItems;
		}
	}
</script>

<svelte:head>
	<title>Roadmap - TradeSense Future</title>
	<meta name="description" content="See what's coming next to TradeSense. Vote on features and track our progress." />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow-sm">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
			<div class="text-center">
				<div class="inline-flex p-3 bg-purple-100 dark:bg-purple-900/30 rounded-full mb-4">
					<Map class="h-8 w-8 text-purple-600 dark:text-purple-400" />
				</div>
				<h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
					Product Roadmap
				</h1>
				<p class="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
					See what we're building next and help shape the future of TradeSense
				</p>
			</div>
		</div>
	</div>

	<!-- Filters -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
		<div class="flex flex-col sm:flex-row gap-4">
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					Quarter
				</label>
				<select
					bind:value={selectedQuarter}
					class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
				>
					{#each quarters as quarter}
						<option value={quarter}>
							{quarter === 'all' ? 'All Quarters' : quarter}
						</option>
					{/each}
				</select>
			</div>
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					Category
				</label>
				<select
					bind:value={selectedCategory}
					class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
				>
					{#each categories as category}
						<option value={category}>
							{category === 'all' ? 'All Categories' : category}
						</option>
					{/each}
				</select>
			</div>
		</div>

		<!-- Legend -->
		<div class="flex flex-wrap gap-6 mt-6">
			<div class="flex items-center gap-2">
				<CheckCircle class="h-5 w-5 text-green-600 dark:text-green-400" />
				<span class="text-sm text-gray-600 dark:text-gray-400">Completed</span>
			</div>
			<div class="flex items-center gap-2">
				<Clock class="h-5 w-5 text-blue-600 dark:text-blue-400" />
				<span class="text-sm text-gray-600 dark:text-gray-400">In Progress</span>
			</div>
			<div class="flex items-center gap-2">
				<Circle class="h-5 w-5 text-gray-400 dark:text-gray-600" />
				<span class="text-sm text-gray-600 dark:text-gray-400">Planned</span>
			</div>
		</div>
	</div>

	<!-- Roadmap Items -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
		{#each Object.entries(groupedItems) as [quarter, items]}
			<div class="mb-8">
				<h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
					<Target class="h-5 w-5" />
					{quarter}
				</h2>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					{#each items as item}
						<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-6">
							<div class="flex items-start justify-between mb-3">
								<div class="flex items-center gap-3">
									<svelte:component 
										this={getStatusIcon(item.status)} 
										class="h-5 w-5 {getStatusColor(item.status)}" 
									/>
									<span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
										{item.category}
									</span>
								</div>
								<button
									on:click={() => voteForItem(item.id)}
									class="flex items-center gap-1 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
								>
									<ThumbsUp class="h-4 w-4" />
									<span class="text-sm">{item.votes}</span>
								</button>
							</div>

							<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
								{item.title}
							</h3>
							<p class="text-gray-600 dark:text-gray-400 mb-4">
								{item.description}
							</p>

							{#if item.status === 'in-progress' && item.progress}
								<div class="mb-3">
									<div class="flex items-center justify-between text-sm mb-1">
										<span class="text-gray-600 dark:text-gray-400">Progress</span>
										<span class="text-gray-900 dark:text-white font-medium">{item.progress}%</span>
									</div>
									<div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
										<div 
											class="bg-blue-600 h-2 rounded-full transition-all"
											style="width: {item.progress}%"
										/>
									</div>
								</div>
							{/if}

							<div class="flex items-center gap-4 text-sm">
								<span class="flex items-center gap-1 {getStatusColor(item.status)}">
									<svelte:component 
										this={getStatusIcon(item.status)} 
										class="h-4 w-4" 
									/>
									{item.status.replace('-', ' ')}
								</span>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/each}
	</div>

	<!-- Feature Request Section -->
	<section class="bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-800 dark:to-purple-800">
		<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
			<div class="inline-flex p-3 bg-white/20 rounded-full mb-4">
				<Rocket class="h-8 w-8 text-white" />
			</div>
			<h2 class="text-3xl font-bold text-white mb-4">
				Have a Feature Request?
			</h2>
			<p class="text-blue-100 mb-8 text-lg">
				We'd love to hear your ideas! Help us build the trading platform you need.
			</p>
			<div class="flex flex-wrap justify-center gap-4">
				<a
					href="/support/feature-request"
					class="px-6 py-3 bg-white text-blue-600 rounded-lg font-medium hover:bg-gray-100 transition-colors"
				>
					Submit Feature Request
				</a>
				<a
					href="/community"
					class="px-6 py-3 bg-transparent text-white border-2 border-white rounded-lg font-medium hover:bg-white/10 transition-colors"
				>
					Join Community Discussion
				</a>
			</div>
		</div>
	</section>

	<!-- Community Feedback -->
	<section class="py-12">
		<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
			<div class="inline-flex p-3 bg-green-100 dark:bg-green-900/30 rounded-full mb-4">
				<Users class="h-8 w-8 text-green-600 dark:text-green-400" />
			</div>
			<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
				Built with Your Feedback
			</h2>
			<p class="text-gray-600 dark:text-gray-400 mb-8">
				Over 2,000 traders have contributed ideas and feedback to shape TradeSense
			</p>
			<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
				<div class="text-center">
					<p class="text-3xl font-bold text-gray-900 dark:text-white mb-2">5,234</p>
					<p class="text-gray-600 dark:text-gray-400">Feature Votes</p>
				</div>
				<div class="text-center">
					<p class="text-3xl font-bold text-gray-900 dark:text-white mb-2">342</p>
					<p class="text-gray-600 dark:text-gray-400">Ideas Submitted</p>
				</div>
				<div class="text-center">
					<p class="text-3xl font-bold text-gray-900 dark:text-white mb-2">89</p>
					<p class="text-gray-600 dark:text-gray-400">Features Shipped</p>
				</div>
			</div>
		</div>
	</section>
</div>