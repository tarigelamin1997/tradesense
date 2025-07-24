<script lang="ts">
	import { 
		BookOpen, Calendar, Clock, User, Tag,
		ArrowRight, Search, Filter
	} from 'lucide-svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	interface BlogPost {
		id: string;
		title: string;
		excerpt: string;
		author: {
			name: string;
			avatar: string;
		};
		publishDate: Date;
		readTime: number;
		category: string;
		tags: string[];
		image: string;
		featured: boolean;
	}

	let posts: BlogPost[] = [
		{
			id: '1',
			title: 'Understanding Risk Management in Day Trading',
			excerpt: 'Learn the fundamental principles of risk management and how to protect your capital while maximizing returns in day trading.',
			author: {
				name: 'Sarah Chen',
				avatar: '👩‍💼'
			},
			publishDate: new Date('2024-01-20'),
			readTime: 8,
			category: 'Education',
			tags: ['risk-management', 'day-trading', 'strategies'],
			image: '📊',
			featured: true
		},
		{
			id: '2',
			title: 'New AI-Powered Analytics Features Released',
			excerpt: 'Discover how our latest AI features can help you identify patterns and improve your trading decisions with machine learning.',
			author: {
				name: 'Mike Johnson',
				avatar: '👨‍💻'
			},
			publishDate: new Date('2024-01-18'),
			readTime: 5,
			category: 'Product Updates',
			tags: ['ai', 'analytics', 'features'],
			image: '🤖',
			featured: true
		},
		{
			id: '3',
			title: 'Market Analysis: Q1 2024 Trading Trends',
			excerpt: 'A comprehensive analysis of trading patterns and market behavior in the first quarter of 2024.',
			author: {
				name: 'Alex Rivera',
				avatar: '🧑‍💼'
			},
			publishDate: new Date('2024-01-15'),
			readTime: 12,
			category: 'Market Analysis',
			tags: ['markets', 'analysis', 'trends'],
			image: '📈',
			featured: false
		},
		{
			id: '4',
			title: 'Building a Winning Trading Psychology',
			excerpt: 'Master the mental game of trading with proven techniques to manage emotions and maintain discipline.',
			author: {
				name: 'Dr. Emily Watson',
				avatar: '👩‍⚕️'
			},
			publishDate: new Date('2024-01-10'),
			readTime: 10,
			category: 'Psychology',
			tags: ['psychology', 'mindset', 'discipline'],
			image: '🧠',
			featured: false
		}
	];

	let searchQuery = '';
	let selectedCategory = 'all';
	let loading = false;

	$: categories = ['all', ...new Set(posts.map(p => p.category))];
	
	$: filteredPosts = posts.filter(post => {
		const matchesSearch = !searchQuery || 
			post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
			post.excerpt.toLowerCase().includes(searchQuery.toLowerCase()) ||
			post.tags.some(tag => tag.includes(searchQuery.toLowerCase()));
		
		const matchesCategory = selectedCategory === 'all' || post.category === selectedCategory;
		
		return matchesSearch && matchesCategory;
	});

	$: featuredPosts = filteredPosts.filter(p => p.featured);
	$: regularPosts = filteredPosts.filter(p => !p.featured);

	function formatDate(date: Date) {
		return date.toLocaleDateString('en-US', { 
			year: 'numeric', 
			month: 'long', 
			day: 'numeric' 
		});
	}
</script>

