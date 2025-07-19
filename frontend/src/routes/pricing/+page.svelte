<script lang="ts">
	import { goto } from '$app/navigation';
	import { Check, X, Zap, TrendingUp, Shield } from 'lucide-svelte';
	import { billingApi } from '$lib/api/billing.js';
	import { isAuthenticated } from '$lib/api/auth.js';
	import { get } from 'svelte/store';
	import { logger } from '$lib/utils/logger';
	
	let isAnnual = false;
	let loading = false;
	let error = '';
	
	const plans = [
		{
			id: 'free',
			name: 'Free',
			monthlyPrice: 0,
			annualPrice: 0,
			description: 'Start tracking your trades',
			features: [
				{ text: 'Up to 10 trades per month', included: true },
				{ text: 'Basic analytics', included: true },
				{ text: 'Trade journal', included: true },
				{ text: 'CSV export', included: true },
				{ text: '1 basic dashboard', included: true },
				{ text: 'Custom dashboard builder', included: false },
				{ text: 'Advanced analytics', included: false },
				{ text: 'Real-time data', included: false },
				{ text: 'Basic AI risk scores', included: false },
				{ text: 'AI pattern detection', included: false },
				{ text: 'Behavioral analytics', included: false },
				{ text: 'Priority support', included: false }
			],
			limits: {
				trades_per_month: 10,
				journal_entries_per_month: 20,
				playbooks: 2
			},
			stripeProductId: null
		},
		{
			id: 'pro',
			name: 'Pro',
			monthlyPrice: 29,
			annualPrice: 290,
			description: 'For serious traders',
			features: [
				{ text: 'Unlimited trades', included: true },
				{ text: 'Advanced analytics', included: true },
				{ text: 'Real-time data', included: true },
				{ text: 'Performance metrics', included: true },
				{ text: '5 custom dashboards', included: true },
				{ text: 'Drag & drop dashboard builder', included: true },
				{ text: '10+ widget types', included: true },
				{ text: 'Multiple strategies', included: true },
				{ text: 'API access', included: true },
				{ text: 'AI trading coach', included: true },
				{ text: 'Pattern detection', included: true },
				{ text: 'Behavioral analytics', included: true },
				{ text: 'Pre-trade analysis', included: true },
				{ text: 'Market regime detection', included: true },
				{ text: 'Priority support', included: false }
			],
			limits: {
				trades_per_month: -1,
				journal_entries_per_month: -1,
				playbooks: 10
			},
			stripeProductId: 'price_pro_monthly',
			annualProductId: 'price_pro_yearly',
			recommended: true
		},
		{
			id: 'enterprise',
			name: 'Enterprise',
			monthlyPrice: 99,
			annualPrice: 990,
			description: 'For professional traders',
			features: [
				{ text: 'Everything in Pro', included: true },
				{ text: 'Unlimited custom dashboards', included: true },
				{ text: 'Dashboard sharing & collaboration', included: true },
				{ text: 'AI-powered insights', included: true },
				{ text: 'Advanced risk analytics', included: true },
				{ text: 'Custom integrations', included: true },
				{ text: 'White-glove onboarding', included: true },
				{ text: 'Dedicated account manager', included: true },
				{ text: '24/7 priority support', included: true },
				{ text: 'Custom reporting', included: true }
			],
			limits: {
				trades_per_month: -1,
				journal_entries_per_month: -1,
				playbooks: -1
			},
			stripeProductId: 'price_enterprise_monthly',
			annualProductId: 'price_enterprise_yearly'
		}
	];
	
	async function handleSubscribe(plan: any) {
		if (plan.id === 'free') {
			if (!get(isAuthenticated)) {
				goto('/register');
			} else {
				goto('/dashboard');
			}
			return;
		}
		
		try {
			loading = true;
			error = '';
			
			if (!get(isAuthenticated)) {
				// Store plan selection and redirect to register
				localStorage.setItem('selectedPlan', JSON.stringify({
					planId: plan.id,
					isAnnual
				}));
				goto('/register');
				return;
			}
			
			// Create checkout session
			const productId = isAnnual ? plan.annualProductId : plan.stripeProductId;
			const { url } = await billingApi.createCheckoutSession({
				productId,
				successUrl: `${window.location.origin}/payment-success`,
				cancelUrl: `${window.location.origin}/pricing`
			});
			
			// Redirect to Stripe checkout
			window.location.href = url;
			
		} catch (err: any) {
			logger.error('Failed to create checkout session:', err);
			error = err.message || 'Failed to start checkout process';
		} finally {
			loading = false;
		}
	}
	
	function calculateSavings(monthlyPrice: number, annualPrice: number): number {
		const yearlyFromMonthly = monthlyPrice * 12;
		return Math.round(((yearlyFromMonthly - annualPrice) / yearlyFromMonthly) * 100);
	}
</script>

<svelte:head>
	<title>Pricing - TradeSense</title>
</svelte:head>

