<script lang="ts">
	import './styles.css';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import WebSocketStatus from '$lib/components/WebSocketStatus.svelte';
	import MobileNav from '$lib/components/MobileNav.svelte';
	import PWAInstallPrompt from '$lib/components/PWAInstallPrompt.svelte';
	import NotificationCenter from '$lib/components/NotificationCenter.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import EmailVerificationBanner from '$lib/components/EmailVerificationBanner.svelte';
	import GlobalSearch from '$lib/components/GlobalSearch.svelte';
	import FeedbackButton from '$lib/components/FeedbackButton.svelte';
	import BackendStatus from '$lib/components/BackendStatus.svelte';
	import SkipLinks from '$lib/components/SkipLinks.svelte';
	import LanguageSwitcher from '$lib/components/LanguageSwitcher.svelte';
	import { trackPageVisit } from '$lib/utils/feedbackContext';
	import { authStore, isAuthenticated } from '$lib/stores/auth';
	import { websocket } from '$lib/stores/websocket';
	import { requestNotificationPermission } from '$lib/stores/notifications';
	import { ensureFocusVisible, manageFocus, registerCommonShortcuts } from '$lib/utils/accessibility';
	import { _ } from 'svelte-i18n';
	
	$: authState = $authStore;
	
	// Initialize browser-only features
	onMount(() => {
		// Initialize auth store
		authStore.initialize();
		
		// Connect WebSocket
		websocket.connect();
		
		// Setup accessibility features
		ensureFocusVisible();
		registerCommonShortcuts();
		
		// Request notification permission after user interaction
		// We don't do it immediately to avoid annoying users
		return () => {
			// Cleanup WebSocket on unmount
			websocket.disconnect();
		};
	});
	
	async function handleLogout() {
		await authStore.logout();
		// Navigation is handled by the logout function
	}
	
	// Track page visits for feedback context
	$: if ($page.url.pathname && browser) {
		trackPageVisit($page.url.pathname);
		// Manage focus for screen readers on route change
		manageFocus();
	}
</script>

<div class="app" class:authenticated={$isAuthenticated}>
	<SkipLinks />
	<BackendStatus />
	<header role="banner">
		<nav id="navigation" aria-label="Main navigation">
			<a href="/" class="logo" aria-label="{$_('common.app.name')} - Home">{$_('common.app.name')}</a>
			<div class="nav-links">
				{#if $isAuthenticated}
					<a href="/dashboard">{$_('common.nav.dashboard')}</a>
					<a href="/dashboards">Custom Dashboards</a>
					<a href="/tradelog">{$_('common.nav.trades')}</a>
					<a href="/portfolio">{$_('common.nav.portfolio')}</a>
					<a href="/upload">{$_('common.nav.import')}</a>
					<a href="/journal">{$_('common.nav.journal')}</a>
					<a href="/analytics">{$_('common.nav.analytics')}</a>
					<a href="/ai-insights">{$_('common.nav.aiInsights')}</a>
					<a href="/playbook">{$_('common.nav.playbook')}</a>
					<div class="nav-divider"></div>
					<GlobalSearch />
					<div class="nav-divider"></div>
					<WebSocketStatus />
					<NotificationCenter />
					<div class="nav-divider"></div>
					<span class="username">{authState?.user?.name || authState?.user?.email || ''}</span>
					<LanguageSwitcher />
					<button on:click={handleLogout} class="logout-button" aria-label="{$_('common.nav.logout')} from {$_('common.app.name')}">{$_('common.nav.logout')}</button>
				{:else}
					<a href="/pricing">Pricing</a>
					<LanguageSwitcher />
					<a href="/login">{$_('common.nav.login')}</a>
					<a href="/register" class="register-button">{$_('common.nav.register')}</a>
				{/if}
			</div>
		</nav>
	</header>
	
	{#if $isAuthenticated && authState.user}
		<EmailVerificationBanner user={authState.user} />
	{/if}

	<main id="main-content" role="main">
		<slot />
	</main>
	
	{#if !$isAuthenticated}
		<Footer />
	{/if}
	
	<MobileNav />
	<PWAInstallPrompt />
	<FeedbackButton />
</div>

<style>
	.app {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
	}

	header {
		background: #1a1a1a;
		color: white;
		padding: 1rem 0;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
	}

	nav {
		max-width: 1200px;
		margin: 0 auto;
		padding: 0 2rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.logo {
		font-size: 1.5rem;
		font-weight: bold;
		color: white;
		text-decoration: none;
		margin-right: 3rem;
	}

	.nav-links {
		display: flex;
		gap: 1.5rem;
		align-items: center;
	}

	.nav-links a {
		color: white;
		text-decoration: none;
		transition: opacity 0.2s;
	}

	.nav-links a:hover {
		opacity: 0.8;
	}

	main {
		flex: 1;
		background: #f5f5f5;
		padding: 2rem;
		max-width: 1200px;
		margin: 0 auto;
		width: 100%;
		box-sizing: border-box;
	}
	
	.nav-divider {
		width: 1px;
		height: 20px;
		background: rgba(255, 255, 255, 0.3);
		margin: 0 1rem;
	}
	
	.username {
		color: rgba(255, 255, 255, 0.9);
		font-weight: 500;
	}
	
	.logout-button {
		background: rgba(239, 68, 68, 0.1);
		border: 1px solid rgba(239, 68, 68, 0.3);
		color: #ef4444;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.logout-button:hover {
		background: rgba(239, 68, 68, 0.2);
		border-color: rgba(239, 68, 68, 0.5);
	}
	
	.register-button {
		background: #10b981;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		transition: background 0.2s;
	}
	
	.register-button:hover {
		background: #059669;
	}
	
	/* Medium screens */
	@media (max-width: 1200px) {
		.nav-links {
			gap: 1rem;
		}
		
		.logo {
			margin-right: 2rem;
		}
		
		.nav-links a {
			font-size: 0.875rem;
		}
	}
	
	/* Mobile Styles */
	@media (max-width: 768px) {
		header {
			display: none;
		}
		
		main {
			padding: 1rem;
			padding-bottom: 80px; /* Space for mobile nav */
		}
		
		/* Add top padding when not authenticated (for mobile header) */
		.app:not(.authenticated) main {
			padding-top: 4rem;
		}
	}
</style>