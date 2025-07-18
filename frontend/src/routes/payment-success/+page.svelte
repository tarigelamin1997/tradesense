<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { CheckCircle, ArrowRight, Sparkles } from 'lucide-svelte';
	
	let countdown = 5;
	let interval: number;
	
	onMount(() => {
		// Start countdown
		interval = setInterval(() => {
			countdown--;
			if (countdown <= 0) {
				clearInterval(interval);
				goto('/dashboard');
			}
		}, 1000);
		
		return () => {
			if (interval) clearInterval(interval);
		};
	});
</script>

<svelte:head>
	<title>Payment Successful - TradeSense</title>
</svelte:head>

<div class="success-page">
	<div class="success-container">
		<div class="success-icon">
			<CheckCircle size={64} />
		</div>
		
		<h1>Welcome to TradeSense Pro!</h1>
		<p class="success-message">
			Your payment was successful and your account has been upgraded.
		</p>
		
		<div class="features-unlocked">
			<h3><Sparkles size={20} /> You've unlocked:</h3>
			<ul>
				<li>Unlimited trade tracking</li>
				<li>Advanced analytics and insights</li>
				<li>Real-time data synchronization</li>
				<li>Priority customer support</li>
			</ul>
		</div>
		
		<div class="next-steps">
			<h3>What's next?</h3>
			<p>Start by importing your trades or creating your first trade entry.</p>
		</div>
		
		<div class="redirect-info">
			Redirecting to dashboard in {countdown} seconds...
		</div>
		
		<a href="/dashboard" class="dashboard-button">
			Go to Dashboard
			<ArrowRight size={20} />
		</a>
	</div>
</div>

<style>
	.success-page {
		min-height: calc(100vh - 200px);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
	}
	
	.success-container {
		max-width: 600px;
		text-align: center;
		background: white;
		padding: 3rem;
		border-radius: 16px;
		box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
	}
	
	.success-icon {
		color: #10b981;
		margin-bottom: 2rem;
		animation: checkmark 0.6s ease-out;
	}
	
	@keyframes checkmark {
		0% {
			transform: scale(0) rotate(-45deg);
			opacity: 0;
		}
		50% {
			transform: scale(1.2) rotate(0deg);
		}
		100% {
			transform: scale(1) rotate(0deg);
			opacity: 1;
		}
	}
	
	h1 {
		font-size: 2.5rem;
		margin-bottom: 1rem;
		color: #1a1a1a;
	}
	
	.success-message {
		font-size: 1.25rem;
		color: #666;
		margin-bottom: 2rem;
	}
	
	.features-unlocked {
		background: #f0fdf4;
		padding: 1.5rem;
		border-radius: 12px;
		margin-bottom: 2rem;
		text-align: left;
	}
	
	.features-unlocked h3 {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		color: #10b981;
		margin-bottom: 1rem;
	}
	
	.features-unlocked ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	
	.features-unlocked li {
		padding: 0.5rem 0;
		padding-left: 1.5rem;
		position: relative;
		color: #333;
	}
	
	.features-unlocked li::before {
		content: '✓';
		position: absolute;
		left: 0;
		color: #10b981;
		font-weight: bold;
	}
	
	.next-steps {
		margin-bottom: 2rem;
	}
	
	.next-steps h3 {
		margin-bottom: 0.5rem;
		color: #333;
	}
	
	.next-steps p {
		color: #666;
	}
	
	.redirect-info {
		font-size: 0.875rem;
		color: #999;
		margin-bottom: 2rem;
	}
	
	.dashboard-button {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 1rem 2rem;
		background: #10b981;
		color: white;
		text-decoration: none;
		border-radius: 8px;
		font-weight: 600;
		transition: all 0.2s;
	}
	
	.dashboard-button:hover {
		background: #059669;
		transform: translateX(4px);
	}
	
	@media (max-width: 640px) {
		.success-container {
			padding: 2rem;
		}
		
		h1 {
			font-size: 1.75rem;
		}
		
		.success-message {
			font-size: 1rem;
		}
	}
</style>