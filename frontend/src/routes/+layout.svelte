<script lang="ts">
	import './styles.css';
	import { auth, isAuthenticated } from '$lib/api/auth';
	import { goto } from '$app/navigation';
	import WebSocketStatus from '$lib/components/WebSocketStatus.svelte';
	import MobileNav from '$lib/components/MobileNav.svelte';
	import PWAInstallPrompt from '$lib/components/PWAInstallPrompt.svelte';
	import NotificationCenter from '$lib/components/NotificationCenter.svelte';
	import Footer from '$lib/components/Footer.svelte';
	import EmailVerificationBanner from '$lib/components/EmailVerificationBanner.svelte';
	import GlobalSearch from '$lib/components/GlobalSearch.svelte';
	
	let authState: any = { user: null, loading: true, error: null };
	
	auth.subscribe(state => {
		authState = state;
	});
	
	async function handleLogout() {
		await auth.logout();
		goto('/login');
	}
</script>

<div class="app" class:authenticated={$isAuthenticated}>
	<header>
		<nav>
			<a href="/" class="logo">TradeSense</a>
			<div class="nav-links">
				{#if $isAuthenticated}
					<a href="/dashboard">Dashboard</a>
					<a href="/tradelog">Trade Log</a>
					<a href="/portfolio">Portfolio</a>
					<a href="/upload">Import</a>
					<a href="/journal">Journal</a>
					<a href="/analytics">Analytics</a>
					<a href="/playbook">Playbook</a>
					<div class="nav-divider"></div>
					<GlobalSearch />
					<div class="nav-divider"></div>
					<WebSocketStatus />
					<NotificationCenter />
					<div class="nav-divider"></div>
					<span class="username">{authState?.user?.username || ''}</span>
					<button on:click={handleLogout} class="logout-button">Logout</button>
				{:else}
					<a href="/pricing">Pricing</a>
					<a href="/login">Login</a>
					<a href="/register" class="register-button">Sign Up</a>
				{/if}
			</div>
		</nav>
	</header>
	
	{#if $isAuthenticated && authState.user}
		<EmailVerificationBanner user={authState.user} />
	{/if}

	<main>
		<slot />
	</main>
	
	{#if !$isAuthenticated}
		<Footer />
	{/if}
	
	<MobileNav />
	<PWAInstallPrompt />
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
	}

	.nav-links {
		display: flex;
		gap: 2rem;
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
		background: transparent;
		border: 1px solid rgba(255, 255, 255, 0.3);
		color: white;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.logout-button:hover {
		background: rgba(255, 255, 255, 0.1);
		border-color: rgba(255, 255, 255, 0.5);
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