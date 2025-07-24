<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { 
		User, Settings, Upload, Target, ChevronRight, 
		ChevronLeft, Check, Rocket, FileSpreadsheet,
		BarChart3, Brain
	} from 'lucide-svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	let currentStep = 1;
	let loading = false;
	let completedSteps = new Set<number>();

	// Form data
	let profileData = {
		displayName: '',
		tradingExperience: '',
		preferredMarkets: [],
		timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
	};

	let preferencesData = {
		defaultCurrency: 'USD',
		riskTolerance: 'medium',
		tradingStyle: '',
		goals: []
	};

	let importData = {
		importMethod: '',
		broker: '',
		file: null
	};

	const steps = [
		{
			id: 1,
			title: 'Welcome',
			description: 'Let\'s get you started',
			icon: Rocket
		},
		{
			id: 2,
			title: 'Profile',
			description: 'Tell us about yourself',
			icon: User
		},
		{
			id: 3,
			title: 'Preferences',
			description: 'Customize your experience',
			icon: Settings
		},
		{
			id: 4,
			title: 'Import Trades',
			description: 'Bring your trading history',
			icon: Upload
		},
		{
			id: 5,
			title: 'Complete',
			description: 'You\'re all set!',
			icon: Check
		}
	];

	$: currentStepData = steps.find(s => s.id === currentStep);
	$: progress = ((currentStep - 1) / (steps.length - 1)) * 100;

	function nextStep() {
		if (validateStep()) {
			completedSteps.add(currentStep);
			completedSteps = completedSteps;
			if (currentStep < steps.length) {
				currentStep++;
			}
		}
	}

	function previousStep() {
		if (currentStep > 1) {
			currentStep--;
		}
	}

	function validateStep() {
		switch (currentStep) {
			case 2:
				return profileData.displayName && profileData.tradingExperience;
			case 3:
				return preferencesData.tradingStyle;
			default:
				return true;
		}
	}

	async function completeOnboarding() {
		loading = true;
		// Save onboarding data
		await new Promise(resolve => setTimeout(resolve, 1500));
		await goto('/dashboard');
	}

	function skipImport() {
		completedSteps.add(4);
		currentStep = 5;
	}
</script>

