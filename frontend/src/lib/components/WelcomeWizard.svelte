<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { browser } from '$app/environment';
	import { fade, fly } from 'svelte/transition';
	import { 
		ChevronRight, ChevronLeft, Check, Upload, 
		TrendingUp, BarChart2, BookOpen, Zap 
	} from 'lucide-svelte';
	import { goto } from '$app/navigation';
	
	const dispatch = createEventDispatcher();
	
	export let show = true;
	
	let currentStep = 0;
	let selectedGoal = '';
	let selectedExperience = '';
	let selectedMarkets: string[] = [];
	
	const steps = [
		{
			title: "Welcome to TradeSense! 🎉",
			subtitle: "Let's get you set up in just a few steps"
		},
		{
			title: "What's your main trading goal?",
			subtitle: "This helps us customize your experience"
		},
		{
			title: "How would you describe your experience?",
			subtitle: "We'll adjust complexity based on your level"
		},
		{
			title: "Which markets do you trade?",
			subtitle: "Select all that apply"
		},
		{
			title: "You're all set!",
			subtitle: "Here's how to get started"
		}
	];
	
	const goals = [
		{ id: 'improve', label: 'Improve my win rate', icon: TrendingUp },
		{ id: 'track', label: 'Track performance', icon: BarChart2 },
		{ id: 'learn', label: 'Learn from mistakes', icon: BookOpen },
		{ id: 'consistency', label: 'Build consistency', icon: Zap }
	];
	
	const experienceLevels = [
		{ id: 'beginner', label: 'Beginner', description: 'Less than 1 year' },
		{ id: 'intermediate', label: 'Intermediate', description: '1-3 years' },
		{ id: 'advanced', label: 'Advanced', description: '3-5 years' },
		{ id: 'expert', label: 'Expert', description: '5+ years' }
	];
	
	const markets = [
		'Stocks', 'Options', 'Futures', 'Forex', 'Crypto', 'Bonds', 'Commodities', 'ETFs'
	];
	
	const quickActions = [
		{
			title: 'Import your trades',
			description: 'Upload CSV files from your broker',
			action: () => goto('/upload'),
			icon: Upload
		},
		{
			title: 'Add your first trade',
			description: 'Manually enter a recent trade',
			action: () => goto('/trades/new'),
			icon: TrendingUp
		},
		{
			title: 'Explore demo data',
			description: 'See what TradeSense can do',
			action: () => {
				dispatch('viewDemo');
				handleComplete();
			},
			icon: BarChart2
		}
	];
	
	function handleNext() {
		if (currentStep < steps.length - 1) {
			currentStep++;
		}
	}
	
	function handlePrev() {
		if (currentStep > 0) {
			currentStep--;
		}
	}
	
	function handleComplete() {
		// Save preferences
		const preferences = {
			goal: selectedGoal,
			experience: selectedExperience,
			markets: selectedMarkets,
			wizardCompleted: true
		};
		
		// Store in localStorage
		if (browser) {
			localStorage.setItem('userPreferences', JSON.stringify(preferences));
		}
		
		// Dispatch completion event
		dispatch('complete', preferences);
		
		// Hide wizard
		show = false;
	}
	
	function handleSkip() {
		if (browser) {
			localStorage.setItem('wizardSkipped', 'true');
		}
		show = false;
		dispatch('skip');
	}
	
	function toggleMarket(market: string) {
		if (selectedMarkets.includes(market)) {
			selectedMarkets = selectedMarkets.filter(m => m !== market);
		} else {
			selectedMarkets = [...selectedMarkets, market];
		}
	}
	
	$: canProceed = 
		currentStep === 0 || 
		currentStep === 4 ||
		(currentStep === 1 && selectedGoal) ||
		(currentStep === 2 && selectedExperience) ||
		(currentStep === 3 && selectedMarkets.length > 0);
</script>