<svelte:head>
	<title>Blog - TradeSense Insights</title>
	<meta name="description" content="Trading insights, market analysis, and platform updates from the TradeSense team." />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow-sm">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
			<div class="text-center">
				<h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
					TradeSense Blog
				</h1>
				<p class="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
					Trading insights, market analysis, and platform updates to help you trade smarter
				</p>
			</div>
		</div>
	</div>

	<!-- Search and Filters -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
		<div class="flex flex-col md:flex-row gap-4">
			<div class="flex-1 relative">
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search articles..."
					class="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
				/>
				<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
			</div>
			<div class="flex gap-2 overflow-x-auto pb-2">
				{#each categories as category}
					<button
						on:click={() => selectedCategory = category}
						class="px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-colors
							{selectedCategory === category
								? 'bg-blue-600 text-white'
								: 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}"
					>
						{category === 'all' ? 'All Posts' : category}
					</button>
				{/each}
			</div>
		</div>
	</div>

	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
		{#if loading}
			<div class="flex justify-center py-12">
				<LoadingSpinner size="lg" />
			</div>
		{:else if filteredPosts.length === 0}
			<div class="text-center py-12">
				<BookOpen class="h-12 w-12 text-gray-400 mx-auto mb-4" />
				<p class="text-gray-500 dark:text-gray-400">No articles found matching your criteria.</p>
			</div>
		{:else}
			<!-- Featured Posts -->
			{#if featuredPosts.length > 0}
				<div class="mb-12">
					<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">Featured</h2>
					<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
						{#each featuredPosts as post}
							<article class="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden hover:shadow-lg transition-shadow">
								<a href="/blog/{post.id}" class="block">
									<div class="p-6">
										<div class="flex items-center gap-3 mb-4">
											<span class="text-4xl">{post.image}</span>
											<div>
												<span class="inline-block px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs font-medium rounded-full">
													{post.category}
												</span>
											</div>
										</div>
										<h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2 line-clamp-2">
											{post.title}
										</h3>
										<p class="text-gray-600 dark:text-gray-400 mb-4 line-clamp-3">
											{post.excerpt}
										</p>
										<div class="flex items-center justify-between">
											<div class="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
												<span class="flex items-center gap-1">
													<Calendar class="h-4 w-4" />
													{formatDate(post.publishDate)}
												</span>
												<span class="flex items-center gap-1">
													<Clock class="h-4 w-4" />
													{post.readTime} min read
												</span>
											</div>
											<ArrowRight class="h-5 w-5 text-blue-600 dark:text-blue-400" />
										</div>
									</div>
								</a>
							</article>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Regular Posts -->
			{#if regularPosts.length > 0}
				<div>
					<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
						{featuredPosts.length > 0 ? 'Recent Posts' : 'All Posts'}
					</h2>
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
						{#each regularPosts as post}
							<article class="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden hover:shadow-lg transition-shadow">
								<a href="/blog/{post.id}" class="block">
									<div class="p-6">
										<div class="flex items-center justify-between mb-3">
											<span class="text-3xl">{post.image}</span>
											<span class="text-xs text-gray-500 dark:text-gray-400">
												{formatDate(post.publishDate)}
											</span>
										</div>
										<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
											{post.title}
										</h3>
										<p class="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-3">
											{post.excerpt}
										</p>
										<div class="flex items-center justify-between">
											<div class="flex items-center gap-2">
												<span class="text-2xl">{post.author.avatar}</span>
												<div>
													<p class="text-sm font-medium text-gray-900 dark:text-white">
														{post.author.name}
													</p>
													<p class="text-xs text-gray-500 dark:text-gray-400">
														{post.readTime} min read
													</p>
												</div>
											</div>
											<ArrowRight class="h-4 w-4 text-blue-600 dark:text-blue-400" />
										</div>
									</div>
								</a>
							</article>
						{/each}
					</div>
				</div>
			{/if}
		{/if}
	</div>

	<!-- Newsletter CTA -->
	<section class="bg-blue-600 dark:bg-blue-800">
		<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
			<h2 class="text-3xl font-bold text-white mb-4">
				Stay Updated with Trading Insights
			</h2>
			<p class="text-blue-100 mb-8 text-lg">
				Get the latest trading tips, market analysis, and platform updates delivered to your inbox.
			</p>
			<form class="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
				<input
					type="email"
					placeholder="Enter your email"
					class="flex-1 px-4 py-3 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white placeholder-gray-500"
				/>
				<button
					type="submit"
					class="px-6 py-3 bg-white dark:bg-gray-900 text-blue-600 dark:text-blue-400 rounded-lg font-medium hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
				>
					Subscribe
				</button>
			</form>
		</div>
	</section>
</div>