<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '$lib/api/auth';
	import MFAVerification from '$lib/components/MFAVerification.svelte';
	import { _ } from 'svelte-i18n';
	
	let username = '';
	let password = '';
	let loading = false;
	let error = '';
	
	// MFA state
	let showMFA = false;
	let mfaSessionId = '';
	let mfaMethods: string[] = [];
	
	async function handleLogin(event: Event) {
		event.preventDefault();
		error = '';
		loading = true;
		
		try {
			const result = await auth.login({ username, password });
			
			// Check if MFA is required
			if (result.mfa_required) {
				showMFA = true;
				mfaSessionId = result.session_id;
				mfaMethods = result.methods;
			} else {
				// Direct login successful
				goto('/');
			}
		} catch (err: any) {
			console.error('Login error:', err);
			// Extract error message
			if (err.detail && typeof err.detail === 'string') {
				error = err.detail;
			} else if (err.message) {
				error = err.message;
			} else {
				error = $_('auth.login.errors.invalidCredentials');
			}
		} finally {
			loading = false;
		}
	}
	
	function handleMFASuccess(authData: any) {
		// MFA verification successful, redirect
		goto('/');
	}
	
	function handleMFACancel() {
		// User cancelled MFA, reset to login form
		showMFA = false;
		mfaSessionId = '';
		mfaMethods = [];
		password = '';
	}
</script>

<svelte:head>
	<title>{$_('auth.login.title')} - {$_('common.app.name')}</title>
</svelte:head>

{#if showMFA}
	<MFAVerification
		sessionId={mfaSessionId}
		methods={mfaMethods}
		onSuccess={handleMFASuccess}
		onCancel={handleMFACancel}
	/>
{:else}
	<div class="auth-container">
		<div class="auth-card" role="region" aria-labelledby="login-heading">
			<h1 id="login-heading">{$_('auth.login.title')}</h1>
			<p class="subtitle">{$_('auth.login.subtitle')}</p>
			
			{#if error}
				<div class="error-message" role="alert" aria-live="assertive">
					{error}
				</div>
			{/if}
			
			<form on:submit={handleLogin}>
				<div class="form-group">
					<label for="username">{$_('auth.login.email')}</label>
					<input
						id="username"
						type="text"
						bind:value={username}
						required
						placeholder={$_('auth.login.emailPlaceholder')}
						disabled={loading}
					/>
				</div>
				
				<div class="form-group">
					<label for="password">{$_('auth.login.password')}</label>
					<input
						id="password"
						type="password"
						bind:value={password}
						required
						placeholder={$_('auth.login.passwordPlaceholder')}
						disabled={loading}
					/>
				</div>
				
				<div class="form-footer">
					<a href="/forgot-password" class="forgot-password">{$_('auth.login.forgotPassword')}</a>
				</div>
				
				<button type="submit" class="submit-button" disabled={loading}>
					{loading ? $_('auth.login.submitting') : $_('auth.login.submit')}
				</button>
			</form>
			
			<div class="auth-footer">
				<p>{$_('auth.login.noAccount')} <a href="/register">{$_('auth.login.signUp')}</a></p>
			</div>
		</div>
	</div>
{/if}

<style>
	.auth-container {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #f5f5f5;
		padding: 2rem;
	}
	
	.auth-card {
		background: white;
		padding: 3rem;
		border-radius: 12px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
		width: 100%;
		max-width: 400px;
	}
	
	h1 {
		font-size: 2rem;
		margin-bottom: 0.5rem;
		color: #1a1a1a;
		text-align: center;
	}
	
	.subtitle {
		color: #666;
		text-align: center;
		margin-bottom: 2rem;
	}
	
	.error-message {
		background: #fee;
		color: #c00;
		padding: 0.75rem;
		border-radius: 6px;
		margin-bottom: 1rem;
		font-size: 0.875rem;
	}
	
	.form-group {
		margin-bottom: 1.5rem;
	}
	
	label {
		display: block;
		margin-bottom: 0.5rem;
		color: #333;
		font-weight: 500;
	}
	
	input {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 1rem;
		transition: border-color 0.2s;
	}
	
	input:focus {
		outline: none;
		border-color: #10b981;
	}
	
	input:disabled {
		background: #f5f5f5;
		cursor: not-allowed;
	}
	
	.submit-button {
		width: 100%;
		padding: 0.875rem;
		background: #10b981;
		color: white;
		border: none;
		border-radius: 6px;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.2s;
	}
	
	.submit-button:hover:not(:disabled) {
		background: #059669;
	}
	
	.submit-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	.auth-footer {
		margin-top: 2rem;
		text-align: center;
		color: #666;
	}
	
	.auth-footer a {
		color: #10b981;
		text-decoration: none;
		font-weight: 500;
	}
	
	.auth-footer a:hover {
		text-decoration: underline;
	}
	
	.form-footer {
		display: flex;
		justify-content: flex-end;
		margin-bottom: 1rem;
	}
	
	.forgot-password {
		color: #10b981;
		text-decoration: none;
		font-size: 0.875rem;
		transition: opacity 0.2s;
	}
	
	.forgot-password:hover {
		opacity: 0.8;
		text-decoration: underline;
	}
</style>