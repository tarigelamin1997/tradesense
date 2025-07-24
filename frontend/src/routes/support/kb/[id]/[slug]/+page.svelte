<script lang="ts">
	import { page } from '$app/stores';
	import { 
		ArrowLeft, Clock, BookOpen, ThumbsUp, ThumbsDown, 
		Share2, Printer, ChevronRight
	} from 'lucide-svelte';
	import { goto } from '$app/navigation';
	import Breadcrumb from '$lib/components/ui/Breadcrumb.svelte';

	// In production, this would come from the database
	const article = {
		id: '1',
		title: 'Getting Started with TradeSense',
		category: 'Getting Started',
		readTime: '5 min',
		lastUpdated: new Date('2024-01-15'),
		author: 'TradeSense Team',
		content: `
			<h2>Welcome to TradeSense</h2>
			<p>TradeSense is a comprehensive trading journal and analytics platform designed to help you track, analyze, and improve your trading performance. This guide will walk you through the basics of getting started with our platform.</p>
			
			<h3>1. Setting Up Your Account</h3>
			<p>After signing up, you'll need to complete a few steps to set up your account:</p>
			<ul>
				<li><strong>Complete your profile:</strong> Add your name and trading preferences</li>
				<li><strong>Choose your subscription:</strong> Select a plan that fits your needs</li>
				<li><strong>Set your timezone:</strong> Ensure accurate timestamps for your trades</li>
				<li><strong>Configure your preferences:</strong> Customize how you want to use TradeSense</li>
			</ul>
			
			<h3>2. Adding Your First Trade</h3>
			<p>There are several ways to add trades to TradeSense:</p>
			<ol>
				<li><strong>Manual Entry:</strong> Click "Add Trade" and fill in the details</li>
				<li><strong>CSV Import:</strong> Upload a CSV file with your trading history</li>
				<li><strong>Broker Integration:</strong> Connect your broker for automatic imports</li>
			</ol>
			
			<h3>3. Understanding Your Dashboard</h3>
			<p>Your dashboard provides a comprehensive overview of your trading performance:</p>
			<ul>
				<li><strong>Performance Summary:</strong> Key metrics like win rate and profit factor</li>
				<li><strong>P&L Chart:</strong> Visual representation of your profit/loss over time</li>
				<li><strong>Recent Trades:</strong> Quick access to your latest trading activity</li>
				<li><strong>AI Insights:</strong> Personalized recommendations based on your trading patterns</li>
			</ul>
			
			<h3>4. Exploring Analytics</h3>
			<p>The Analytics section offers deep insights into your trading:</p>
			<ul>
				<li><strong>Performance Metrics:</strong> Detailed statistics about your trading</li>
				<li><strong>Trade Analysis:</strong> Breakdown by symbol, strategy, and time</li>
				<li><strong>Risk Management:</strong> Analysis of your risk/reward ratios</li>
				<li><strong>Custom Reports:</strong> Create tailored reports for your needs</li>
			</ul>
			
			<h3>5. Next Steps</h3>
			<p>Now that you're familiar with the basics, here are some recommended next steps:</p>
			<ul>
				<li>Import your historical trades to see your full trading history</li>
				<li>Set up trade tags and categories for better organization</li>
				<li>Explore the AI Insights to identify patterns in your trading</li>
				<li>Create custom dashboards to focus on metrics that matter to you</li>
			</ul>
			
			<div class="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg mt-6">
				<p class="text-blue-700 dark:text-blue-400"><strong>Pro Tip:</strong> Start by importing at least 20-30 trades to get meaningful analytics and AI insights. The more data you provide, the better our algorithms can help you improve.</p>
			</div>
		`,
		relatedArticles: [
			{ id: '2', title: 'Your First Trade Import', slug: 'your-first-trade-import' },
			{ id: '3', title: 'Dashboard Overview', slug: 'dashboard-overview' },
			{ id: '4', title: 'Understanding Win Rate and Profit Factor', slug: 'understanding-win-rate' }
		]
	};

	let helpful = null;

	function handleHelpful(value: boolean) {
		helpful = value;
		// In production, this would send feedback to the server
	}

	function shareArticle() {
		if (navigator.share) {
			navigator.share({
				title: article.title,
				url: window.location.href
			});
		} else {
			// Fallback: copy to clipboard
			navigator.clipboard.writeText(window.location.href);
		}
	}

	function printArticle() {
		window.print();
	}
