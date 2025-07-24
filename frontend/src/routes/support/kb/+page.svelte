<script lang="ts">
	import { 
		Search, BookOpen, FileText, ChevronRight,
		TrendingUp, BarChart3, Shield, Zap, Users, Settings
	} from 'lucide-svelte';

	let searchQuery = '';
	let selectedCategory = 'all';

	const categories = [
		{ id: 'all', name: 'All Articles', count: 69 },
		{ id: 'getting-started', name: 'Getting Started', count: 12, icon: BookOpen },
		{ id: 'analytics', name: 'Analytics & Reports', count: 18, icon: BarChart3 },
		{ id: 'trades', name: 'Trade Management', count: 15, icon: TrendingUp },
		{ id: 'security', name: 'Account & Security', count: 8, icon: Shield },
		{ id: 'integrations', name: 'Integrations', count: 10, icon: Zap },
		{ id: 'teams', name: 'Team Features', count: 6, icon: Users }
	];

	const articles = [
		// Getting Started
		{
			id: '1',
			title: 'Getting Started with TradeSense',
			excerpt: 'Learn how to set up your account and start tracking your trades.',
			category: 'getting-started',
			readTime: '5 min',
			popular: true
		},
		{
			id: '2',
			title: 'Your First Trade Import',
			excerpt: 'Step-by-step guide to importing your trading history.',
			category: 'getting-started',
			readTime: '3 min'
		},
		{
			id: '3',
			title: 'Dashboard Overview',
			excerpt: 'Understanding your trading dashboard and key metrics.',
			category: 'getting-started',
			readTime: '4 min',
			popular: true
		},
		// Analytics
		{
			id: '4',
			title: 'Understanding Win Rate and Profit Factor',
			excerpt: 'Deep dive into the most important trading metrics.',
			category: 'analytics',
			readTime: '7 min',
			popular: true
		},
		{
			id: '5',
			title: 'Custom Report Creation',
			excerpt: 'How to create and customize your trading reports.',
			category: 'analytics',
			readTime: '6 min'
		},
		{
			id: '6',
			title: 'AI Insights Explained',
			excerpt: 'How our AI analyzes your trades and provides recommendations.',
			category: 'analytics',
			readTime: '5 min'
		},
		// Trade Management
		{
			id: '7',
			title: 'Manual Trade Entry',
			excerpt: 'How to manually add trades to your journal.',
			category: 'trades',
			readTime: '3 min'
		},
		{
			id: '8',
			title: 'Bulk Import from CSV',
			excerpt: 'Import hundreds of trades at once using CSV files.',
			category: 'trades',
			readTime: '4 min',
			popular: true
		},
		{
			id: '9',
			title: 'Trade Tags and Categories',
			excerpt: 'Organize your trades with tags and custom categories.',
			category: 'trades',
			readTime: '3 min'
		},
		// Security
		{
			id: '10',
			title: 'Two-Factor Authentication Setup',
			excerpt: 'Secure your account with 2FA.',
			category: 'security',
			readTime: '3 min',
			popular: true
		},
		{
			id: '11',
			title: 'API Key Management',
			excerpt: 'How to create and manage API keys safely.',
			category: 'security',
			readTime: '4 min'
		},
		{
			id: '12',
			title: 'Data Privacy and Encryption',
			excerpt: 'How we protect your trading data.',
			category: 'security',
			readTime: '5 min'
		},
		// Integrations
		{
			id: '13',
			title: 'Interactive Brokers Integration',
			excerpt: 'Connect your IB account for automatic trade sync.',
			category: 'integrations',
			readTime: '6 min'
		},
		{
			id: '14',
			title: 'ThinkorSwim Import Guide',
			excerpt: 'Import your trades from TD Ameritrade ThinkorSwim.',
			category: 'integrations',
			readTime: '5 min'
		},
		{
			id: '15',
			title: 'MetaTrader 4/5 Integration',
			excerpt: 'Connect MT4 or MT5 for forex trading analysis.',
			category: 'integrations',
			readTime: '7 min'
		}
	];

	$: filteredArticles = articles.filter(article => {
		const matchesSearch = !searchQuery || 
			article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
			article.excerpt.toLowerCase().includes(searchQuery.toLowerCase());
		
		const matchesCategory = selectedCategory === 'all' || article.category === selectedCategory;
		
		return matchesSearch && matchesCategory;
	});

	$: currentCategory = categories.find(c => c.id === selectedCategory);
