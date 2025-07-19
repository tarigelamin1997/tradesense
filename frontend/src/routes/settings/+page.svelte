<script lang="ts">
	import { onMount } from 'svelte';
	import { 
		User, 
		Bell, 
		Shield, 
		CreditCard, 
		Moon, 
		Globe, 
		Key,
		Mail,
		Smartphone,
		ChevronRight,
		Check,
		AlertCircle
	} from 'lucide-svelte';
	import { auth } from '$lib/api/auth';
	import { api } from '$lib/api/client';
	import { logger } from '$lib/utils/logger';
	
	let authState: any;
	let loading = false;
	let saveStatus = '';
	let activeSection = 'profile';
	
	// User settings
	let userSettings = {
		username: '',
		email: '',
		firstName: '',
		lastName: '',
		timezone: 'UTC',
		tradingExperience: '',
		preferredMarkets: []
	};
	
	// Notification settings
	let notifications = {
		emailAlerts: true,
		tradeReminders: true,
		weeklyReports: true,
		marketAlerts: false,
		pushNotifications: false
	};
	
	// Display settings
	let displaySettings = {
		theme: 'light',
		compactMode: false,
		showPnLInHeader: true,
		defaultChartType: 'candlestick'
	};
	
	auth.subscribe(state => {
		authState = state;
		if (state.user) {
			userSettings.username = state.user.username || '';
			userSettings.email = state.user.email || '';
			userSettings.firstName = state.user.first_name || '';
			userSettings.lastName = state.user.last_name || '';
			userSettings.timezone = state.user.timezone || 'UTC';
			userSettings.tradingExperience = state.user.trading_experience || '';
			userSettings.preferredMarkets = state.user.preferred_markets || [];
		}
	});
	
	const sections = [
		{ id: 'profile', label: 'Profile', icon: User },
		{ id: 'notifications', label: 'Notifications', icon: Bell },
		{ id: 'display', label: 'Display', icon: Moon },
		{ id: 'security', label: 'Security', icon: Shield },
		{ id: 'billing', label: 'Billing', icon: CreditCard }
	];
	
	const timezones = [
		{ value: 'UTC', label: 'UTC (Universal)' },
		{ value: 'America/New_York', label: 'Eastern Time (US)' },
		{ value: 'America/Chicago', label: 'Central Time (US)' },
		{ value: 'America/Denver', label: 'Mountain Time (US)' },
		{ value: 'America/Los_Angeles', label: 'Pacific Time (US)' },
		{ value: 'Europe/London', label: 'London (UK)' },
		{ value: 'Europe/Paris', label: 'Central European Time' },
		{ value: 'Asia/Tokyo', label: 'Tokyo (Japan)' },
		{ value: 'Asia/Shanghai', label: 'Shanghai (China)' },
		{ value: 'Asia/Singapore', label: 'Singapore' },
		{ value: 'Australia/Sydney', label: 'Sydney (Australia)' }
	];
	
	const markets = [
		'Stocks', 'Options', 'Futures', 'Forex', 'Crypto', 'Bonds', 'Commodities'
	];
	
	async function saveProfile() {
		loading = true;
		saveStatus = '';
		
		try {
			await api.put('/api/v1/auth/me', {
				username: userSettings.username,
				email: userSettings.email,
				first_name: userSettings.firstName,
				last_name: userSettings.lastName,
				timezone: userSettings.timezone,
				trading_experience: userSettings.tradingExperience,
				preferred_markets: userSettings.preferredMarkets
			});
			
			saveStatus = 'Profile updated successfully!';
			
			// Update auth state
			await auth.checkAuth();
			
			setTimeout(() => {
				saveStatus = '';
			}, 3000);
		} catch (error) {
			logger.error('Failed to update profile:', error);
			saveStatus = 'Failed to update profile. Please try again.';
		} finally {
			loading = false;
		}
	}
	
	async function saveNotifications() {
		loading = true;
		saveStatus = '';
		
		try {
			await api.put('/api/v1/settings/notifications', notifications);
			saveStatus = 'Notification settings saved!';
			
			setTimeout(() => {
				saveStatus = '';
			}, 3000);
		} catch (error) {
			logger.error('Failed to save notifications:', error);
			saveStatus = 'Failed to save notification settings.';
		} finally {
			loading = false;
		}
	}
	
	async function saveDisplay() {
		loading = true;
		saveStatus = '';
		
		try {
			await api.put('/api/v1/settings/display', displaySettings);
			saveStatus = 'Display settings saved!';
			
			// Apply theme immediately
			if (displaySettings.theme === 'dark') {
				document.documentElement.classList.add('dark');
			} else {
				document.documentElement.classList.remove('dark');
			}
			
			setTimeout(() => {
				saveStatus = '';
			}, 3000);
		} catch (error) {
			logger.error('Failed to save display settings:', error);
			saveStatus = 'Failed to save display settings.';
		} finally {
			loading = false;
		}
	}
	
	function toggleMarket(market: string) {
		const index = userSettings.preferredMarkets.indexOf(market);
		if (index > -1) {
			userSettings.preferredMarkets = userSettings.preferredMarkets.filter(m => m !== market);
		} else {
			userSettings.preferredMarkets = [...userSettings.preferredMarkets, market];
		}
	}
	
	onMount(async () => {
		// Load saved settings
		try {
			const [notificationSettings, displayPrefs] = await Promise.all([
				api.get('/api/v1/settings/notifications').catch(() => null),
				api.get('/api/v1/settings/display').catch(() => null)
			]);
			
			if (notificationSettings) {
				notifications = { ...notifications, ...notificationSettings };
			}
			
			if (displayPrefs) {
				displaySettings = { ...displaySettings, ...displayPrefs };
			}
		} catch (error) {
			logger.error('Failed to load settings:', error);
		}
	});
