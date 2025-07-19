<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { CreditCard, Calendar, TrendingUp, AlertCircle, ExternalLink } from 'lucide-svelte';
	import { billingApi, type Subscription, type Usage } from '$lib/api/billing';
	import { isAuthenticated } from '$lib/api/auth';
	import { get } from 'svelte/store';
	import { logger } from '$lib/utils/logger';
	
	let loading = true;
	let error = '';
	let subscription: Subscription | null = null;
	let usage: Usage | null = null;
	
	const planDetails = {
		free: {
			name: 'Free',
			color: 'gray',
			price: 0
		},
		pro: {
			name: 'Pro',
			color: 'blue',
			price: 29
		},
		enterprise: {
			name: 'Enterprise',
			color: 'purple',
			price: 99
		}
	};
	
	async function fetchBillingData() {
		try {
			loading = true;
			error = '';
			
			if (!get(isAuthenticated)) {
				goto('/login');
				return;
			}
			
			// Fetch subscription and usage data
			const [subData, usageData] = await Promise.all([
				billingApi.getSubscription(),
				billingApi.getUsage()
			]);
			
			subscription = subData;
			usage = usageData;
			
		} catch (err: any) {
			logger.error('Failed to fetch billing data:', err);
			error = err.message || 'Failed to load billing information';
		} finally {
			loading = false;
		}
	}
	
	async function handleManageBilling() {
		try {
			const { url } = await billingApi.createPortalSession(window.location.href);
			window.location.href = url;
		} catch (err: any) {
			logger.error('Failed to create portal session:', err);
			error = err.message || 'Failed to open billing portal';
		}
	}
	
	async function handleCancelSubscription() {
		if (!confirm('Are you sure you want to cancel your subscription? You will lose access to premium features at the end of your billing period.')) {
			return;
		}
		
		try {
			await billingApi.cancelSubscription();
			await fetchBillingData();
		} catch (err: any) {
			logger.error('Failed to cancel subscription:', err);
			error = err.message || 'Failed to cancel subscription';
		}
	}
	
	async function handleResumeSubscription() {
		try {
			await billingApi.resumeSubscription();
			await fetchBillingData();
		} catch (err: any) {
			logger.error('Failed to resume subscription:', err);
			error = err.message || 'Failed to resume subscription';
		}
	}
	
	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}
	
	function getUsagePercentage(current: number, limit: number): number {
		if (limit === -1) return 0; // Unlimited
		return Math.min((current / limit) * 100, 100);
	}
	
	function getPlanFromId(planId: string): string {
		if (planId.includes('enterprise')) return 'enterprise';
		if (planId.includes('pro')) return 'pro';
		return 'free';
	}
	
	onMount(() => {
		fetchBillingData();
	});
</script>

<svelte:head>
	<title>Billing - TradeSense</title>
</svelte:head>