<div class="pricing-page">
	<div class="pricing-header">
		<h1>Choose Your Trading Edge</h1>
		<p>Start free and upgrade as you grow. No hidden fees.</p>
		
		<div class="billing-toggle">
			<span class:active={!isAnnual}>Monthly</span>
			<button 
				class="toggle-switch"
				class:annual={isAnnual}
				on:click={() => isAnnual = !isAnnual}
			>
				<span class="toggle-slider" />
			</button>
			<span class:active={isAnnual}>
				Annual
				<span class="save-badge">Save 20%</span>
			</span>
		</div>
	</div>
	
	{#if error}
		<div class="error-message">{error}</div>
	{/if}
	
	<div class="pricing-grid">
		{#each plans as plan}
			<div class="pricing-card" class:recommended={plan.recommended}>
				{#if plan.recommended}
					<div class="recommended-badge">
						<Zap size={16} />
						Most Popular
					</div>
				{/if}
				
				<div class="plan-header">
					<h3>{plan.name}</h3>
					<p>{plan.description}</p>
				</div>
				
				<div class="plan-price">
					<span class="currency">$</span>
					<span class="amount">
						{isAnnual 
							? Math.floor(plan.annualPrice / 12) 
							: plan.monthlyPrice}
					</span>
					<span class="period">/month</span>
				</div>
				
				{#if isAnnual && plan.monthlyPrice > 0}
					<div class="annual-pricing">
						${plan.annualPrice} billed annually
						<span class="savings">
							Save {calculateSavings(plan.monthlyPrice, plan.annualPrice)}%
						</span>
					</div>
				{/if}
				
				<button 
					class="subscribe-button"
					class:primary={plan.recommended}
					on:click={() => handleSubscribe(plan)}
					disabled={loading}
				>
					{plan.id === 'free' ? 'Get Started' : 'Subscribe'}
				</button>
				
				<div class="features-list">
					{#each plan.features as feature}
						<div class="feature" class:excluded={!feature.included}>
							{#if feature.included}
								<Check size={18} class="check-icon" />
							{:else}
								<X size={18} class="x-icon" />
							{/if}
							<span>{feature.text}</span>
						</div>
					{/each}
				</div>
			</div>
		{/each}
	</div>
	
	<!-- Trust Badges -->
	<div class="trust-section">
		<div class="trust-badge">
			<Shield size={24} />
			<div>
				<h4>Bank-level Security</h4>
				<p>Your data is encrypted and secure</p>
			</div>
		</div>
		<div class="trust-badge">
			<TrendingUp size={24} />
			<div>
				<h4>No Hidden Fees</h4>
				<p>Cancel or change plans anytime</p>
			</div>
		</div>
	</div>
	
	<!-- FAQ Section -->
	<div class="faq-section">
		<h2>Frequently Asked Questions</h2>
		<div class="faq-grid">
			<div class="faq-item">
				<h3>Can I change plans later?</h3>
				<p>Yes! You can upgrade or downgrade your plan at any time. Changes take effect at the next billing cycle.</p>
			</div>
			<div class="faq-item">
				<h3>What payment methods do you accept?</h3>
				<p>We accept all major credit cards, debit cards, and bank transfers through our secure payment processor, Stripe.</p>
			</div>
			<div class="faq-item">
				<h3>Is there a free trial?</h3>
				<p>Our free plan lets you explore TradeSense with up to 10 trades per month. No credit card required.</p>
			</div>
			<div class="faq-item">
				<h3>How do I cancel my subscription?</h3>
				<p>You can cancel anytime from your account settings. You'll continue to have access until the end of your billing period.</p>
			</div>
		</div>
	</div>
</div>

<style>
	.pricing-page {
		max-width: 1200px;
		margin: 0 auto;
		padding-bottom: 4rem;
	}
	
	.pricing-header {
		text-align: center;
		margin-bottom: 3rem;
	}
	
	.pricing-header h1 {
		font-size: 3rem;
		margin-bottom: 1rem;
		background: linear-gradient(135deg, #10b981 0%, #059669 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}
	
	.pricing-header p {
		font-size: 1.25rem;
		color: #666;
		margin-bottom: 2rem;
	}
	
	.billing-toggle {
		display: inline-flex;
		align-items: center;
		gap: 1rem;
		padding: 0.5rem;
		background: #f3f4f6;
		border-radius: 100px;
	}
	
	.billing-toggle span {
		padding: 0.5rem 1rem;
		color: #666;
		transition: color 0.2s;
	}
	
	.billing-toggle span.active {
		color: #333;
		font-weight: 600;
	}
	
	.toggle-switch {
		position: relative;
		width: 56px;
		height: 28px;
		background: #e5e7eb;
		border: none;
		border-radius: 100px;
		cursor: pointer;
		transition: background 0.3s;
	}
	
	.toggle-switch.annual {
		background: #10b981;
	}
	
	.toggle-slider {
		position: absolute;
		top: 2px;
		left: 2px;
		width: 24px;
		height: 24px;
		background: white;
		border-radius: 50%;
		transition: transform 0.3s;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}
	
	.toggle-switch.annual .toggle-slider {
		transform: translateX(28px);
	}
	
	.save-badge {
		background: #10b981;
		color: white;
		padding: 0.125rem 0.5rem;
		border-radius: 12px;
		font-size: 0.75rem;
		margin-left: 0.5rem;
	}
	
	.error-message {
		background: #fee;
		color: #dc2626;
		padding: 1rem;
		border-radius: 8px;
		text-align: center;
		margin-bottom: 2rem;
	}
	
	.pricing-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
		gap: 2rem;
		margin-bottom: 4rem;
	}
	
	.pricing-card {
		position: relative;
		background: white;
		border: 2px solid #e0e0e0;
		border-radius: 16px;
		padding: 2rem;
		transition: all 0.3s;
	}
	
	.pricing-card:hover {
		transform: translateY(-4px);
		box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
	}
	
	.pricing-card.recommended {
		border-color: #10b981;
		box-shadow: 0 8px 16px rgba(16, 185, 129, 0.1);
	}
	
	.recommended-badge {
		position: absolute;
		top: -1px;
		left: 50%;
		transform: translateX(-50%);
		background: #10b981;
		color: white;
		padding: 0.375rem 1.5rem;
		border-radius: 0 0 12px 12px;
		font-size: 0.875rem;
		font-weight: 600;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.plan-header {
		text-align: center;
		margin-bottom: 2rem;
	}
	
	.plan-header h3 {
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}
	
	.plan-header p {
		color: #666;
	}
	
	.plan-price {
		text-align: center;
		margin-bottom: 1rem;
	}
	
	.currency {
		font-size: 1.5rem;
		color: #666;
		vertical-align: top;
	}
	
	.amount {
		font-size: 3.5rem;
		font-weight: 700;
		color: #1a1a1a;
	}
	
	.period {
		color: #666;
		font-size: 1rem;
	}
	
	.annual-pricing {
		text-align: center;
		font-size: 0.875rem;
		color: #666;
		margin-bottom: 2rem;
	}
	
	.savings {
		color: #10b981;
		font-weight: 600;
		margin-left: 0.5rem;
	}
	
	.subscribe-button {
		width: 100%;
		padding: 1rem;
		background: white;
		color: #333;
		border: 2px solid #e0e0e0;
		border-radius: 8px;
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
		margin-bottom: 2rem;
	}
	
	.subscribe-button:hover {
		background: #f3f4f6;
		border-color: #d1d5db;
	}
	
	.subscribe-button.primary {
		background: #10b981;
		color: white;
		border-color: #10b981;
	}
	
	.subscribe-button.primary:hover {
		background: #059669;
		border-color: #059669;
	}
	
	.subscribe-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	.features-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.feature {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		font-size: 0.875rem;
	}
	
	.feature.excluded {
		opacity: 0.5;
	}
	
	:global(.check-icon) {
		color: #10b981;
		flex-shrink: 0;
	}
	
	:global(.x-icon) {
		color: #e5e7eb;
		flex-shrink: 0;
	}
	
	/* Trust Section */
	.trust-section {
		display: flex;
		justify-content: center;
		gap: 4rem;
		margin-bottom: 4rem;
		padding: 2rem;
		background: #f9fafb;
		border-radius: 16px;
	}
	
	.trust-badge {
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.trust-badge h4 {
		font-size: 1rem;
		margin-bottom: 0.25rem;
	}
	
	.trust-badge p {
		font-size: 0.875rem;
		color: #666;
	}
	
	/* FAQ Section */
	.faq-section {
		max-width: 900px;
		margin: 0 auto;
	}
	
	.faq-section h2 {
		font-size: 2rem;
		text-align: center;
		margin-bottom: 2rem;
	}
	
	.faq-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
		gap: 2rem;
	}
	
	.faq-item {
		padding: 1.5rem;
		background: white;
		border-radius: 12px;
		border: 1px solid #e0e0e0;
	}
	
	.faq-item h3 {
		font-size: 1.125rem;
		margin-bottom: 0.75rem;
		color: #333;
	}
	
	.faq-item p {
		color: #666;
		line-height: 1.6;
	}
	
	.warning-banner {
		background: #fef3c7;
		border: 1px solid #f59e0b;
		color: #92400e;
		padding: 1rem;
		border-radius: 8px;
		margin-top: 1rem;
		font-size: 0.875rem;
		text-align: center;
	}
	
	.warning-banner a {
		color: #dc2626;
		text-decoration: underline;
	}
	
	@media (max-width: 768px) {
		.pricing-header h1 {
			font-size: 2rem;
		}
		
		.pricing-grid {
			grid-template-columns: 1fr;
		}
		
		.trust-section {
			flex-direction: column;
			gap: 2rem;
		}
		
		.faq-grid {
			grid-template-columns: 1fr;
		}
	}
</style>