</script>

<svelte:head>
	<title>Settings - TradeSense</title>
</svelte:head>

<div class="settings-container">
	<h1>Settings</h1>
	
	<div class="settings-layout">
		<!-- Sidebar Navigation -->
		<aside class="settings-sidebar">
			{#each sections as section}
				<button
					class="sidebar-item"
					class:active={activeSection === section.id}
					on:click={() => activeSection = section.id}
				>
					<svelte:component this={section.icon} size={20} />
					<span>{section.label}</span>
					<ChevronRight size={16} />
				</button>
			{/each}
		</aside>
		
		<!-- Settings Content -->
		<div class="settings-content">
			{#if saveStatus}
				<div class="save-status" class:success={!saveStatus.includes('Failed')}>
					{#if saveStatus.includes('Failed')}
						<AlertCircle size={18} />
					{:else}
						<Check size={18} />
					{/if}
					{saveStatus}
				</div>
			{/if}
			
			<!-- Profile Section -->
			{#if activeSection === 'profile'}
				<section class="settings-section">
					<h2>Profile Settings</h2>
					<p class="section-description">Manage your account information and trading preferences</p>
					
					<div class="form-grid">
						<div class="form-group">
							<label for="username">Username</label>
							<input
								id="username"
								type="text"
								bind:value={userSettings.username}
								disabled={loading}
							/>
						</div>
						
						<div class="form-group">
							<label for="email">Email</label>
							<input
								id="email"
								type="email"
								bind:value={userSettings.email}
								disabled={loading}
							/>
						</div>
						
						<div class="form-group">
							<label for="firstName">First Name</label>
							<input
								id="firstName"
								type="text"
								bind:value={userSettings.firstName}
								disabled={loading}
							/>
						</div>
						
						<div class="form-group">
							<label for="lastName">Last Name</label>
							<input
								id="lastName"
								type="text"
								bind:value={userSettings.lastName}
								disabled={loading}
							/>
						</div>
						
						<div class="form-group full-width">
							<label for="timezone">Timezone</label>
							<select
								id="timezone"
								bind:value={userSettings.timezone}
								disabled={loading}
							>
								{#each timezones as tz}
									<option value={tz.value}>{tz.label}</option>
								{/each}
							</select>
						</div>
						
						<div class="form-group full-width">
							<label for="experience">Trading Experience</label>
							<select
								id="experience"
								bind:value={userSettings.tradingExperience}
								disabled={loading}
							>
								<option value="">Select experience level</option>
								<option value="beginner">Beginner (0-1 years)</option>
								<option value="intermediate">Intermediate (1-5 years)</option>
								<option value="advanced">Advanced (5-10 years)</option>
								<option value="expert">Expert (10+ years)</option>
							</select>
						</div>
					</div>
					
					<div class="form-group">
						<label>Preferred Markets</label>
						<div class="checkbox-grid">
							{#each markets as market}
								<label class="checkbox-label">
									<input
										type="checkbox"
										checked={userSettings.preferredMarkets.includes(market)}
										on:change={() => toggleMarket(market)}
										disabled={loading}
									/>
									<span>{market}</span>
								</label>
							{/each}
						</div>
					</div>
					
					<button
						class="save-button"
						on:click={saveProfile}
						disabled={loading}
					>
						{loading ? 'Saving...' : 'Save Profile'}
					</button>
				</section>
			{/if}
			
			<!-- Notifications Section -->
			{#if activeSection === 'notifications'}
				<section class="settings-section">
					<h2>Notification Settings</h2>
					<p class="section-description">Choose how you want to be notified about your trading activity</p>
					
					<div class="toggle-list">
						<div class="toggle-item">
							<div class="toggle-info">
								<Mail size={20} />
								<div>
									<h3>Email Alerts</h3>
									<p>Receive email notifications for important trading events</p>
								</div>
							</div>
							<label class="toggle">
								<input
									type="checkbox"
									bind:checked={notifications.emailAlerts}
									disabled={loading}
								/>
								<span class="toggle-slider"></span>
							</label>
						</div>
						
						<div class="toggle-item">
							<div class="toggle-info">
								<Bell size={20} />
								<div>
									<h3>Trade Reminders</h3>
									<p>Get reminders to review and journal your trades</p>
								</div>
							</div>
							<label class="toggle">
								<input
									type="checkbox"
									bind:checked={notifications.tradeReminders}
									disabled={loading}
								/>
								<span class="toggle-slider"></span>
							</label>
						</div>
						
						<div class="toggle-item">
							<div class="toggle-info">
								<Globe size={20} />
								<div>
									<h3>Weekly Reports</h3>
									<p>Receive weekly performance summaries</p>
								</div>
							</div>
							<label class="toggle">
								<input
									type="checkbox"
									bind:checked={notifications.weeklyReports}
									disabled={loading}
								/>
								<span class="toggle-slider"></span>
							</label>
						</div>
						
						<div class="toggle-item">
							<div class="toggle-info">
								<AlertCircle size={20} />
								<div>
									<h3>Market Alerts</h3>
									<p>Get notified about significant market movements</p>
								</div>
							</div>
							<label class="toggle">
								<input
									type="checkbox"
									bind:checked={notifications.marketAlerts}
									disabled={loading}
								/>
								<span class="toggle-slider"></span>
							</label>
						</div>
						
						<div class="toggle-item">
							<div class="toggle-info">
								<Smartphone size={20} />
								<div>
									<h3>Push Notifications</h3>
									<p>Enable browser push notifications</p>
								</div>
							</div>
							<label class="toggle">
								<input
									type="checkbox"
									bind:checked={notifications.pushNotifications}
									disabled={loading}
								/>
								<span class="toggle-slider"></span>
							</label>
						</div>
					</div>
					
					<button
						class="save-button"
						on:click={saveNotifications}
						disabled={loading}
					>
						{loading ? 'Saving...' : 'Save Notifications'}
					</button>
				</section>
			{/if}
			
			<!-- Display Section -->
			{#if activeSection === 'display'}
				<section class="settings-section">
					<h2>Display Settings</h2>
					<p class="section-description">Customize how TradeSense looks and feels</p>
					
					<div class="form-group">
						<label for="theme">Theme</label>
						<select
							id="theme"
							bind:value={displaySettings.theme}
							disabled={loading}
						>
							<option value="light">Light</option>
							<option value="dark">Dark</option>
							<option value="auto">Auto (System)</option>
						</select>
					</div>
					
					<div class="toggle-list">
						<div class="toggle-item">
							<div class="toggle-info">
								<div>
									<h3>Compact Mode</h3>
									<p>Show more information with reduced spacing</p>
								</div>
							</div>
							<label class="toggle">
								<input
									type="checkbox"
									bind:checked={displaySettings.compactMode}
									disabled={loading}
								/>
								<span class="toggle-slider"></span>
							</label>
						</div>
						
						<div class="toggle-item">
							<div class="toggle-info">
								<div>
									<h3>Show P&L in Header</h3>
									<p>Display your total P&L in the navigation bar</p>
								</div>
							</div>
							<label class="toggle">
								<input
									type="checkbox"
									bind:checked={displaySettings.showPnLInHeader}
									disabled={loading}
								/>
								<span class="toggle-slider"></span>
							</label>
						</div>
					</div>
					
					<div class="form-group">
						<label for="chartType">Default Chart Type</label>
						<select
							id="chartType"
							bind:value={displaySettings.defaultChartType}
							disabled={loading}
						>
							<option value="candlestick">Candlestick</option>
							<option value="line">Line</option>
							<option value="bar">Bar</option>
							<option value="area">Area</option>
						</select>
					</div>
					
					<button
						class="save-button"
						on:click={saveDisplay}
						disabled={loading}
					>
						{loading ? 'Saving...' : 'Save Display Settings'}
					</button>
				</section>
			{/if}
			
			<!-- Security Section -->
			{#if activeSection === 'security'}
				<section class="settings-section">
					<h2>Security Settings</h2>
					<p class="section-description">Keep your account secure</p>
					
					<div class="security-options">
						<a href="/change-password" class="security-option">
							<Key size={24} />
							<div>
								<h3>Change Password</h3>
								<p>Update your account password</p>
							</div>
							<ChevronRight size={20} />
						</a>
						
						<div class="security-option disabled">
							<Shield size={24} />
							<div>
								<h3>Two-Factor Authentication</h3>
								<p>Coming soon - Add an extra layer of security</p>
							</div>
						</div>
						
						<div class="security-info">
							<h3>Recent Activity</h3>
							<p>Last login: {new Date().toLocaleString()}</p>
							<p>IP Address: 192.168.1.1</p>
						</div>
					</div>
				</section>
			{/if}
			
			<!-- Billing Section -->
			{#if activeSection === 'billing'}
				<section class="settings-section">
					<h2>Billing & Subscription</h2>
					<p class="section-description">Manage your subscription and payment methods</p>
					
					<div class="subscription-card">
						<h3>Current Plan</h3>
						<div class="plan-info">
							<span class="plan-name">Free Plan</span>
							<span class="plan-status">Active</span>
						</div>
						<p>You're currently on the free plan with limited features.</p>
						<a href="/pricing" class="upgrade-button">
							Upgrade to Pro
						</a>
					</div>
					
					<div class="billing-info">
						<h3>Payment Method</h3>
						<p class="no-payment">No payment method on file</p>
						<button class="add-payment-button" disabled>
							<CreditCard size={18} />
							Add Payment Method
						</button>
					</div>
				</section>
			{/if}
		</div>
	</div>
</div>

<style>
	.settings-container {
		max-width: 1200px;
		margin: 0 auto;
	}
	
	h1 {
		font-size: 2rem;
		margin-bottom: 2rem;
		color: #1a1a1a;
	}
	
	.settings-layout {
		display: grid;
		grid-template-columns: 250px 1fr;
		gap: 2rem;
		align-items: start;
	}
	
	/* Sidebar */
	.settings-sidebar {
		background: white;
		border-radius: 12px;
		padding: 0.5rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		position: sticky;
		top: 2rem;
	}
	
	.sidebar-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		width: 100%;
		padding: 0.875rem 1rem;
		background: none;
		border: none;
		border-radius: 8px;
		color: #4b5563;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
		text-align: left;
	}
	
	.sidebar-item:hover {
		background: #f3f4f6;
		color: #1a1a1a;
	}
	
	.sidebar-item.active {
		background: #10b981;
		color: white;
	}
	
	.sidebar-item :global(svg:last-child) {
		margin-left: auto;
		opacity: 0.5;
	}
	
	/* Content */
	.settings-content {
		background: white;
		border-radius: 12px;
		padding: 2rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
	
	.settings-section h2 {
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
		color: #1a1a1a;
	}
	
	.section-description {
		color: #6b7280;
		margin-bottom: 2rem;
	}
	
	/* Forms */
	.form-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.form-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.form-group.full-width {
		grid-column: 1 / -1;
	}
	
	label {
		font-size: 0.875rem;
		font-weight: 500;
		color: #374151;
	}
	
	input,
	select {
		padding: 0.75rem;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		font-size: 1rem;
		transition: border-color 0.2s;
		background: white;
	}
	
	input:focus,
	select:focus {
		outline: none;
		border-color: #10b981;
	}
	
	input:disabled,
	select:disabled {
		background: #f9fafb;
		cursor: not-allowed;
	}
	
	/* Checkboxes */
	.checkbox-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		gap: 1rem;
	}
	
	.checkbox-label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
		font-size: 0.875rem;
		color: #4b5563;
	}
	
	.checkbox-label input {
		width: auto;
	}
	
	/* Toggle Switches */
	.toggle-list {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
		margin-bottom: 2rem;
	}
	
	.toggle-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		background: #f9fafb;
		border-radius: 8px;
	}
	
	.toggle-info {
		display: flex;
		gap: 1rem;
		align-items: start;
	}
	
	.toggle-info :global(svg) {
		color: #6b7280;
		margin-top: 0.25rem;
	}
	
	.toggle-info h3 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 0.25rem;
		color: #1a1a1a;
	}
	
	.toggle-info p {
		font-size: 0.875rem;
		color: #6b7280;
		margin: 0;
	}
	
	.toggle {
		position: relative;
		display: inline-block;
		width: 48px;
		height: 24px;
	}
	
	.toggle input {
		opacity: 0;
		width: 0;
		height: 0;
	}
	
	.toggle-slider {
		position: absolute;
		cursor: pointer;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: #d1d5db;
		transition: 0.3s;
		border-radius: 24px;
	}
	
	.toggle-slider:before {
		position: absolute;
		content: "";
		height: 18px;
		width: 18px;
		left: 3px;
		bottom: 3px;
		background-color: white;
		transition: 0.3s;
		border-radius: 50%;
	}
	
	.toggle input:checked + .toggle-slider {
		background-color: #10b981;
	}
	
	.toggle input:checked + .toggle-slider:before {
		transform: translateX(24px);
	}
	
	/* Buttons */
	.save-button {
		background: #10b981;
		color: white;
		padding: 0.875rem 2rem;
		border: none;
		border-radius: 6px;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.2s;
	}
	
	.save-button:hover:not(:disabled) {
		background: #059669;
	}
	
	.save-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	/* Save Status */
	.save-status {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		margin-bottom: 1.5rem;
		background: #fee;
		color: #dc2626;
		border-radius: 6px;
		font-size: 0.875rem;
		animation: slideDown 0.3s ease-out;
	}
	
	.save-status.success {
		background: #d1fae5;
		color: #065f46;
	}
	
	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	
	/* Security Section */
	.security-options {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
	
	.security-option {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 1.5rem;
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		text-decoration: none;
		color: #1a1a1a;
		transition: all 0.2s;
	}
	
	.security-option:hover:not(.disabled) {
		background: #f3f4f6;
		border-color: #d1d5db;
		transform: translateX(4px);
	}
	
	.security-option.disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.security-option :global(svg:first-child) {
		color: #6b7280;
	}
	
	.security-option h3 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 0.25rem;
	}
	
	.security-option p {
		font-size: 0.875rem;
		color: #6b7280;
		margin: 0;
	}
	
	.security-option :global(svg:last-child) {
		margin-left: auto;
		color: #9ca3af;
	}
	
	.security-info {
		margin-top: 2rem;
		padding: 1.5rem;
		background: #f9fafb;
		border-radius: 8px;
	}
	
	.security-info h3 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 1rem;
		color: #1a1a1a;
	}
	
	.security-info p {
		font-size: 0.875rem;
		color: #6b7280;
		margin: 0.5rem 0;
	}
	
	/* Billing Section */
	.subscription-card {
		padding: 1.5rem;
		background: #f9fafb;
		border-radius: 8px;
		margin-bottom: 2rem;
	}
	
	.subscription-card h3 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 1rem;
		color: #1a1a1a;
	}
	
	.plan-info {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 1rem;
	}
	
	.plan-name {
		font-size: 1.25rem;
		font-weight: 600;
		color: #1a1a1a;
	}
	
	.plan-status {
		padding: 0.25rem 0.75rem;
		background: #d1fae5;
		color: #065f46;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 500;
	}
	
	.subscription-card p {
		color: #6b7280;
		margin-bottom: 1.5rem;
	}
	
	.upgrade-button {
		display: inline-block;
		padding: 0.75rem 1.5rem;
		background: #10b981;
		color: white;
		text-decoration: none;
		border-radius: 6px;
		font-weight: 500;
		transition: background 0.2s;
	}
	
	.upgrade-button:hover {
		background: #059669;
	}
	
	.billing-info {
		padding: 1.5rem;
		background: #f9fafb;
		border-radius: 8px;
	}
	
	.billing-info h3 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 1rem;
		color: #1a1a1a;
	}
	
	.no-payment {
		color: #6b7280;
		margin-bottom: 1rem;
	}
	
	.add-payment-button {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1.5rem;
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 500;
		color: #4b5563;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.add-payment-button:hover:not(:disabled) {
		background: #f9fafb;
		border-color: #d1d5db;
	}
	
	.add-payment-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	/* Mobile Styles */
	@media (max-width: 768px) {
		.settings-layout {
			grid-template-columns: 1fr;
		}
		
		.settings-sidebar {
			position: static;
			display: flex;
			overflow-x: auto;
			-webkit-overflow-scrolling: touch;
			padding: 0;
			gap: 0.5rem;
		}
		
		.sidebar-item {
			flex-shrink: 0;
			white-space: nowrap;
		}
		
		.sidebar-item :global(svg:last-child) {
			display: none;
		}
		
		.form-grid {
			grid-template-columns: 1fr;
		}
		
		.toggle-info {
			flex-direction: column;
			gap: 0.5rem;
		}
		
		.toggle-info :global(svg) {
			display: none;
		}
		
		.security-option {
			padding: 1rem;
		}
		
		.settings-content {
			padding: 1.5rem;
		}
	}
</style>