<svelte:head>
	<title>Welcome to TradeSense - Setup Your Account</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
	<div class="max-w-4xl mx-auto px-4 py-8">
		<!-- Progress Bar -->
		<div class="mb-8">
			<div class="flex items-center justify-between mb-4">
				<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
					Account Setup
				</h1>
				<button
					on:click={() => goto('/dashboard')}
					class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
				>
					Skip for now
				</button>
			</div>
			
			<div class="relative">
				<div class="h-2 bg-gray-200 dark:bg-gray-700 rounded-full">
					<div 
						class="h-2 bg-blue-600 rounded-full transition-all duration-300"
						style="width: {progress}%"
					/>
				</div>
				
				<!-- Step Indicators -->
				<div class="absolute -top-3 left-0 right-0 flex justify-between">
					{#each steps as step}
						<div 
							class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-all
								{currentStep >= step.id 
									? 'bg-blue-600 text-white' 
									: 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'}"
						>
							{#if completedSteps.has(step.id)}
								<Check class="h-4 w-4" />
							{:else}
								{step.id}
							{/if}
						</div>
					{/each}
				</div>
			</div>
		</div>

		<!-- Step Content -->
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 mb-8">
			<div class="flex items-center gap-4 mb-6">
				<div class="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
					<svelte:component this={currentStepData.icon} class="h-8 w-8 text-blue-600 dark:text-blue-400" />
				</div>
				<div>
					<h2 class="text-2xl font-bold text-gray-900 dark:text-white">
						{currentStepData.title}
					</h2>
					<p class="text-gray-600 dark:text-gray-400">
						{currentStepData.description}
					</p>
				</div>
			</div>

			<!-- Step Forms -->
			{#if currentStep === 1}
				<!-- Welcome Step -->
				<div class="text-center py-8">
					<h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
						Welcome to TradeSense! 🎉
					</h3>
					<p class="text-gray-600 dark:text-gray-400 mb-8 max-w-2xl mx-auto">
						We're excited to have you on board. This quick setup will help us personalize your experience 
						and get you trading smarter in just a few minutes.
					</p>
					
					<div class="grid md:grid-cols-3 gap-6 max-w-3xl mx-auto mb-8">
						<div class="text-center">
							<div class="inline-flex p-3 bg-green-100 dark:bg-green-900/30 rounded-full mb-3">
								<BarChart3 class="h-8 w-8 text-green-600 dark:text-green-400" />
							</div>
							<h4 class="font-medium text-gray-900 dark:text-white mb-1">Track Performance</h4>
							<p class="text-sm text-gray-600 dark:text-gray-400">
								Monitor your trades and see detailed analytics
							</p>
						</div>
						
						<div class="text-center">
							<div class="inline-flex p-3 bg-purple-100 dark:bg-purple-900/30 rounded-full mb-3">
								<Brain class="h-8 w-8 text-purple-600 dark:text-purple-400" />
							</div>
							<h4 class="font-medium text-gray-900 dark:text-white mb-1">AI Insights</h4>
							<p class="text-sm text-gray-600 dark:text-gray-400">
								Get personalized recommendations to improve
							</p>
						</div>
						
						<div class="text-center">
							<div class="inline-flex p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-3">
								<Target class="h-8 w-8 text-blue-600 dark:text-blue-400" />
							</div>
							<h4 class="font-medium text-gray-900 dark:text-white mb-1">Achieve Goals</h4>
							<p class="text-sm text-gray-600 dark:text-gray-400">
								Set targets and track your progress
							</p>
						</div>
					</div>
				</div>
			{:else if currentStep === 2}
				<!-- Profile Step -->
				<div class="space-y-6">
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Display Name
						</label>
						<input
							type="text"
							bind:value={profileData.displayName}
							placeholder="How should we address you?"
							class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
						/>
					</div>
					
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Trading Experience
						</label>
						<select
							bind:value={profileData.tradingExperience}
							class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
						>
							<option value="">Select your experience level</option>
							<option value="beginner">Beginner (< 1 year)</option>
							<option value="intermediate">Intermediate (1-3 years)</option>
							<option value="advanced">Advanced (3-5 years)</option>
							<option value="expert">Expert (5+ years)</option>
						</select>
					</div>
					
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Preferred Markets
						</label>
						<div class="space-y-2">
							{#each ['Stocks', 'Forex', 'Crypto', 'Futures', 'Options'] as market}
								<label class="flex items-center gap-3">
									<input
										type="checkbox"
										value={market}
										on:change={(e) => {
											if (e.target.checked) {
												profileData.preferredMarkets = [...profileData.preferredMarkets, market];
											} else {
												profileData.preferredMarkets = profileData.preferredMarkets.filter(m => m !== market);
											}
										}}
										class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
									/>
									<span class="text-gray-700 dark:text-gray-300">{market}</span>
								</label>
							{/each}
						</div>
					</div>
					
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Timezone
						</label>
						<select
							bind:value={profileData.timezone}
							class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
						>
							<option value="America/New_York">Eastern Time (ET)</option>
							<option value="America/Chicago">Central Time (CT)</option>
							<option value="America/Denver">Mountain Time (MT)</option>
							<option value="America/Los_Angeles">Pacific Time (PT)</option>
							<option value="Europe/London">London (GMT)</option>
							<option value="Europe/Berlin">Berlin (CET)</option>
							<option value="Asia/Tokyo">Tokyo (JST)</option>
							<option value="Asia/Singapore">Singapore (SGT)</option>
						</select>
					</div>
				</div>
			{:else if currentStep === 3}
				<!-- Preferences Step -->
				<div class="space-y-6">
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Default Currency
						</label>
						<select
							bind:value={preferencesData.defaultCurrency}
							class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
						>
							<option value="USD">USD - US Dollar</option>
							<option value="EUR">EUR - Euro</option>
							<option value="GBP">GBP - British Pound</option>
							<option value="JPY">JPY - Japanese Yen</option>
							<option value="AUD">AUD - Australian Dollar</option>
							<option value="CAD">CAD - Canadian Dollar</option>
						</select>
					</div>
					
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Risk Tolerance
						</label>
						<div class="grid grid-cols-3 gap-3">
							{#each ['low', 'medium', 'high'] as risk}
								<button
									on:click={() => preferencesData.riskTolerance = risk}
									class="px-4 py-2 rounded-lg border transition-colors capitalize
										{preferencesData.riskTolerance === risk 
											? 'bg-blue-600 text-white border-blue-600' 
											: 'bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-700 hover:border-blue-600'}"
								>
									{risk}
								</button>
							{/each}
						</div>
					</div>
					
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Trading Style
						</label>
						<div class="space-y-3">
							{#each [
								{ value: 'daytrading', label: 'Day Trading', desc: 'Open and close positions within the same day' },
								{ value: 'swing', label: 'Swing Trading', desc: 'Hold positions for days to weeks' },
								{ value: 'position', label: 'Position Trading', desc: 'Hold positions for weeks to months' },
								{ value: 'scalping', label: 'Scalping', desc: 'Very short-term trades for small profits' }
							] as style}
								<label class="flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors
									{preferencesData.tradingStyle === style.value 
										? 'bg-blue-50 dark:bg-blue-900/30 border-blue-600' 
										: 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 hover:border-blue-600'}"
								>
									<input
										type="radio"
										bind:group={preferencesData.tradingStyle}
										value={style.value}
										class="mt-1"
									/>
									<div>
										<p class="font-medium text-gray-900 dark:text-white">{style.label}</p>
										<p class="text-sm text-gray-600 dark:text-gray-400">{style.desc}</p>
									</div>
								</label>
							{/each}
						</div>
					</div>
					
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Trading Goals
						</label>
						<div class="space-y-2">
							{#each [
								'Consistent monthly income',
								'Long-term wealth building',
								'Learning and skill development',
								'Portfolio diversification',
								'Risk management improvement'
							] as goal}
								<label class="flex items-center gap-3">
									<input
										type="checkbox"
										value={goal}
										on:change={(e) => {
											if (e.target.checked) {
												preferencesData.goals = [...preferencesData.goals, goal];
											} else {
												preferencesData.goals = preferencesData.goals.filter(g => g !== goal);
											}
										}}
										class="h-4 w-4 text-blue-600 rounded border-gray-300 dark:border-gray-700"
									/>
									<span class="text-gray-700 dark:text-gray-300">{goal}</span>
								</label>
							{/each}
						</div>
					</div>
				</div>
			{:else if currentStep === 4}
				<!-- Import Step -->
				<div class="space-y-6">
					<p class="text-gray-600 dark:text-gray-400">
						Import your trading history to start analyzing your performance right away.
					</p>
					
					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
							How would you like to import your trades?
						</label>
						<div class="grid md:grid-cols-2 gap-4">
							<button
								on:click={() => importData.importMethod = 'csv'}
								class="p-4 rounded-lg border text-left transition-colors
									{importData.importMethod === 'csv' 
										? 'bg-blue-50 dark:bg-blue-900/30 border-blue-600' 
										: 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 hover:border-blue-600'}"
							>
								<FileSpreadsheet class="h-8 w-8 text-blue-600 dark:text-blue-400 mb-2" />
								<h4 class="font-medium text-gray-900 dark:text-white mb-1">CSV Upload</h4>
								<p class="text-sm text-gray-600 dark:text-gray-400">
									Upload a CSV file from your broker
								</p>
							</button>
							
							<button
								on:click={() => importData.importMethod = 'broker'}
								class="p-4 rounded-lg border text-left transition-colors
									{importData.importMethod === 'broker' 
										? 'bg-blue-50 dark:bg-blue-900/30 border-blue-600' 
										: 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 hover:border-blue-600'}"
							>
								<Upload class="h-8 w-8 text-blue-600 dark:text-blue-400 mb-2" />
								<h4 class="font-medium text-gray-900 dark:text-white mb-1">Broker Connection</h4>
								<p class="text-sm text-gray-600 dark:text-gray-400">
									Connect directly to your broker
								</p>
							</button>
						</div>
					</div>
					
					{#if importData.importMethod === 'csv'}
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								Select your CSV file
							</label>
							<input
								type="file"
								accept=".csv"
								on:change={(e) => importData.file = e.target.files[0]}
								class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
							/>
							<p class="text-sm text-gray-600 dark:text-gray-400 mt-2">
								Supported formats: Interactive Brokers, TD Ameritrade, E*TRADE, and more
							</p>
						</div>
					{:else if importData.importMethod === 'broker'}
						<div>
							<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
								Select your broker
							</label>
							<select
								bind:value={importData.broker}
								class="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
							>
								<option value="">Choose a broker</option>
								<option value="ib">Interactive Brokers</option>
								<option value="td">TD Ameritrade</option>
								<option value="etrade">E*TRADE</option>
								<option value="robinhood">Robinhood</option>
								<option value="fidelity">Fidelity</option>
							</select>
						</div>
					{/if}
					
					<div class="flex items-center justify-center">
						<button
							on:click={skipImport}
							class="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
						>
							Skip for now, I'll import later
						</button>
					</div>
				</div>
			{:else if currentStep === 5}
				<!-- Complete Step -->
				<div class="text-center py-8">
					<div class="inline-flex p-4 bg-green-100 dark:bg-green-900/30 rounded-full mb-6">
						<Check class="h-12 w-12 text-green-600 dark:text-green-400" />
					</div>
					
					<h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
						You're All Set! 🎉
					</h3>
					<p class="text-gray-600 dark:text-gray-400 mb-8 max-w-lg mx-auto">
						Your account is configured and ready to go. Let's start tracking your trades and improving your performance!
					</p>
					
					<div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 max-w-lg mx-auto mb-8">
						<h4 class="font-medium text-gray-900 dark:text-white mb-3">Quick Tips to Get Started:</h4>
						<ul class="text-left space-y-2 text-sm text-gray-600 dark:text-gray-400">
							<li class="flex items-start gap-2">
								<Check class="h-4 w-4 text-green-600 dark:text-green-400 shrink-0 mt-0.5" />
								<span>Add your first trade manually or import more trades</span>
							</li>
							<li class="flex items-start gap-2">
								<Check class="h-4 w-4 text-green-600 dark:text-green-400 shrink-0 mt-0.5" />
								<span>Explore the analytics dashboard to see your metrics</span>
							</li>
							<li class="flex items-start gap-2">
								<Check class="h-4 w-4 text-green-600 dark:text-green-400 shrink-0 mt-0.5" />
								<span>Check out AI Insights for personalized recommendations</span>
							</li>
							<li class="flex items-start gap-2">
								<Check class="h-4 w-4 text-green-600 dark:text-green-400 shrink-0 mt-0.5" />
								<span>Set up trade alerts to stay on top of your performance</span>
							</li>
						</ul>
					</div>
				</div>
			{/if}
		</div>

		<!-- Navigation -->
		<div class="flex items-center justify-between">
			{#if currentStep > 1}
				<button
					on:click={previousStep}
					class="flex items-center gap-2 px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
				>
					<ChevronLeft class="h-5 w-5" />
					Previous
				</button>
			{:else}
				<div></div>
			{/if}
			
			{#if currentStep < steps.length}
				<button
					on:click={nextStep}
					disabled={!validateStep()}
					class="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{currentStep === 4 && !importData.importMethod ? 'Skip' : 'Next'}
					<ChevronRight class="h-5 w-5" />
				</button>
			{:else}
				<button
					on:click={completeOnboarding}
					disabled={loading}
					class="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
				>
					{#if loading}
						<LoadingSpinner size="sm" color="white" />
						Setting up...
					{:else}
						Go to Dashboard
						<Rocket class="h-5 w-5" />
					{/if}
				</button>
			{/if}
		</div>
	</div>
</div>