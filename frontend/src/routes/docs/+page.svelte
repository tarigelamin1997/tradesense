<script lang="ts">
	import { 
		BookOpen, Video, Code, FileText, 
		Rocket, BarChart3, Upload, Settings,
		Search, ChevronRight
	} from 'lucide-svelte';

	let searchQuery = '';

	const quickStart = [
		{
			icon: Rocket,
			title: 'Getting Started',
			description: 'Learn the basics of TradeSense and set up your account',
			link: '/docs/getting-started'
		},
		{
			icon: Upload,
			title: 'Import Your Trades',
			description: 'Import trades from your broker or trading platform',
			link: '/docs/importing-trades'
		},
		{
			icon: BarChart3,
			title: 'Analyze Performance',
			description: 'Understand your trading metrics and analytics',
			link: '/docs/analytics'
		},
		{
			icon: Settings,
			title: 'Customize Settings',
			description: 'Configure TradeSense to match your trading style',
			link: '/docs/settings'
		}
	];

	const categories = [
		{
			title: 'Platform Basics',
			icon: BookOpen,
			articles: [
				{ title: 'Account Setup', link: '/docs/account-setup' },
				{ title: 'Dashboard Overview', link: '/docs/dashboard' },
				{ title: 'Navigation Guide', link: '/docs/navigation' },
				{ title: 'Keyboard Shortcuts', link: '/docs/shortcuts' }
			]
		},
		{
			title: 'Trade Management',
			icon: FileText,
			articles: [
				{ title: 'Adding Trades Manually', link: '/docs/manual-trades' },
				{ title: 'Bulk Import', link: '/docs/bulk-import' },
				{ title: 'Trade Types & Categories', link: '/docs/trade-types' },
				{ title: 'Tags & Organization', link: '/docs/tags' }
			]
		},
		{
			title: 'Analytics & Reports',
			icon: BarChart3,
			articles: [
				{ title: 'Performance Metrics', link: '/docs/metrics' },
				{ title: 'Custom Reports', link: '/docs/custom-reports' },
				{ title: 'Exporting Data', link: '/docs/export' },
				{ title: 'AI Insights', link: '/docs/ai-insights' }
			]
		},
		{
			title: 'API & Integrations',
			icon: Code,
			articles: [
				{ title: 'API Overview', link: '/docs/api' },
				{ title: 'Authentication', link: '/docs/api-auth' },
				{ title: 'Webhooks', link: '/docs/webhooks' },
				{ title: 'Broker Integrations', link: '/docs/integrations' }
			]
		}
	];

	const resources = [
		{
			icon: Video,
			title: 'Video Tutorials',
			description: 'Step-by-step video guides',
			link: '/docs/videos'
		},
		{
			icon: Code,
			title: 'API Reference',
			description: 'Complete API documentation',
			link: '/docs/api-reference'
		},
		{
			icon: FileText,
			title: 'Release Notes',
			description: 'Latest updates and changes',
			link: '/changelog'
		}
	];

	$: filteredCategories = searchQuery
		? categories.map(cat => ({
				...cat,
				articles: cat.articles.filter(article =>
					article.title.toLowerCase().includes(searchQuery.toLowerCase())
				)
			})).filter(cat => cat.articles.length > 0)
		: categories;
</script>