<div class="billing-page">
	<header class="page-header">
		<h1>Billing & Subscription</h1>
		<p>Manage your subscription and view usage</p>
	</header>
	
	{#if loading}
		<div class="loading">Loading billing information...</div>
	{:else if error}
		<div class="error-message">
			<AlertCircle size={20} />
			{error}
		</div>
	{:else}
		<!-- Current Plan -->
		<div class="billing-section">
			<h2>Current Plan</h2>
			<div class="plan-card card">
				{#if subscription}
					{@const plan = getPlanFromId(subscription.plan_id)}
					{@const details = planDetails[plan] || planDetails.free}
					<div class="plan-info">
						<div>
							<h3>{details.name} Plan</h3>
							<p class="plan-price">${details.price}/month</p>
							<div class="plan-status">
								<span class="status-badge" class:active={subscription.status === 'active'}>
									{subscription.status}
								</span>
							</div>
						</div>
						<div class="plan-actions">
							{#if subscription.status === 'active'}
								<button on:click={handleManageBilling} class="manage-button">
									<CreditCard size={18} />
									Manage Billing
								</button>
								<button on:click={handleCancelSubscription} class="cancel-button">
									Cancel Subscription
								</button>
							{:else if subscription.status === 'canceled'}
								<button on:click={handleResumeSubscription} class="resume-button">
									Resume Subscription
								</button>
							{/if}
						</div>
					</div>
					
					<div class="billing-dates">
						<div class="date-item">
							<Calendar size={16} />
							<span>Current period: {formatDate(subscription.current_period_start)} - {formatDate(subscription.current_period_end)}</span>
						</div>
						{#if subscription.status === 'canceled'}
							<div class="date-item warning">
								<AlertCircle size={16} />
								<span>Access ends on {formatDate(subscription.current_period_end)}</span>
							</div>
						{/if}
					</div>
				{:else}
					<div class="plan-info">
						<div>
							<h3>Free Plan</h3>
							<p class="plan-price">$0/month</p>
							<p class="plan-description">Limited features with usage caps</p>
						</div>
						<div class="plan-actions">
							<a href="/pricing" class="upgrade-button">
								<TrendingUp size={18} />
								Upgrade Plan
							</a>
						</div>
					</div>
				{/if}
			</div>
		</div>
		
		<!-- Usage Statistics -->
		{#if usage}
			<div class="billing-section">
				<h2>Usage This Period</h2>
				<div class="usage-grid">
					<!-- Trades Usage -->
					<div class="usage-card card">
						<h3>Trades</h3>
						<div class="usage-stats">
							<span class="usage-current">{usage.trades_count}</span>
							<span class="usage-separator">/</span>
							<span class="usage-limit">
								{usage.trades_limit === -1 ? 'Unlimited' : usage.trades_limit}
							</span>
						</div>
						{#if usage.trades_limit !== -1}
							<div class="usage-bar">
								<div 
									class="usage-bar-fill"
									style="width: {getUsagePercentage(usage.trades_count, usage.trades_limit)}%"
									class:warning={getUsagePercentage(usage.trades_count, usage.trades_limit) > 80}
								/>
							</div>
						{/if}
					</div>
					
					<!-- Journal Entries Usage -->
					<div class="usage-card card">
						<h3>Journal Entries</h3>
						<div class="usage-stats">
							<span class="usage-current">{usage.journal_entries_count}</span>
							<span class="usage-separator">/</span>
							<span class="usage-limit">
								{usage.journal_entries_limit === -1 ? 'Unlimited' : usage.journal_entries_limit}
							</span>
						</div>
						{#if usage.journal_entries_limit !== -1}
							<div class="usage-bar">
								<div 
									class="usage-bar-fill"
									style="width: {getUsagePercentage(usage.journal_entries_count, usage.journal_entries_limit)}%"
									class:warning={getUsagePercentage(usage.journal_entries_count, usage.journal_entries_limit) > 80}
								/>
							</div>
						{/if}
					</div>
					
					<!-- Playbooks Usage -->
					<div class="usage-card card">
						<h3>Playbooks</h3>
						<div class="usage-stats">
							<span class="usage-current">{usage.playbooks_count}</span>
							<span class="usage-separator">/</span>
							<span class="usage-limit">
								{usage.playbooks_limit === -1 ? 'Unlimited' : usage.playbooks_limit}
							</span>
						</div>
						{#if usage.playbooks_limit !== -1}
							<div class="usage-bar">
								<div 
									class="usage-bar-fill"
									style="width: {getUsagePercentage(usage.playbooks_count, usage.playbooks_limit)}%"
									class:warning={getUsagePercentage(usage.playbooks_count, usage.playbooks_limit) > 80}
								/>
							</div>
						{/if}
					</div>
				</div>
				
				<div class="usage-period">
					Usage period: {formatDate(usage.period_start)} - {formatDate(usage.period_end)}
				</div>
			</div>
		{/if}
		
		<!-- Need More? -->
		{#if !subscription || subscription.plan_id.includes('free')}
			<div class="upgrade-prompt card">
				<h3>Need more features?</h3>
				<p>Upgrade to Pro for unlimited trades, advanced analytics, and real-time data.</p>
				<a href="/pricing" class="upgrade-button">
					View Plans
					<ExternalLink size={16} />
				</a>
			</div>
		{/if}
	{/if}
</div>

<style>
	.billing-page {
		max-width: 1000px;
		margin: 0 auto;
		padding-bottom: 4rem;
	}
	
	.page-header {
		margin-bottom: 2rem;
	}
	
	.page-header h1 {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}
	
	.page-header p {
		color: #666;
	}
	
	.loading {
		text-align: center;
		padding: 4rem;
		color: #666;
	}
	
	.error-message {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: #fee;
		color: #dc2626;
		padding: 1rem;
		border-radius: 8px;
		margin-bottom: 2rem;
	}
	
	.billing-section {
		margin-bottom: 3rem;
	}
	
	.billing-section h2 {
		font-size: 1.5rem;
		margin-bottom: 1rem;
	}
	
	/* Plan Card */
	.plan-card {
		padding: 2rem;
	}
	
	.plan-info {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1.5rem;
	}
	
	.plan-info h3 {
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}
	
	.plan-price {
		font-size: 2rem;
		font-weight: 700;
		color: #10b981;
		margin-bottom: 0.5rem;
	}
	
	.plan-description {
		color: #666;
	}
	
	.plan-status {
		margin-top: 0.5rem;
	}
	
	.status-badge {
		display: inline-block;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.875rem;
		font-weight: 500;
		background: #fee;
		color: #dc2626;
		text-transform: capitalize;
	}
	
	.status-badge.active {
		background: #d1fae5;
		color: #059669;
	}
	
	.plan-actions {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.manage-button,
	.cancel-button,
	.resume-button,
	.upgrade-button {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
		text-decoration: none;
	}
	
	.manage-button {
		background: #3b82f6;
		color: white;
	}
	
	.manage-button:hover {
		background: #2563eb;
	}
	
	.cancel-button {
		background: #fee;
		color: #dc2626;
	}
	
	.cancel-button:hover {
		background: #fecaca;
	}
	
	.resume-button {
		background: #10b981;
		color: white;
	}
	
	.resume-button:hover {
		background: #059669;
	}
	
	.upgrade-button {
		background: #10b981;
		color: white;
		justify-content: center;
	}
	
	.upgrade-button:hover {
		background: #059669;
	}
	
	.billing-dates {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		padding-top: 1.5rem;
		border-top: 1px solid #e0e0e0;
	}
	
	.date-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		color: #666;
	}
	
	.date-item.warning {
		color: #dc4a26;
	}
	
	/* Usage Grid */
	.usage-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
		margin-bottom: 1rem;
	}
	
	.usage-card {
		padding: 1.5rem;
	}
	
	.usage-card h3 {
		font-size: 1rem;
		margin-bottom: 1rem;
		color: #666;
	}
	
	.usage-stats {
		display: flex;
		align-items: baseline;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}
	
	.usage-current {
		font-size: 2rem;
		font-weight: 700;
		color: #333;
	}
	
	.usage-separator {
		font-size: 1.5rem;
		color: #999;
	}
	
	.usage-limit {
		font-size: 1.5rem;
		color: #666;
	}
	
	.usage-bar {
		height: 8px;
		background: #e5e7eb;
		border-radius: 4px;
		overflow: hidden;
	}
	
	.usage-bar-fill {
		height: 100%;
		background: #10b981;
		transition: width 0.3s;
	}
	
	.usage-bar-fill.warning {
		background: #f59e0b;
	}
	
	.usage-period {
		font-size: 0.875rem;
		color: #666;
		text-align: center;
		margin-top: 1rem;
	}
	
	/* Upgrade Prompt */
	.upgrade-prompt {
		text-align: center;
		padding: 2rem;
		background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
		border: 2px solid #10b981;
	}
	
	.upgrade-prompt h3 {
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
	}
	
	.upgrade-prompt p {
		color: #666;
		margin-bottom: 1.5rem;
	}
	
	@media (max-width: 768px) {
		.plan-info {
			flex-direction: column;
			gap: 1.5rem;
		}
		
		.plan-actions {
			width: 100%;
		}
		
		.usage-grid {
			grid-template-columns: 1fr;
		}
	}
</style>