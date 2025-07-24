<script lang="ts">
	import { 
		TrendingUp, BarChart3, Brain, FileSpreadsheet, 
		Shield, Zap, Users, Globe, Smartphone, Cloud,
		LineChart, PieChart, Calculator, Bell
	} from 'lucide-svelte';

	const features = [
		{
			category: 'Trading Analytics',
			icon: BarChart3,
			items: [
				{
					title: 'Performance Metrics',
					description: 'Track win rate, profit factor, and other key performance indicators',
					icon: TrendingUp
				},
				{
					title: 'Advanced Charts',
					description: 'Interactive charts with multiple timeframes and technical indicators',
					icon: LineChart
				},
				{
					title: 'Risk Analysis',
					description: 'Monitor risk/reward ratios and maximum drawdown',
					icon: Shield
				},
				{
					title: 'P&L Tracking',
					description: 'Real-time profit and loss tracking with detailed breakdowns',
					icon: Calculator
				}
			]
		},
		{
			category: 'AI-Powered Insights',
			icon: Brain,
			items: [
				{
					title: 'Pattern Recognition',
					description: 'AI identifies winning and losing patterns in your trading',
					icon: Brain
				},
				{
					title: 'Trade Recommendations',
					description: 'Get personalized suggestions based on your trading history',
					icon: Zap
				},
				{
					title: 'Market Analysis',
					description: 'AI-driven market sentiment and trend analysis',
					icon: Globe
				},
				{
					title: 'Risk Alerts',
					description: 'Intelligent alerts for potential risk situations',
					icon: Bell
				}
			]
		},
		{
			category: 'Portfolio Management',
			icon: PieChart,
			items: [
				{
					title: 'Multi-Asset Support',
					description: 'Track stocks, forex, crypto, and futures in one place',
					icon: Globe
				},
				{
					title: 'Position Sizing',
					description: 'Automated position sizing based on your risk parameters',
					icon: Calculator
				},
				{
					title: 'Diversification Analysis',
					description: 'Monitor portfolio concentration and correlation',
					icon: PieChart
				},
				{
					title: 'Trade Import',
					description: 'Import trades from popular brokers automatically',
					icon: FileSpreadsheet
				}
			]
		}
	];

	const additionalFeatures = [
		{
			icon: Cloud,
			title: 'Cloud Sync',
			description: 'Access your data from anywhere, on any device'
		},
		{
			icon: Smartphone,
			title: 'Mobile App',
			description: 'Trade logging and analysis on the go'
		},
		{
			icon: Users,
			title: 'Team Collaboration',
			description: 'Share insights and strategies with your trading team'
		},
		{
			icon: Shield,
			title: 'Bank-Level Security',
			description: 'Your data is encrypted and secure'
		}
	];
</script>

<svelte:head>
	<title>Features - TradeSense</title>
	<meta name="description" content="Discover TradeSense's powerful features for trade tracking, analytics, and AI-powered insights to improve your trading performance." />
</svelte:head>

<div class="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
	<!-- Hero Section -->
	<section class="pt-20 pb-16 px-4 sm:px-6 lg:px-8">
		<div class="max-w-7xl mx-auto text-center">
			<h1 class="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6">
				Everything You Need to
				<span class="text-blue-600 dark:text-blue-400"> Succeed in Trading</span>
			</h1>
			<p class="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto mb-12">
				TradeSense combines powerful analytics, AI insights, and intuitive design to help you make better trading decisions and improve your performance.
			</p>
			
			<div class="flex flex-wrap justify-center gap-4">
				<a
					href="/register"
					class="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
				>
					Start Free Trial
				</a>
				<a
					href="/demo"
					class="px-8 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium border border-gray-300 dark:border-gray-600"
				>
					View Demo
				</a>
			</div>
		</div>
	</section>

	<!-- Main Features -->
	<section class="py-16 px-4 sm:px-6 lg:px-8">
		<div class="max-w-7xl mx-auto">
			{#each features as category}
				<div class="mb-16">
					<div class="flex items-center gap-3 mb-8">
						<div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
							<svelte:component this={category.icon} class="h-6 w-6 text-blue-600 dark:text-blue-400" />
						</div>
						<h2 class="text-2xl font-bold text-gray-900 dark:text-white">
							{category.category}
						</h2>
					</div>
					
					<div class="grid md:grid-cols-2 gap-6">
						{#each category.items as feature}
							<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
								<div class="flex items-start gap-4">
									<div class="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg shrink-0">
										<svelte:component this={feature.icon} class="h-5 w-5 text-gray-700 dark:text-gray-300" />
									</div>
									<div>
										<h3 class="font-semibold text-gray-900 dark:text-white mb-2">
											{feature.title}
										</h3>
										<p class="text-gray-600 dark:text-gray-400">
											{feature.description}
										</p>
									</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	</section>

	<!-- Additional Features -->
	<section class="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-900">
		<div class="max-w-7xl mx-auto">
			<h2 class="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
				And Much More
			</h2>
			
			<div class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
				{#each additionalFeatures as feature}
					<div class="text-center">
						<div class="inline-flex p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
							<svelte:component this={feature.icon} class="h-8 w-8 text-blue-600 dark:text-blue-400" />
						</div>
						<h3 class="font-semibold text-gray-900 dark:text-white mb-2">
							{feature.title}
						</h3>
						<p class="text-gray-600 dark:text-gray-400 text-sm">
							{feature.description}
						</p>
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- CTA Section -->
	<section class="py-16 px-4 sm:px-6 lg:px-8">
		<div class="max-w-4xl mx-auto text-center">
			<h2 class="text-3xl font-bold text-gray-900 dark:text-white mb-4">
				Ready to Transform Your Trading?
			</h2>
			<p class="text-xl text-gray-600 dark:text-gray-400 mb-8">
				Join thousands of traders who are already using TradeSense to improve their performance.
			</p>
			
			<div class="flex flex-wrap justify-center gap-4">
				<a
					href="/register"
					class="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
				>
					Start Your Free Trial
				</a>
				<a
					href="/pricing"
					class="px-8 py-3 text-blue-600 dark:text-blue-400 hover:underline font-medium"
				>
					View Pricing →
				</a>
			</div>
		</div>
	</section>
</div>