<svelte:head>
	<title>Documentation - TradeSense</title>
	<meta name="description" content="Complete documentation for TradeSense trading analytics platform. Learn how to import trades, analyze performance, and use our API." />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Hero Section -->
	<section class="pt-20 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-gray-50 dark:from-gray-800 dark:to-gray-900">
		<div class="max-w-7xl mx-auto text-center">
			<h1 class="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6">
				Documentation
			</h1>
			<p class="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto mb-8">
				Everything you need to know about using TradeSense to track, analyze, and improve your trading performance.
			</p>

			<!-- Search Bar -->
			<div class="max-w-xl mx-auto">
				<div class="relative">
					<input
						type="text"
						bind:value={searchQuery}
						placeholder="Search documentation..."
						class="w-full px-4 py-3 pl-12 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
					/>
					<Search class="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
				</div>
			</div>
		</div>
	</section>

	<!-- Quick Start -->
	<section class="py-16 px-4 sm:px-6 lg:px-8">
		<div class="max-w-7xl mx-auto">
			<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-8">
				Quick Start Guides
			</h2>
			
			<div class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
				{#each quickStart as guide}
					<a
						href={guide.link}
						class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-200 dark:border-gray-700"
					>
						<div class="flex items-start gap-4">
							<div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg shrink-0">
								<svelte:component this={guide.icon} class="h-6 w-6 text-blue-600 dark:text-blue-400" />
							</div>
							<div>
								<h3 class="font-semibold text-gray-900 dark:text-white mb-1">
									{guide.title}
								</h3>
								<p class="text-sm text-gray-600 dark:text-gray-400">
									{guide.description}
								</p>
							</div>
						</div>
					</a>
				{/each}
			</div>
		</div>
	</section>

	<!-- Documentation Categories -->
	<section class="py-16 px-4 sm:px-6 lg:px-8 bg-white dark:bg-gray-800">
		<div class="max-w-7xl mx-auto">
			<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-8">
				Browse by Category
			</h2>
			
			<div class="grid lg:grid-cols-2 gap-8">
				{#each filteredCategories as category}
					<div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
						<div class="flex items-center gap-3 mb-4">
							<div class="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
								<svelte:component this={category.icon} class="h-6 w-6 text-gray-700 dark:text-gray-300" />
							</div>
							<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
								{category.title}
							</h3>
						</div>
						
						<ul class="space-y-2">
							{#each category.articles as article}
								<li>
									<a
										href={article.link}
										class="flex items-center justify-between p-2 rounded hover:bg-white dark:hover:bg-gray-800 transition-colors group"
									>
										<span class="text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400">
											{article.title}
										</span>
										<ChevronRight class="h-4 w-4 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400" />
									</a>
								</li>
							{/each}
						</ul>
					</div>
				{/each}
			</div>

			{#if searchQuery && filteredCategories.length === 0}
				<div class="text-center py-12">
					<p class="text-gray-600 dark:text-gray-400">
						No results found for "{searchQuery}". Try a different search term.
					</p>
				</div>
			{/if}
		</div>
	</section>

	<!-- Additional Resources -->
	<section class="py-16 px-4 sm:px-6 lg:px-8">
		<div class="max-w-7xl mx-auto">
			<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-8">
				Additional Resources
			</h2>
			
			<div class="grid md:grid-cols-3 gap-6">
				{#each resources as resource}
					<a
						href={resource.link}
						class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow border border-gray-200 dark:border-gray-700"
					>
						<div class="flex items-start gap-4">
							<div class="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg shrink-0">
								<svelte:component this={resource.icon} class="h-6 w-6 text-gray-700 dark:text-gray-300" />
							</div>
							<div>
								<h3 class="font-semibold text-gray-900 dark:text-white mb-1">
									{resource.title}
								</h3>
								<p class="text-sm text-gray-600 dark:text-gray-400">
									{resource.description}
								</p>
							</div>
						</div>
					</a>
				{/each}
			</div>
		</div>
	</section>

	<!-- Help Section -->
	<section class="py-16 px-4 sm:px-6 lg:px-8 bg-blue-50 dark:bg-blue-900/20">
		<div class="max-w-4xl mx-auto text-center">
			<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
				Can't find what you're looking for?
			</h2>
			<p class="text-gray-600 dark:text-gray-400 mb-6">
				Our support team is here to help you get the most out of TradeSense.
			</p>
			
			<div class="flex flex-wrap justify-center gap-4">
				<a
					href="/contact"
					class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
				>
					Contact Support
				</a>
				<a
					href="/support/kb"
					class="px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium border border-gray-300 dark:border-gray-600"
				>
					Browse FAQs
				</a>
			</div>
		</div>
	</section>
</div>