<script lang="ts">
	import { Users, Target, Award, TrendingUp, Heart, Shield } from 'lucide-svelte';

	const stats = [
		{ label: 'Active Traders', value: '10,000+' },
		{ label: 'Trades Analyzed', value: '5M+' },
		{ label: 'Countries', value: '50+' },
		{ label: 'Uptime', value: '99.9%' }
	];

	const values = [
		{
			icon: Target,
			title: 'Mission-Driven',
			description: 'We\'re committed to helping traders achieve consistent profitability through data-driven insights.'
		},
		{
			icon: Users,
			title: 'Trader-First',
			description: 'Every feature we build starts with understanding real trader needs and pain points.'
		},
		{
			icon: Shield,
			title: 'Security & Privacy',
			description: 'Your trading data is encrypted and secure. We never share your information.'
		},
		{
			icon: Heart,
			title: 'Community',
			description: 'We foster a supportive community where traders help each other grow and succeed.'
		}
	];

	const team = [
		{
			name: 'Sarah Chen',
			role: 'CEO & Co-Founder',
			bio: 'Former quant trader with 10+ years experience in algorithmic trading.',
			image: '/images/team/sarah.jpg'
		},
		{
			name: 'Michael Rodriguez',
			role: 'CTO & Co-Founder',
			bio: 'Engineering leader with expertise in financial technology and real-time systems.',
			image: '/images/team/michael.jpg'
		},
		{
			name: 'Emily Watson',
			role: 'Head of Product',
			bio: 'Product strategist focused on creating intuitive tools for complex workflows.',
			image: '/images/team/emily.jpg'
		},
		{
			name: 'David Kim',
			role: 'Head of AI',
			bio: 'Machine learning expert specializing in financial pattern recognition.',
			image: '/images/team/david.jpg'
		}
	];
</script>

<svelte:head>
	<title>About Us - TradeSense</title>
	<meta name="description" content="Learn about TradeSense's mission to empower traders with data-driven insights and AI-powered analytics." />
</svelte:head>

<div class="min-h-screen bg-white dark:bg-gray-900">
	<!-- Hero Section -->
	<section class="pt-20 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-white dark:from-gray-800 dark:to-gray-900">
		<div class="max-w-7xl mx-auto text-center">
			<h1 class="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6">
				Empowering Traders to
				<span class="text-blue-600 dark:text-blue-400"> Achieve More</span>
			</h1>
			<p class="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
				We believe every trader deserves access to professional-grade analytics and insights. 
				That's why we built TradeSense - to level the playing field and help traders of all 
				levels improve their performance.
			</p>
		</div>
	</section>

	<!-- Stats Section -->
	<section class="py-16 px-4 sm:px-6 lg:px-8 border-b border-gray-200 dark:border-gray-800">
		<div class="max-w-7xl mx-auto">
			<div class="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
				{#each stats as stat}
					<div>
						<p class="text-3xl md:text-4xl font-bold text-blue-600 dark:text-blue-400 mb-2">
							{stat.value}
						</p>
						<p class="text-gray-600 dark:text-gray-400">
							{stat.label}
						</p>
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- Story Section -->
	<section class="py-16 px-4 sm:px-6 lg:px-8">
		<div class="max-w-4xl mx-auto">
			<h2 class="text-3xl font-bold text-gray-900 dark:text-white mb-8 text-center">
				Our Story
			</h2>
			
			<div class="prose prose-lg dark:prose-invert mx-auto">
				<p class="text-gray-600 dark:text-gray-400 mb-6">
					TradeSense was born from a simple observation: while professional traders had access 
					to sophisticated analytics tools, retail traders were left with spreadsheets and 
					basic charting software.
				</p>
				
				<p class="text-gray-600 dark:text-gray-400 mb-6">
					Our founders, both experienced traders and technologists, saw an opportunity to 
					democratize trading analytics. They envisioned a platform that would give every 
					trader - from beginners to professionals - the insights they need to improve.
				</p>
				
				<p class="text-gray-600 dark:text-gray-400">
					Today, TradeSense serves thousands of traders worldwide, helping them track their 
					performance, identify patterns, and make data-driven decisions. We're just getting 
					started on our mission to transform how traders analyze and improve their performance.
				</p>
			</div>
		</div>
	</section>

	<!-- Values Section -->
	<section class="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-800">
		<div class="max-w-7xl mx-auto">
			<h2 class="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
				Our Values
			</h2>
			
			<div class="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
				{#each values as value}
					<div class="text-center">
						<div class="inline-flex p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
							<svelte:component this={value.icon} class="h-8 w-8 text-blue-600 dark:text-blue-400" />
						</div>
						<h3 class="font-semibold text-gray-900 dark:text-white mb-2">
							{value.title}
						</h3>
						<p class="text-gray-600 dark:text-gray-400 text-sm">
							{value.description}
						</p>
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- Team Section -->
	<section class="py-16 px-4 sm:px-6 lg:px-8">
		<div class="max-w-7xl mx-auto">
			<h2 class="text-3xl font-bold text-center text-gray-900 dark:text-white mb-12">
				Meet Our Team
			</h2>
			
			<div class="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
				{#each team as member}
					<div class="text-center">
						<div class="w-32 h-32 mx-auto mb-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
							<!-- Placeholder for team member photo -->
							<div class="w-full h-full flex items-center justify-center">
								<Users class="h-16 w-16 text-gray-400 dark:text-gray-600" />
							</div>
						</div>
						<h3 class="font-semibold text-gray-900 dark:text-white mb-1">
							{member.name}
						</h3>
						<p class="text-blue-600 dark:text-blue-400 text-sm mb-3">
							{member.role}
						</p>
						<p class="text-gray-600 dark:text-gray-400 text-sm">
							{member.bio}
						</p>
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- CTA Section -->
	<section class="py-16 px-4 sm:px-6 lg:px-8 bg-blue-600 dark:bg-blue-700">
		<div class="max-w-4xl mx-auto text-center">
			<h2 class="text-3xl font-bold text-white mb-4">
				Join Our Mission
			</h2>
			<p class="text-xl text-blue-100 mb-8">
				Whether you're a trader looking to improve or a talented professional wanting to make an impact, we'd love to hear from you.
			</p>
			
			<div class="flex flex-wrap justify-center gap-4">
				<a
					href="/register"
					class="px-8 py-3 bg-white text-blue-600 rounded-lg hover:bg-gray-100 transition-colors font-medium"
				>
					Start Trading Smarter
				</a>
				<a
					href="/careers"
					class="px-8 py-3 bg-blue-700 dark:bg-blue-800 text-white rounded-lg hover:bg-blue-800 dark:hover:bg-blue-900 transition-colors font-medium"
				>
					View Careers
				</a>
			</div>
		</div>
	</section>
</div>