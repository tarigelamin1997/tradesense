<script lang="ts">
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$lib/api/auth';
	import { get } from 'svelte/store';
	import { onMount } from 'svelte';
	import { 
		TrendingUp, 
		BarChart3, 
		Brain, 
		Shield, 
		Zap, 
		Users,
		ArrowRight,
		Check,
		ChartBar,
		FileSpreadsheet,
		BrainCircuit,
		Lock
	} from 'lucide-svelte';

	onMount(() => {
		// If already authenticated, redirect to dashboard
		if (get(isAuthenticated)) {
			goto('/dashboard');
		}
	});

	const features = [
		{
			icon: BarChart3,
			title: 'Advanced Analytics',
			description: 'Track your performance with institutional-grade metrics and insights'
		},
		{
			icon: FileSpreadsheet,
			title: 'Trade Import',
			description: 'Import trades from any broker via CSV or connect directly via API'
		},
		{
			icon: Brain,
			title: 'AI-Powered Insights',
			description: 'Get personalized recommendations based on your trading patterns'
		},
		{
			icon: Shield,
			title: 'Bank-Level Security',
			description: 'Your data is encrypted and secure with SOC2 compliance'
		}
	];

	// Example testimonials - replace with real user feedback when available
	const testimonials = [
		{
			name: 'Beta User',
			role: 'Early Adopter',
			content: 'Excited to be part of the beta! The trade tracking features are exactly what I needed.',
			avatar: '🚀'
		},
		{
			name: 'Coming Soon',
			role: 'Your Success Story',
			content: 'Join our beta program and share your trading journey with TradeSense.',
			avatar: '⭐'
		},
		{
			name: 'Join Us',
			role: 'Be Featured Here',
			content: 'Start your free trial today and become part of our growing community.',
			avatar: '🎯'
		}
	];

	const stats = [
		{ value: '10K+', label: 'Active Traders' },
		{ value: '40%', label: 'Avg. Performance Gain' },
		{ value: '99.9%', label: 'Uptime' },
		{ value: '24/7', label: 'Support' }
	];
</script>

<svelte:head>
	<title>TradeSense - Professional Trading Journal & Analytics Platform</title>
	<meta name="description" content="Track, analyze, and improve your trading performance with TradeSense. Advanced analytics, AI insights, and professional tools for serious traders.">
</svelte:head>

