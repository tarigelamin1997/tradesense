<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { CheckCircle2, XCircle, Loader2, Mail } from 'lucide-svelte';
	import { authApi } from '$lib/api/auth';
	import { logger } from '$lib/utils/logger';
	
	let verifying = true;
	let verified = false;
	let error = '';
	let resendEmail = '';
	let resending = false;
	let resendSuccess = false;
	
	onMount(async () => {
		const token = $page.url.searchParams.get('token');
		
		if (!token) {
			error = 'No verification token provided';
			verifying = false;
			return;
		}
		
		try {
			await authApi.verifyEmail(token);
			verified = true;
		} catch (err: any) {
			logger.error('Email verification failed:', err);
			error = err.message || 'Verification failed. The link may be expired or invalid.';
		} finally {
			verifying = false;
		}
	});
	
	async function handleResend() {
		if (!resendEmail || resending) return;
		
		try {
			resending = true;
			error = '';
			resendSuccess = false;
			
			await authApi.resendVerification(resendEmail);
			resendSuccess = true;
		} catch (err: any) {
			logger.error('Failed to resend verification:', err);
			error = err.message || 'Failed to resend verification email';
		} finally {
			resending = false;
		}
	}
</script>

<svelte:head>
	<title>Email Verification - TradeSense</title>
</svelte:head>

<div class="verification-container">
	<div class="verification-card">
		{#if verifying}
			<div class="status-icon">
				<Loader2 size={64} class="animate-spin" />
			</div>
			<h1>Verifying your email...</h1>
			<p>Please wait while we confirm your email address.</p>
		{:else if verified}
			<div class="status-icon success">
				<CheckCircle2 size={64} />
			</div>
			<h1>Email Verified!</h1>
			<p>Your email has been successfully verified. You can now access all features.</p>
			<div class="actions">
				<button on:click={() => goto('/login')} class="primary-button">
					Go to Login
				</button>
			</div>
		{:else}
			<div class="status-icon error">
				<XCircle size={64} />
			</div>
			<h1>Verification Failed</h1>
			<p class="error-message">{error}</p>
			
			<div class="resend-section">
				<h2>Need a new verification link?</h2>
				<p>Enter your email address and we'll send you a new verification link.</p>
				
				<form on:submit|preventDefault={handleResend} class="resend-form">
					<div class="form-group">
						<Mail size={20} />
						<input
							type="email"
							bind:value={resendEmail}
							placeholder="Enter your email"
							required
							disabled={resending}
						/>
					</div>
					<button type="submit" disabled={resending} class="primary-button">
						{resending ? 'Sending...' : 'Resend Verification'}
					</button>
				</form>
				
				{#if resendSuccess}
					<div class="success-message">
						Verification email sent! Please check your inbox.
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

<style>
	.verification-container {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: #f5f5f5;
		padding: 2rem;
	}
	
	.verification-card {
		background: white;
		padding: 3rem;
		border-radius: 12px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		text-align: center;
		max-width: 500px;
		width: 100%;
	}
	
	.status-icon {
		margin-bottom: 2rem;
		color: #666;
	}
	
	.status-icon.success {
		color: #10b981;
	}
	
	.status-icon.error {
		color: #dc2626;
	}
	
	:global(.animate-spin) {
		animation: spin 1s linear infinite;
	}
	
	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
	
	h1 {
		font-size: 2rem;
		margin-bottom: 1rem;
		color: #1a1a1a;
	}
	
	h2 {
		font-size: 1.25rem;
		margin-bottom: 0.5rem;
		color: #333;
	}
	
	p {
		color: #666;
		margin-bottom: 2rem;
		line-height: 1.6;
	}
	
	.error-message {
		color: #dc2626;
		background: #fee;
		padding: 1rem;
		border-radius: 6px;
		margin-bottom: 2rem;
	}
	
	.actions {
		margin-top: 2rem;
	}
	
	.primary-button {
		background: #10b981;
		color: white;
		border: none;
		padding: 0.75rem 2rem;
		border-radius: 6px;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.primary-button:hover:not(:disabled) {
		background: #059669;
		transform: translateY(-1px);
	}
	
	.primary-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	.resend-section {
		margin-top: 3rem;
		padding-top: 2rem;
		border-top: 1px solid #e0e0e0;
		text-align: left;
	}
	
	.resend-form {
		margin-top: 1rem;
	}
	
	.form-group {
		display: flex;
		align-items: center;
		background: #f5f5f5;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		padding: 0.75rem;
		margin-bottom: 1rem;
		transition: border-color 0.2s;
	}
	
	.form-group:focus-within {
		border-color: #10b981;
	}
	
	.form-group input {
		flex: 1;
		background: none;
		border: none;
		outline: none;
		font-size: 1rem;
		margin-left: 0.5rem;
	}
	
	.success-message {
		background: #dcfce7;
		color: #059669;
		padding: 1rem;
		border-radius: 6px;
		margin-top: 1rem;
		text-align: center;
	}
	
	@media (max-width: 640px) {
		.verification-card {
			padding: 2rem;
		}
		
		h1 {
			font-size: 1.5rem;
		}
	}
</style>