<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Home, FileQuestion, ServerCrash, AlertTriangle, Search, ArrowLeft } from 'lucide-svelte';

	$: error = $page.error;
	$: status = $page.status;

	const publicPages = [
		{ path: '/', label: 'Home', icon: Home },
		{ path: '/features', label: 'Features' },
		{ path: '/pricing', label: 'Pricing' },
		{ path: '/about', label: 'About' },
		{ path: '/blog', label: 'Blog' },
		{ path: '/contact', label: 'Contact' },
		{ path: '/docs', label: 'Documentation' }
	];

	const authPages = [
		{ path: '/dashboard', label: 'Dashboard' },
		{ path: '/trades', label: 'Trade Log' },
		{ path: '/portfolio', label: 'Portfolio' },
		{ path: '/analytics', label: 'Analytics' },
		{ path: '/journal', label: 'Journal' },
		{ path: '/ai-insights', label: 'AI Insights' }
	];

	const supportPages = [
		{ path: '/support', label: 'Support Center' },
		{ path: '/support/kb', label: 'Knowledge Base' },
		{ path: '/status', label: 'System Status' }
	];

	function handleSearch(event: Event) {
		event.preventDefault();
		const form = event.target as HTMLFormElement;
		const query = new FormData(form).get('search') as string;
		if (query) {
			goto(`/search?q=${encodeURIComponent(query)}`);
		}
	}
</script>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
		{#if status === 404}
			<!-- 404 Error Page -->
			<div class="text-center">
				<div class="flex justify-center mb-8">
					<div class="relative">
						<FileQuestion class="h-24 w-24 text-gray-400 dark:text-gray-600" />
						<div class="absolute -bottom-2 -right-2 bg-yellow-500 rounded-full p-2">
							<AlertTriangle class="h-6 w-6 text-white" />
						</div>
					</div>
				</div>
				
				<h1 class="text-6xl font-bold text-gray-900 dark:text-white mb-4">404</h1>
				<h2 class="text-2xl font-semibold text-gray-700 dark:text-gray-300 mb-4">
					Page Not Found
				</h2>
				<p class="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto">
					Sorry, we couldn't find the page you're looking for. It might have been moved, 
					deleted, or the URL might be incorrect.
				</p>

				<!-- Search Bar -->
				<div class="max-w-md mx-auto mb-12">
					<form on:submit={handleSearch} class="relative">
						<input
							type="text"
							name="search"
							placeholder="Search for pages..."
							class="w-full px-4 py-3 pr-12 rounded-lg border border-gray-300 dark:border-gray-700 
									 bg-white dark:bg-gray-800 text-gray-900 dark:text-white
									 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
						/>
						<button
							type="submit"
							class="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-gray-500 hover:text-gray-700 
									 dark:text-gray-400 dark:hover:text-gray-200"
						>
							<Search class="h-5 w-5" />
						</button>
					</form>
				</div>

				<!-- Quick Actions -->
				<div class="flex flex-wrap justify-center gap-4 mb-12">
					<button
						on:click={() => history.back()}
						class="flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-800 
								 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 
								 dark:hover:bg-gray-700 transition-colors"
					>
						<ArrowLeft class="h-4 w-4" />
						Go Back
					</button>
					<a
						href="/"
						class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg 
								 hover:bg-blue-700 transition-colors"
					>
						<Home class="h-4 w-4" />
						Go to Home
					</a>
				</div>

				<!-- Sitemap -->
				<div class="border-t border-gray-200 dark:border-gray-800 pt-12">
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-8">
						Here are some pages you might be looking for:
					</h3>
					
					<div class="grid md:grid-cols-3 gap-8 text-left max-w-4xl mx-auto">
						<!-- Public Pages -->
						<div>
							<h4 class="font-medium text-gray-900 dark:text-white mb-4">General</h4>
							<ul class="space-y-2">
								{#each publicPages as page}
									<li>
										<a
											href={page.path}
											class="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-2"
										>
											{#if page.icon}
												<svelte:component this={page.icon} class="h-4 w-4" />
											{/if}
											{page.label}
										</a>
									</li>
								{/each}
							</ul>
						</div>

						<!-- Auth Pages -->
						<div>
							<h4 class="font-medium text-gray-900 dark:text-white mb-4">Trading Platform</h4>
							<ul class="space-y-2">
								{#each authPages as page}
									<li>
										<a
											href={page.path}
											class="text-blue-600 dark:text-blue-400 hover:underline"
										>
											{page.label}
										</a>
									</li>
								{/each}
							</ul>
						</div>

						<!-- Support Pages -->
						<div>
							<h4 class="font-medium text-gray-900 dark:text-white mb-4">Help & Support</h4>
							<ul class="space-y-2">
								{#each supportPages as page}
									<li>
										<a
											href={page.path}
											class="text-blue-600 dark:text-blue-400 hover:underline"
										>
											{page.label}
										</a>
									</li>
								{/each}
							</ul>
						</div>
					</div>
				</div>
			</div>
			
		{:else if status === 500}
			<!-- 500 Error Page -->
			<div class="text-center">
				<div class="flex justify-center mb-8">
					<div class="relative">
						<ServerCrash class="h-24 w-24 text-red-500" />
					</div>
				</div>
				
				<h1 class="text-6xl font-bold text-gray-900 dark:text-white mb-4">500</h1>
				<h2 class="text-2xl font-semibold text-gray-700 dark:text-gray-300 mb-4">
					Internal Server Error
				</h2>
				<p class="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto">
					Something went wrong on our end. We're working to fix it. 
					Please try again in a few moments.
				</p>

				<div class="flex flex-wrap justify-center gap-4">
					<button
						on:click={() => location.reload()}
						class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
					>
						Try Again
					</button>
					<a
						href="/"
						class="px-6 py-3 bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300 
								 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors"
					>
						Go to Home
					</a>
				</div>

				{#if error?.message}
					<div class="mt-8 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg max-w-2xl mx-auto">
						<p class="text-sm text-red-600 dark:text-red-400">
							Error details: {error.message}
						</p>
					</div>
				{/if}
			</div>
			
		{:else}
			<!-- Generic Error Page -->
			<div class="text-center">
				<div class="flex justify-center mb-8">
					<AlertTriangle class="h-24 w-24 text-yellow-500" />
				</div>
				
				<h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
					Oops! Something went wrong
				</h1>
				<p class="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto">
					An unexpected error occurred. Please try again or contact support if the problem persists.
				</p>

				<div class="flex flex-wrap justify-center gap-4">
					<button
						on:click={() => history.back()}
						class="px-6 py-3 bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300 
								 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors"
					>
						Go Back
					</button>
					<a
						href="/support"
						class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
					>
						Contact Support
					</a>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	/* Add any custom styles here */
</style>