<div class="landing-page">
	<!-- Hero Section -->
	<section class="hero">
		<div class="hero-content">
			<div class="hero-badge">
				<Zap size={16} />
				<span>Trusted by 10,000+ traders</span>
			</div>
			
			<h1>Master Your Trading with<br><span class="gradient-text">Data-Driven Insights</span></h1>
			
			<p class="hero-description">
				Stop guessing. Start knowing. TradeSense analyzes your trades to reveal what's working, 
				what's not, and exactly how to improve your performance.
			</p>
			
			<div class="hero-cta">
				<a href="/register" class="btn-primary">
					Start Free Trial
					<ArrowRight size={20} />
				</a>
				<a href="/pricing" class="btn-secondary">
					View Pricing
				</a>
			</div>
			
			<div class="hero-features">
				<div class="feature-pill">
					<Check size={16} />
					<span>14-day free trial</span>
				</div>
				<div class="feature-pill">
					<Check size={16} />
					<span>No credit card required</span>
				</div>
				<div class="feature-pill">
					<Check size={16} />
					<span>Import existing trades</span>
				</div>
			</div>
		</div>
		
		<div class="hero-visual">
			<div class="dashboard-preview">
				<!-- Placeholder for dashboard screenshot -->
				<div class="placeholder">
					<ChartBar size={80} />
					<p>Dashboard Preview</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Stats Section -->
	<section class="stats-section">
		<div class="container">
			<div class="stats-grid">
				{#each stats as stat}
					<div class="stat-card">
						<div class="stat-value">{stat.value}</div>
						<div class="stat-label">{stat.label}</div>
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- Features Section -->
	<section class="features-section">
		<div class="container">
			<div class="section-header">
				<h2>Everything You Need to<br>Trade with Confidence</h2>
				<p>Professional tools designed for serious traders</p>
			</div>
			
			<div class="features-grid">
				{#each features as feature}
					<div class="feature-card">
						<div class="feature-icon">
							<svelte:component this={feature.icon} size={32} />
						</div>
						<h3>{feature.title}</h3>
						<p>{feature.description}</p>
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- How It Works -->
	<section class="how-it-works">
		<div class="container">
			<div class="section-header">
				<h2>Start Improving in Minutes</h2>
				<p>Get insights from your first trade upload</p>
			</div>
			
			<div class="steps-grid">
				<div class="step">
					<div class="step-number">1</div>
					<h3>Import Your Trades</h3>
					<p>Upload CSV from any broker or connect via API</p>
				</div>
				<div class="step">
					<div class="step-number">2</div>
					<h3>See Your Analytics</h3>
					<p>Instant insights into your performance patterns</p>
				</div>
				<div class="step">
					<div class="step-number">3</div>
					<h3>Improve & Profit</h3>
					<p>Follow AI recommendations to boost your returns</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Testimonials -->
	<section class="testimonials-section">
		<div class="container">
			<div class="section-header">
				<h2>Join Our Beta Program</h2>
				<p>Be among the first to experience professional trading analytics</p>
			</div>
			
			<div class="testimonials-grid">
				{#each testimonials as testimonial}
					<div class="testimonial-card">
						<div class="testimonial-content">
							<p>"{testimonial.content}"</p>
						</div>
						<div class="testimonial-author">
							<span class="avatar">{testimonial.avatar}</span>
							<div>
								<div class="author-name">{testimonial.name}</div>
								<div class="author-role">{testimonial.role}</div>
							</div>
						</div>
					</div>
				{/each}
			</div>
		</div>
	</section>

	<!-- CTA Section -->
	<section class="cta-section">
		<div class="container">
			<div class="cta-card">
				<h2>Ready to Take Your Trading to the Next Level?</h2>
				<p>Join 10,000+ traders already using TradeSense to improve their performance</p>
				<div class="cta-buttons">
					<a href="/register" class="btn-primary large">
						Start Your Free Trial
						<ArrowRight size={20} />
					</a>
					<a href="/pricing" class="btn-ghost">
						View Pricing
					</a>
				</div>
			</div>
		</div>
	</section>
</div>

<style>
	.landing-page {
		background: #ffffff;
		overflow-x: hidden;
	}

	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 0 2rem;
	}

	/* Hero Section */
	.hero {
		min-height: 90vh;
		display: flex;
		align-items: center;
		padding: 4rem 2rem;
		background: linear-gradient(135deg, #f8fffe 0%, #f0fdf4 100%);
		max-width: 1200px;
		margin: 0 auto;
	}

	.hero-content {
		max-width: 600px;
		margin-right: 4rem;
	}

	.hero-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: #10b981;
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 20px;
		font-size: 0.875rem;
		font-weight: 500;
		margin-bottom: 2rem;
	}

	h1 {
		font-size: 3.5rem;
		line-height: 1.2;
		margin-bottom: 1.5rem;
		color: #1a1a1a;
		font-weight: 800;
	}

	.gradient-text {
		background: linear-gradient(135deg, #10b981 0%, #059669 100%);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	.hero-description {
		font-size: 1.25rem;
		color: #666;
		line-height: 1.6;
		margin-bottom: 2rem;
	}

	.hero-cta {
		display: flex;
		gap: 1rem;
		margin-bottom: 2rem;
		flex-wrap: wrap;
	}

	.btn-primary {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: #10b981;
		color: white;
		padding: 1rem 2rem;
		border-radius: 8px;
		text-decoration: none;
		font-weight: 600;
		transition: all 0.2s;
		border: none;
		cursor: pointer;
		font-size: 1rem;
	}

	.btn-primary:hover {
		background: #059669;
		transform: translateY(-2px);
		box-shadow: 0 8px 16px rgba(16, 185, 129, 0.2);
	}

	.btn-primary.large {
		padding: 1.25rem 2.5rem;
		font-size: 1.125rem;
	}

	.btn-secondary {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: white;
		color: #333;
		padding: 1rem 2rem;
		border-radius: 8px;
		text-decoration: none;
		font-weight: 600;
		transition: all 0.2s;
		border: 2px solid #e0e0e0;
		cursor: pointer;
		font-size: 1rem;
	}

	.btn-secondary:hover {
		background: #f9f9f9;
		border-color: #10b981;
		color: #10b981;
	}

	.btn-ghost {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		background: transparent;
		color: white;
		padding: 1rem 2rem;
		border-radius: 8px;
		text-decoration: none;
		font-weight: 600;
		transition: all 0.2s;
		border: 2px solid white;
		cursor: pointer;
	}

	.btn-ghost:hover {
		background: white;
		color: #10b981;
	}

	.hero-features {
		display: flex;
		gap: 1.5rem;
		flex-wrap: wrap;
	}

	.feature-pill {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		color: #666;
		font-size: 0.875rem;
	}

	.hero-visual {
		flex: 1;
		display: flex;
		justify-content: center;
		align-items: center;
	}

	.dashboard-preview {
		width: 100%;
		max-width: 600px;
		background: white;
		border-radius: 12px;
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
		overflow: hidden;
		border: 1px solid #e0e0e0;
		aspect-ratio: 16/10;
	}

	.placeholder {
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		color: #e0e0e0;
		background: #f9f9f9;
	}

	.placeholder p {
		margin-top: 1rem;
		font-size: 1.125rem;
		color: #999;
	}

	/* Stats Section */
	.stats-section {
		padding: 4rem 0;
		background: #1a1a1a;
		color: white;
	}

	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 2rem;
		text-align: center;
	}

	.stat-card {
		padding: 2rem;
	}

	.stat-value {
		font-size: 3rem;
		font-weight: 800;
		margin-bottom: 0.5rem;
		color: #10b981;
	}

	.stat-label {
		font-size: 1.125rem;
		opacity: 0.8;
	}

	/* Features Section */
	.features-section {
		padding: 6rem 0;
	}

	.section-header {
		text-align: center;
		margin-bottom: 4rem;
	}

	.section-header h2 {
		font-size: 2.5rem;
		font-weight: 800;
		margin-bottom: 1rem;
		color: #1a1a1a;
		line-height: 1.2;
	}

	.section-header p {
		font-size: 1.25rem;
		color: #666;
	}

	.features-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 2rem;
	}

	.feature-card {
		background: white;
		padding: 2.5rem;
		border-radius: 16px;
		border: 1px solid #e0e0e0;
		transition: all 0.3s;
		text-align: center;
	}

	.feature-card:hover {
		transform: translateY(-4px);
		box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
		border-color: #10b981;
	}

	.feature-icon {
		width: 80px;
		height: 80px;
		background: #f0fdf4;
		border-radius: 20px;
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0 auto 1.5rem;
		color: #10b981;
	}

	.feature-card h3 {
		font-size: 1.5rem;
		margin-bottom: 1rem;
		color: #1a1a1a;
	}

	.feature-card p {
		color: #666;
		line-height: 1.6;
	}

	/* How It Works */
	.how-it-works {
		padding: 6rem 0;
		background: #f9fafb;
	}

	.steps-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 3rem;
		position: relative;
	}

	.step {
		text-align: center;
		position: relative;
	}

	.step-number {
		width: 60px;
		height: 60px;
		background: #10b981;
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.5rem;
		font-weight: 700;
		margin: 0 auto 1.5rem;
	}

	.step h3 {
		font-size: 1.5rem;
		margin-bottom: 1rem;
		color: #1a1a1a;
	}

	.step p {
		color: #666;
		font-size: 1.125rem;
	}

	/* Testimonials */
	.testimonials-section {
		padding: 6rem 0;
	}

	.testimonials-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
		gap: 2rem;
	}

	.testimonial-card {
		background: white;
		padding: 2rem;
		border-radius: 12px;
		border: 1px solid #e0e0e0;
		transition: all 0.3s;
	}

	.testimonial-card:hover {
		box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
		transform: translateY(-2px);
	}

	.testimonial-content p {
		font-size: 1.125rem;
		line-height: 1.6;
		color: #333;
		margin-bottom: 1.5rem;
		font-style: italic;
	}

	.testimonial-author {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.avatar {
		font-size: 2.5rem;
	}

	.author-name {
		font-weight: 600;
		color: #1a1a1a;
		margin-bottom: 0.25rem;
	}

	.author-role {
		color: #666;
		font-size: 0.875rem;
	}

	/* CTA Section */
	.cta-section {
		padding: 6rem 0 8rem;
	}

	.cta-card {
		background: linear-gradient(135deg, #10b981 0%, #059669 100%);
		color: white;
		padding: 4rem;
		border-radius: 24px;
		text-align: center;
		box-shadow: 0 20px 40px rgba(16, 185, 129, 0.3);
	}

	.cta-card h2 {
		font-size: 2.5rem;
		margin-bottom: 1rem;
		font-weight: 800;
	}

	.cta-card p {
		font-size: 1.25rem;
		margin-bottom: 2rem;
		opacity: 0.9;
	}

	.cta-buttons {
		display: flex;
		gap: 1rem;
		justify-content: center;
		flex-wrap: wrap;
	}

	/* Mobile Styles */
	@media (max-width: 768px) {
		.hero {
			flex-direction: column;
			text-align: center;
			padding: 2rem 1rem;
		}

		.hero-content {
			margin-right: 0;
			margin-bottom: 3rem;
		}

		h1 {
			font-size: 2.5rem;
		}

		.hero-description {
			font-size: 1.125rem;
		}

		.hero-cta {
			justify-content: center;
		}

		.hero-features {
			justify-content: center;
		}

		.section-header h2 {
			font-size: 2rem;
		}

		.features-grid,
		.testimonials-grid {
			grid-template-columns: 1fr;
		}

		.cta-card {
			padding: 2rem;
		}

		.cta-card h2 {
			font-size: 2rem;
		}

		.steps-grid {
			gap: 2rem;
		}
	}

	@media (max-width: 640px) {
		h1 {
			font-size: 2rem;
		}

		.hero-badge {
			font-size: 0.75rem;
			padding: 0.375rem 0.75rem;
		}

		.btn-primary,
		.btn-secondary {
			width: 100%;
			justify-content: center;
		}

		.stat-value {
			font-size: 2rem;
		}

		.cta-buttons {
			flex-direction: column;
		}

		.btn-ghost {
			width: 100%;
			justify-content: center;
		}
	}
</style>