</script>

<svelte:head>
	<title>Knowledge Base - TradeSense Support</title>
	<meta name="description" content="Browse our comprehensive knowledge base for guides, tutorials, and answers to common questions about TradeSense." />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<section class="pt-20 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-gray-50 dark:from-gray-800 dark:to-gray-900">
		<div class="max-w-7xl mx-auto">
			<div class="text-center mb-8">
				<h1 class="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
					Knowledge Base
				</h1>
				<p class="text-xl text-gray-600 dark:text-gray-400">
					Find answers and learn how to get the most out of TradeSense
				</p>
			</div>

			<!-- Search -->
			<div class="max-w-2xl mx-auto">
				<div class="relative">
					<input
						type="text"
						bind:value={searchQuery}
						placeholder="Search articles..."
						class="w-full px-6 py-3 pl-12 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					/>
					<Search class="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
				</div>
			</div>
		</div>
	</section>

	<div class="py-8 px-4 sm:px-6 lg:px-8">
		<div class="max-w-7xl mx-auto">
			<div class="lg:grid lg:grid-cols-4 lg:gap-8">
				<!-- Sidebar Categories -->
				<aside class="mb-8 lg:mb-0">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
						Categories
					</h2>
					
					<nav class="space-y-1">
						{#each categories as category}
							<button
								on:click={() => selectedCategory = category.id}
								class="w-full flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg transition-colors
									{selectedCategory === category.id 
										? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400' 
										: 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}"
							>
								<div class="flex items-center gap-2">
									{#if category.icon}
										<svelte:component this={category.icon} class="h-4 w-4" />
									{/if}
									<span>{category.name}</span>
								</div>
								<span class="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-full">
									{category.count}
								</span>
							</button>
						{/each}
					</nav>
				</aside>

				<!-- Articles List -->
				<main class="lg:col-span-3">
					<div class="mb-6">
						<h2 class="text-2xl font-bold text-gray-900 dark:text-white">
							{currentCategory?.name || 'All Articles'}
						</h2>
						<p class="text-gray-600 dark:text-gray-400">
							{filteredArticles.length} articles found
						</p>
					</div>

					{#if filteredArticles.length === 0}
						<div class="text-center py-12">
							<FileText class="h-12 w-12 text-gray-400 mx-auto mb-4" />
							<p class="text-gray-600 dark:text-gray-400">
								No articles found matching your search.
							</p>
						</div>
					{:else}
						<div class="space-y-4">
							{#each filteredArticles as article}
								<a
									href="/support/kb/{article.id}/{article.title.toLowerCase().replace(/\s+/g, '-')}"
									class="block bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-200 dark:border-gray-700"
								>
									<div class="flex items-start justify-between">
										<div class="flex-1">
											<div class="flex items-center gap-2 mb-2">
												<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
													{article.title}
												</h3>
												{#if article.popular}
													<span class="px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 text-xs rounded-full">
														Popular
													</span>
												{/if}
											</div>
											<p class="text-gray-600 dark:text-gray-400 mb-3">
												{article.excerpt}
											</p>
											<div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
												<span>{article.readTime} read</span>
												<span>•</span>
												<span class="capitalize">{article.category.replace('-', ' ')}</span>
											</div>
										</div>
										<ChevronRight class="h-5 w-5 text-gray-400 shrink-0 ml-4" />
									</div>
								</a>
							{/each}
						</div>
					{/if}
				</main>
			</div>
		</div>
	</div>

	<!-- Help Section -->
	<section class="py-16 px-4 sm:px-6 lg:px-8 bg-blue-50 dark:bg-blue-900/20">
		<div class="max-w-4xl mx-auto text-center">
			<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
				Can't find what you're looking for?
			</h2>
			<p class="text-gray-600 dark:text-gray-400 mb-6">
				Our support team is ready to help you with any questions.
			</p>
			<div class="flex flex-wrap justify-center gap-4">
				<a
					href="/contact"
					class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
				>
					Contact Support
				</a>
				<a
					href="/support"
					class="px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium border border-gray-300 dark:border-gray-600"
				>
					Back to Support Center
				</a>
			</div>
		</div>
	</section>
</div>