</script>

<svelte:head>
	<title>{article.title} - TradeSense Knowledge Base</title>
	<meta name="description" content={article.content.substring(0, 150).replace(/<[^>]*>/g, '')} />
</svelte:head>

<div class="min-h-screen bg-white dark:bg-gray-900">
	<!-- Breadcrumb -->
	<div class="border-b border-gray-200 dark:border-gray-800">
		<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
			<Breadcrumb items={[
				{ label: 'Support', href: '/support' },
				{ label: 'Knowledge Base', href: '/support/kb' },
				{ label: article.category, href: `/support/kb?category=${article.category}` },
				{ label: article.title }
			]} />
		</div>
	</div>

	<!-- Article Content -->
	<article class="py-8 px-4 sm:px-6 lg:px-8">
		<div class="max-w-4xl mx-auto">
			<!-- Header -->
			<header class="mb-8">
				<button
					on:click={() => goto('/support/kb')}
					class="flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline mb-4"
				>
					<ArrowLeft class="h-4 w-4" />
					Back to Knowledge Base
				</button>
				
				<h1 class="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
					{article.title}
				</h1>
				
				<div class="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
					<div class="flex items-center gap-1">
						<Clock class="h-4 w-4" />
						<span>{article.readTime} read</span>
					</div>
					<div class="flex items-center gap-1">
						<BookOpen class="h-4 w-4" />
						<span>{article.category}</span>
					</div>
					<div>
						Last updated: {article.lastUpdated.toLocaleDateString()}
					</div>
				</div>
			</header>

			<!-- Actions -->
			<div class="flex items-center gap-4 mb-8 pb-8 border-b border-gray-200 dark:border-gray-800">
				<button
					on:click={shareArticle}
					class="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
				>
					<Share2 class="h-4 w-4" />
					Share
				</button>
				<button
					on:click={printArticle}
					class="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
				>
					<Printer class="h-4 w-4" />
					Print
				</button>
			</div>

			<!-- Content -->
			<div class="prose prose-lg dark:prose-invert max-w-none mb-12">
				{@html article.content}
			</div>

			<!-- Feedback -->
			<div class="border-t border-gray-200 dark:border-gray-800 pt-8 mb-12">
				<div class="text-center">
					<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
						Was this article helpful?
					</h3>
					<div class="flex items-center justify-center gap-4">
						<button
							on:click={() => handleHelpful(true)}
							class="flex items-center gap-2 px-4 py-2 rounded-lg transition-colors
								{helpful === true 
									? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' 
									: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'}"
						>
							<ThumbsUp class="h-5 w-5" />
							Yes
						</button>
						<button
							on:click={() => handleHelpful(false)}
							class="flex items-center gap-2 px-4 py-2 rounded-lg transition-colors
								{helpful === false 
									? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' 
									: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'}"
						>
							<ThumbsDown class="h-5 w-5" />
							No
						</button>
					</div>
					{#if helpful !== null}
						<p class="mt-4 text-gray-600 dark:text-gray-400">
							Thank you for your feedback!
						</p>
					{/if}
				</div>
			</div>

			<!-- Related Articles -->
			<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-6">
				<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
					Related Articles
				</h3>
				<div class="space-y-3">
					{#each article.relatedArticles as related}
						<a
							href="/support/kb/{related.id}/{related.slug}"
							class="flex items-center justify-between p-3 bg-white dark:bg-gray-900 rounded-lg hover:shadow-sm transition-shadow group"
						>
							<span class="text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400">
								{related.title}
							</span>
							<ChevronRight class="h-4 w-4 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400" />
						</a>
					{/each}
				</div>
			</div>
		</div>
	</article>

	<!-- Contact Support -->
	<section class="py-8 px-4 sm:px-6 lg:px-8 bg-blue-50 dark:bg-blue-900/20">
		<div class="max-w-4xl mx-auto text-center">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
				Need more help?
			</h3>
			<p class="text-gray-600 dark:text-gray-400 mb-4">
				Contact our support team for personalized assistance.
			</p>
			<a
				href="/contact"
				class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
			>
				Contact Support
			</a>
		</div>
	</section>
</div>

<style>
	@media print {
		/* Hide non-content elements when printing */
		nav, header button, header div, 
		div:has(> button), 
		section:last-child {
			display: none !important;
		}
		
		article {
			padding: 0 !important;
		}
	}
</style>