<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Lock, CheckCircle2, XCircle } from 'lucide-svelte';
	import { authApi } from '$lib/api/auth.js';
	import { logger } from '$lib/utils/logger';
	
	let password = '';
	let confirmPassword = '';
	let loading = false;
	let error = '';
	let success = false;
	let tokenValid = true;
	let token = '';
	
	onMount(() => {
		token = $page.url.searchParams.get('token') || '';
		
		if (!token) {
			tokenValid = false;
			error = 'No reset token provided';
		}
	});
	
	async function handleSubmit(e: Event) {
		e.preventDefault();
		
		// Validation
		if (!password || !confirmPassword) {
			error = 'Please fill in all fields';
			return;
		}
		
		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}
		
		if (password.length < 8) {
			error = 'Password must be at least 8 characters long';
			return;
		}
		
		// Check for letters and numbers
		const hasLetter = /[a-zA-Z]/.test(password);
		const hasNumber = /[0-9]/.test(password);
		
		if (!hasLetter || !hasNumber) {
			error = 'Password must contain both letters and numbers';
			return;
		}
		
		loading = true;
		error = '';
		
		try {
			await authApi.resetPassword(token, password);
			success = true;
			
			// Redirect to login after 3 seconds
			setTimeout(() => {
				goto('/login');
			}, 3000);
		} catch (err: any) {
			logger.error('Password reset failed:', err);
			error = err.message || 'Failed to reset password. The link may be expired.';
			
			if (err.message?.includes('expired') || err.message?.includes('invalid')) {
				tokenValid = false;
			}
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Reset Password - TradeSense</title>
</svelte:head>

<div class="auth-container">
	<div class="auth-card">
		{#if success}
			<div class="success-state">
				<div class="success-icon">
					<CheckCircle2 size={64} />
				</div>
				<h1>Password Reset Successful!</h1>
				<p>Your password has been successfully reset. You'll be redirected to login in a moment...</p>
				<a href="/login" class="login-button">Go to Login</a>
			</div>
		{:else if !tokenValid}
			<div class="error-state">
				<div class="error-icon">
					<XCircle size={64} />
				</div>
				<h1>Invalid or Expired Link</h1>
				<p>This password reset link is invalid or has expired. Password reset links are valid for 1 hour.</p>
				<a href="/forgot-password" class="primary-button">Request New Link</a>
			</div>
		{:else}
			<h1>Reset Your Password</h1>
			<p class="subtitle">Enter your new password below</p>
			
			{#if error}
				<div class="error-message">
					{error}
				</div>
			{/if}
			
			<form on:submit={handleSubmit}>
				<div class="form-group">
					<label for="password">New Password</label>
					<div class="input-wrapper">
						<Lock size={20} />
						<input
							id="password"
							type="password"
							bind:value={password}
							placeholder="Enter new password"
							required
							disabled={loading}
						/>
					</div>
					<p class="password-hint">Must be at least 8 characters with letters and numbers</p>
				</div>
				
				<div class="form-group">
					<label for="confirmPassword">Confirm Password</label>
					<div class="input-wrapper">
						<Lock size={20} />
						<input
							id="confirmPassword"
							type="password"
							bind:value={confirmPassword}
							placeholder="Confirm new password"
							required
							disabled={loading}
						/>
					</div>
				</div>
				
				<button type="submit" class="submit-button" disabled={loading}>
					{loading ? 'Resetting...' : 'Reset Password'}
				</button>
			</form>
			
			<div class="auth-footer">
				<a href="/login">Back to Login</a>
			</div>
		{/if}
	</div>
</div>

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
		max-width: 420px;
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
		color: #dc2626;
		padding: 1rem;
		border-radius: 6px;
		margin-bottom: 1.5rem;
		font-size: 0.875rem;
		text-align: center;
	}
	
	.form-group {
		margin-bottom: 1.5rem;
	}
	
	label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
		color: #333;
		font-size: 0.875rem;
	}
	
	.input-wrapper {
		position: relative;
		display: flex;
		align-items: center;
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		transition: all 0.2s;
	}
	
	.input-wrapper:focus-within {
		border-color: #10b981;
		background: white;
	}
	
	.input-wrapper :global(svg) {
		position: absolute;
		left: 1rem;
		color: #6b7280;
		pointer-events: none;
	}
	
	input {
		width: 100%;
		padding: 0.875rem 1rem 0.875rem 3rem;
		background: transparent;
		border: none;
		outline: none;
		font-size: 1rem;
	}
	
	.password-hint {
		font-size: 0.75rem;
		color: #666;
		margin-top: 0.25rem;
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
		margin-top: 0.5rem;
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
	}
	
	.auth-footer a {
		color: #10b981;
		text-decoration: none;
		font-weight: 500;
		font-size: 0.875rem;
	}
	
	.auth-footer a:hover {
		text-decoration: underline;
	}
	
	/* Success/Error States */
	.success-state,
	.error-state {
		text-align: center;
	}
	
	.success-icon {
		color: #10b981;
		margin-bottom: 1.5rem;
	}
	
	.error-icon {
		color: #dc2626;
		margin-bottom: 1.5rem;
	}
	
	.success-state p,
	.error-state p {
		color: #666;
		line-height: 1.6;
		margin-bottom: 2rem;
	}
	
	.login-button,
	.primary-button {
		display: inline-block;
		padding: 0.875rem 2rem;
		background: #10b981;
		color: white;
		text-decoration: none;
		border-radius: 6px;
		font-weight: 500;
		transition: background 0.2s;
	}
	
	.login-button:hover,
	.primary-button:hover {
		background: #059669;
	}
	
	@media (max-width: 640px) {
		.auth-card {
			padding: 2rem;
		}
		
		h1 {
			font-size: 1.75rem;
		}
	}
</style>