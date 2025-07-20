<script lang="ts">
	import { Home, TrendingUp, FileText, BarChart2, Menu, X, User, LogOut, Search } from 'lucide-svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { auth, isAuthenticated } from '$lib/api/auth';
	import GlobalSearch from './GlobalSearch.svelte';
	
	let isMenuOpen = false;
	let authState: any = { user: null, loading: true, error: null };
	
	auth.subscribe(state => {
		authState = state;
	});
	
	async function handleLogout() {
		await auth.logout();
		goto('/login');
		isMenuOpen = false;
	}
	
	function toggleMenu() {
		isMenuOpen = !isMenuOpen;
	}
	
	function closeMenu() {
		isMenuOpen = false;
	}
	
	$: currentPath = $page.url.pathname;
	
	const navItems = [
		{ path: '/dashboard', icon: Home, label: 'Dashboard' },
		{ path: '/tradelog', icon: TrendingUp, label: 'Trades' },
		{ path: '/portfolio', icon: BarChart2, label: 'Portfolio' },
		{ path: '/journal', icon: FileText, label: 'Journal' }
	];
</script>

<!-- Mobile Header for non-authenticated users -->
{#if !$isAuthenticated}
	<div class="mobile-header">
		<a href="/" class="logo">TradeSense</a>
		<button class="menu-toggle" on:click={toggleMenu}>
			<Menu size={24} />
		</button>
	</div>
{/if}

{#if $isAuthenticated}
	<!-- Mobile Bottom Navigation -->
	<nav class="mobile-nav">
		{#each navItems as item}
			<a 
				href={item.path} 
				class="nav-item"
				class:active={currentPath === item.path}
				on:click={closeMenu}
			>
				<svelte:component this={item.icon} size={20} />
				<span>{item.label}</span>
			</a>
		{/each}
		<button class="nav-item menu-button" on:click={toggleMenu}>
			<Menu size={20} />
			<span>Menu</span>
		</button>
	</nav>
	
	<!-- Mobile Menu Overlay -->
	{#if isMenuOpen}
		<button class="menu-overlay" on:click={closeMenu} type="button" aria-label="Close menu overlay">
			<div class="menu-content" on:click|stopPropagation>
				<div class="menu-header">
					<h2>TradeSense</h2>
					<button class="close-button" on:click={closeMenu} aria-label="Close menu">
						<X size={24} />
					</button>
				</div>
				
				{#if $isAuthenticated}
					<div class="user-info">
						<User size={32} />
						<div>
							<p class="username">{authState?.user?.username || 'User'}</p>
							<p class="email">{authState?.user?.email || ''}</p>
						</div>
					</div>
				{/if}
				
				{#if $isAuthenticated}
					<div class="search-container">
						<GlobalSearch />
					</div>
				{/if}
				
				<div class="menu-links">
					{#if $isAuthenticated}
						<a href="/dashboards" on:click={closeMenu}>Custom Dashboards</a>
						<a href="/ai-insights" on:click={closeMenu}>AI Insights</a>
						<a href="/playbook" on:click={closeMenu}>Playbook</a>
						<a href="/upload" on:click={closeMenu}>Import</a>
						<a href="/billing" on:click={closeMenu}>Billing</a>
						<a href="/settings" on:click={closeMenu}>Settings</a>
					{:else}
						<a href="/" on:click={closeMenu}>Home</a>
						<a href="/pricing" on:click={closeMenu}>Pricing</a>
						<a href="/login" on:click={closeMenu}>Login</a>
						<a href="/register" on:click={closeMenu} class="register-link">Sign Up</a>
					{/if}
				</div>
				
				{#if $isAuthenticated}
					<button class="logout-button" on:click={handleLogout}>
						<LogOut size={18} />
						Log Out
					</button>
				{/if}
			</div>
		</button>
	{/if}
{/if}

<style>
	.mobile-nav {
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		background: white;
		border-top: 1px solid #e0e0e0;
		display: none;
		z-index: 100;
		padding-bottom: env(safe-area-inset-bottom);
	}
	
	@media (max-width: 768px) {
		.mobile-nav {
			display: flex;
			justify-content: space-around;
			align-items: center;
			height: 60px;
		}
	}
	
	.nav-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.25rem;
		padding: 0.5rem;
		color: #666;
		text-decoration: none;
		font-size: 0.75rem;
		transition: color 0.2s;
		flex: 1;
		background: none;
		border: none;
		cursor: pointer;
	}
	
	.nav-item:active {
		background: #f3f4f6;
	}
	
	.nav-item.active {
		color: #10b981;
	}
	
	.nav-item span {
		margin-top: 0.125rem;
	}
	
	/* Menu Overlay */
	.menu-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		z-index: 200;
		animation: fadeIn 0.2s;
		border: none;
		padding: 0;
		width: 100%;
		height: 100%;
		cursor: default;
	}
	
	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}
	
	.menu-content {
		position: absolute;
		right: 0;
		top: 0;
		bottom: 0;
		width: 280px;
		max-width: 80vw;
		background: white;
		padding: 1.5rem;
		box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
		animation: slideIn 0.3s;
		display: flex;
		flex-direction: column;
	}
	
	@keyframes slideIn {
		from {
			transform: translateX(100%);
		}
		to {
			transform: translateX(0);
		}
	}
	
	.menu-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
	}
	
	.menu-header h2 {
		font-size: 1.5rem;
		margin: 0;
	}
	
	.close-button {
		background: none;
		border: none;
		color: #666;
		cursor: pointer;
		padding: 0.5rem;
		margin: -0.5rem;
	}
	
	.user-info {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1rem;
		background: #f9fafb;
		border-radius: 8px;
		margin-bottom: 2rem;
	}
	
	.user-info :global(svg) {
		color: #666;
	}
	
	.username {
		font-weight: 600;
		margin-bottom: 0.25rem;
	}
	
	.email {
		font-size: 0.875rem;
		color: #666;
	}
	
	.search-container {
		margin-bottom: 2rem;
	}
	
	/* Override search button styles for mobile nav */
	.search-container :global(.search-trigger) {
		display: flex !important;
		width: 100%;
		background: #f3f4f6;
		border: 1px solid #e5e7eb;
		color: #4b5563;
		justify-content: center;
	}
	
	.search-container :global(.search-trigger:hover) {
		background: #e5e7eb;
		border-color: #d1d5db;
	}
	
	.search-container :global(.search-trigger span) {
		display: inline;
	}
	
	.menu-links {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.menu-links a {
		display: block;
		padding: 0.75rem 1rem;
		color: #333;
		text-decoration: none;
		border-radius: 6px;
		transition: background 0.2s;
	}
	
	.menu-links a:hover {
		background: #f3f4f6;
	}
	
	.logout-button {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.75rem;
		background: #fee;
		color: #dc2626;
		border: none;
		border-radius: 6px;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.2s;
		margin-top: auto;
	}
	
	.logout-button:hover {
		background: #fecaca;
	}
	
	/* Mobile Header */
	.mobile-header {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		background: #1a1a1a;
		color: white;
		padding: 1rem;
		display: none;
		justify-content: space-between;
		align-items: center;
		z-index: 100;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
	}
	
	@media (max-width: 768px) {
		.mobile-header {
			display: flex;
		}
	}
	
	.mobile-header .logo {
		color: white;
		text-decoration: none;
		font-size: 1.25rem;
		font-weight: bold;
	}
	
	.menu-toggle {
		background: none;
		border: none;
		color: white;
		cursor: pointer;
		padding: 0.5rem;
		margin: -0.5rem;
	}
	
	.register-link {
		background: #10b981;
		color: white !important;
		text-align: center;
	}
	
	.register-link:hover {
		background: #059669 !important;
	}
</style>