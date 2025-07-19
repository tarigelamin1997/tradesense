<script lang="ts">
	import { Mail, ArrowLeft, CheckCircle2 } from 'lucide-svelte';
	import { authApi } from '$lib/api/auth.js';
	import { logger } from '$lib/utils/logger';
	
	let email = '';
	let loading = false;
	let error = '';
	let success = false;
	
	async function handleSubmit(e: Event) {
		e.preventDefault();
		
		if (!email) {
			error = 'Please enter your email address';
			return;
		}
		
		loading = true;
		error = '';
		
		try {
			await authApi.requestPasswordReset(email);
			success = true;
		} catch (err: any) {
			logger.error('Password reset request failed:', err);
			// Always show success to prevent email enumeration
			success = true;
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Forgot Password - TradeSense</title>
</svelte:head>

<div class="auth-container">
	<div class="auth-card">
		{#if success}
			<div class="success-state">
				<div class="success-icon">
					<CheckCircle2 size={64} />
				</div>
				<h1>Check Your Email</h1>
				<p>
					If an account exists for <strong>{email}</strong>, we've sent a password reset link. 
					Please check your inbox and follow the instructions.
				</p>
				<div class="info-box">
					<p>Didn't receive the email?</p>
					<ul>
						<li>Check your spam folder</li>
						<li>Make sure you entered the correct email</li>
						<li>Wait a few minutes and try again</li>
					</ul>
				</div>
				<a href="/login" class="back-to-login">
					<ArrowLeft size={16} />
					Back to Login
				</a>
			</div>
		{:else}
			<h1>Forgot Password?</h1>
			<p class="subtitle">
				No worries! Enter your email address and we'll send you a link to reset your password.
			</p>
			
			{#if error}
				<div class="error-message">
					{error}
				</div>
			{/if}
			
			<form on:submit={handleSubmit}>
				<div class="form-group">
					<label for="email">Email</label>
					<div class="input-wrapper">
						<Mail size={20} />
						<input
							id="email"
							type="email"
							bind:value={email}
							placeholder="Enter your email address"
							required
							disabled={loading}
						/>
					</div>
				</div>
				
				<button type="submit" class="submit-button" disabled={loading}>
					{loading ? 'Sending...' : 'Send Reset Link'}
				</button>
			</form>
			
			<div class="auth-footer">
				<a href="/login" class="back-link">
					<ArrowLeft size={16} />
					Back to Login
				</a>
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
		line-height: 1.5;
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
	
	.back-link {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		color: #666;
		text-decoration: none;
		font-size: 0.875rem;
		transition: color 0.2s;
	}
	
	.back-link:hover {
		color: #10b981;
	}
	
	/* Success State */
	.success-state {
		text-align: center;
	}
	
	.success-icon {
		color: #10b981;
		margin-bottom: 1.5rem;
	}
	
	.success-state p {
		color: #666;
		line-height: 1.6;
		margin-bottom: 1.5rem;
	}
	
	.success-state strong {
		color: #333;
	}
	
	.info-box {
		background: #f3f4f6;
		padding: 1.5rem;
		border-radius: 8px;
		text-align: left;
		margin: 2rem 0;
	}
	
	.info-box p {
		font-weight: 600;
		margin-bottom: 0.75rem;
		color: #1a1a1a;
	}
	
	.info-box ul {
		margin: 0;
		padding-left: 1.5rem;
		color: #666;
	}
	
	.info-box li {
		margin-bottom: 0.5rem;
	}
	
	.back-to-login {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		color: #10b981;
		text-decoration: none;
		font-weight: 500;
		margin-top: 1rem;
		transition: opacity 0.2s;
	}
	
	.back-to-login:hover {
		opacity: 0.8;
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