{#if show}
	<div class="wizard-overlay" transition:fade={{ duration: 200 }}>
		<div class="wizard-container" transition:fly={{ y: 20, duration: 300 }}>
			<!-- Progress bar -->
			<div class="progress-bar">
				<div class="progress-fill" style="width: {((currentStep + 1) / steps.length) * 100}%"></div>
			</div>
			
			<!-- Skip button -->
			{#if currentStep < steps.length - 1}
				<button class="skip-button" on:click={handleSkip}>
					Skip for now
				</button>
			{/if}
			
			<!-- Step content -->
			<div class="step-content">
				<h2>{steps[currentStep].title}</h2>
				<p>{steps[currentStep].subtitle}</p>
				
				{#if currentStep === 0}
					<div class="welcome-graphic">
						<div class="feature-grid">
							<div class="feature">
								<BarChart2 size={32} />
								<span>Track Performance</span>
							</div>
							<div class="feature">
								<TrendingUp size={32} />
								<span>Improve Win Rate</span>
							</div>
							<div class="feature">
								<BookOpen size={32} />
								<span>Journal Trades</span>
							</div>
							<div class="feature">
								<Zap size={32} />
								<span>Build Consistency</span>
							</div>
						</div>
					</div>
				{:else if currentStep === 1}
					<div class="options-grid">
						{#each goals as goal}
							<button 
								class="option-card"
								class:selected={selectedGoal === goal.id}
								on:click={() => selectedGoal = goal.id}
							>
								<svelte:component this={goal.icon} size={24} />
								<span>{goal.label}</span>
							</button>
						{/each}
					</div>
				{:else if currentStep === 2}
					<div class="experience-levels">
						{#each experienceLevels as level}
							<button 
								class="experience-option"
								class:selected={selectedExperience === level.id}
								on:click={() => selectedExperience = level.id}
							>
								<div class="level-info">
									<h3>{level.label}</h3>
									<p>{level.description}</p>
								</div>
								{#if selectedExperience === level.id}
									<Check size={20} />
								{/if}
							</button>
						{/each}
					</div>
				{:else if currentStep === 3}
					<div class="markets-grid">
						{#each markets as market}
							<button 
								class="market-option"
								class:selected={selectedMarkets.includes(market)}
								on:click={() => toggleMarket(market)}
							>
								{market}
								{#if selectedMarkets.includes(market)}
									<Check size={16} />
								{/if}
							</button>
						{/each}
					</div>
				{:else if currentStep === 4}
					<div class="quick-actions">
						<p class="action-prompt">Choose how you'd like to start:</p>
						{#each quickActions as action}
							<button class="action-card" on:click={action.action}>
								<svelte:component this={action.icon} size={24} />
								<div>
									<h3>{action.title}</h3>
									<p>{action.description}</p>
								</div>
								<ChevronRight size={20} />
							</button>
						{/each}
					</div>
				{/if}
			</div>
			
			<!-- Navigation -->
			<div class="wizard-nav">
				{#if currentStep > 0}
					<button class="nav-button secondary" on:click={handlePrev}>
						<ChevronLeft size={20} />
						Back
					</button>
				{:else}
					<div></div>
				{/if}
				
				{#if currentStep < steps.length - 1}
					<button 
						class="nav-button primary" 
						on:click={handleNext}
						disabled={!canProceed}
					>
						Next
						<ChevronRight size={20} />
					</button>
				{:else}
					<button class="nav-button primary" on:click={handleComplete}>
						Complete Setup
						<Check size={20} />
					</button>
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	.wizard-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 1rem;
	}
	
	.wizard-container {
		background: white;
		border-radius: 16px;
		max-width: 600px;
		width: 100%;
		max-height: 90vh;
		overflow-y: auto;
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
		position: relative;
	}
	
	.progress-bar {
		height: 4px;
		background: #e5e7eb;
		border-radius: 16px 16px 0 0;
		overflow: hidden;
	}
	
	.progress-fill {
		height: 100%;
		background: #10b981;
		transition: width 0.3s ease;
	}
	
	.skip-button {
		position: absolute;
		top: 1rem;
		right: 1rem;
		background: none;
		border: none;
		color: #666;
		font-size: 0.875rem;
		cursor: pointer;
		padding: 0.5rem;
		transition: color 0.2s;
	}
	
	.skip-button:hover {
		color: #333;
	}
	
	.step-content {
		padding: 3rem;
		text-align: center;
	}
	
	.step-content h2 {
		font-size: 1.75rem;
		margin-bottom: 0.5rem;
		color: #1a1a1a;
	}
	
	.step-content > p {
		color: #666;
		margin-bottom: 2rem;
	}
	
	.welcome-graphic {
		margin: 2rem 0;
	}
	
	.feature-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1.5rem;
	}
	
	.feature {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		padding: 1.5rem;
		background: #f9fafb;
		border-radius: 8px;
		color: #10b981;
	}
	
	.feature span {
		color: #333;
		font-size: 0.875rem;
	}
	
	.options-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 1rem;
		margin-bottom: 1rem;
	}
	
	.option-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.75rem;
		padding: 2rem 1rem;
		background: white;
		border: 2px solid #e5e7eb;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.option-card:hover {
		border-color: #10b981;
		transform: translateY(-2px);
	}
	
	.option-card.selected {
		border-color: #10b981;
		background: #f0fdf4;
		color: #059669;
	}
	
	.experience-levels {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		text-align: left;
	}
	
	.experience-option {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1.5rem;
		background: white;
		border: 2px solid #e5e7eb;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.2s;
		width: 100%;
	}
	
	.experience-option:hover {
		border-color: #10b981;
	}
	
	.experience-option.selected {
		border-color: #10b981;
		background: #f0fdf4;
	}
	
	.level-info h3 {
		font-size: 1.125rem;
		margin-bottom: 0.25rem;
		color: #1a1a1a;
	}
	
	.level-info p {
		font-size: 0.875rem;
		color: #666;
		margin: 0;
	}
	
	.markets-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: 0.75rem;
	}
	
	.market-option {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		background: white;
		border: 2px solid #e5e7eb;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.2s;
		font-size: 0.875rem;
	}
	
	.market-option:hover {
		border-color: #10b981;
	}
	
	.market-option.selected {
		border-color: #10b981;
		background: #f0fdf4;
		color: #059669;
	}
	
	.quick-actions {
		text-align: left;
	}
	
	.action-prompt {
		margin-bottom: 1.5rem;
		text-align: center;
	}
	
	.action-card {
		display: flex;
		align-items: center;
		gap: 1rem;
		width: 100%;
		padding: 1.5rem;
		margin-bottom: 1rem;
		background: white;
		border: 2px solid #e5e7eb;
		border-radius: 12px;
		cursor: pointer;
		transition: all 0.2s;
		text-align: left;
	}
	
	.action-card:hover {
		border-color: #10b981;
		transform: translateX(4px);
	}
	
	.action-card > div {
		flex: 1;
	}
	
	.action-card h3 {
		font-size: 1.125rem;
		margin-bottom: 0.25rem;
		color: #1a1a1a;
	}
	
	.action-card p {
		font-size: 0.875rem;
		color: #666;
		margin: 0;
	}
	
	.wizard-nav {
		display: flex;
		justify-content: space-between;
		padding: 2rem 3rem 3rem;
		gap: 1rem;
	}
	
	.nav-button {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.nav-button.primary {
		background: #10b981;
		color: white;
	}
	
	.nav-button.primary:hover:not(:disabled) {
		background: #059669;
	}
	
	.nav-button.primary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.nav-button.secondary {
		background: #f3f4f6;
		color: #333;
	}
	
	.nav-button.secondary:hover {
		background: #e5e7eb;
	}
	
	@media (max-width: 640px) {
		.step-content {
			padding: 2rem 1.5rem;
		}
		
		.wizard-nav {
			padding: 1.5rem;
		}
		
		.options-grid {
			grid-template-columns: 1fr;
		}
		
		.feature-grid {
			grid-template-columns: 1fr;
		}
	}
</style>