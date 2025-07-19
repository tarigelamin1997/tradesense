<script lang="ts">
	import { Mail, X } from 'lucide-svelte';
	import { auth } from '$lib/api/auth';
	import { authApi } from '$lib/api/auth';
	import { logger } from '$lib/utils/logger';
	
	export let user: any;
	
	let dismissed = false;
	let resending = false;
	let resendSuccess = false;
	let resendError = '';
	
	// Check if user is verified (if the field exists)
	$: showBanner = user && user.is_verified === false && !dismissed;
	
	async function handleResend() {
		if (resending || !user?.email) return;
		
		try {
			resending = true;
			resendError = '';
			resendSuccess = false;
			
			await authApi.resendVerification(user.email);
			resendSuccess = true;
			
			// Hide success message after 5 seconds
			setTimeout(() => {
				resendSuccess = false;
			}, 5000);
		} catch (err: any) {
			logger.error('Failed to resend verification:', err);
			resendError = err.message || 'Failed to send verification email';
		} finally {
			resending = false;
		}
	}
	
	function dismiss() {
		dismissed = true;
		// Store dismissal in session storage
		if (typeof window !== 'undefined') {
			sessionStorage.setItem('email-verification-dismissed', 'true');
		}
	}
	
	// Check if previously dismissed in this session
	if (typeof window !== 'undefined') {
		dismissed = sessionStorage.getItem('email-verification-dismissed') === 'true';
	}
</script>

{#if showBanner}
	<div class="verification-banner">
		<div class="banner-content">
			<div class="banner-icon">
				<Mail size={20} />
			</div>
			<div class="banner-message">
				<strong>Verify your email</strong>
				<p>Please check your inbox and verify your email address to access all features.</p>
			</div>
			<div class="banner-actions">
				{#if resendSuccess}
					<span class="success-text">Email sent!</span>
				{:else if resendError}
					<span class="error-text">{resendError}</span>
				{:else}
					<button 
						on:click={handleResend} 
						disabled={resending}
						class="resend-button"
					>
						{resending ? 'Sending...' : 'Resend email'}
					</button>
				{/if}
			</div>
			<button on:click={dismiss} class="dismiss-button" aria-label="Dismiss">
				<X size={16} />
			</button>
		</div>
	</div>
{/if}

<style>
	.verification-banner {
		background: #fef3c7;
		border-bottom: 1px solid #f59e0b;
		padding: 1rem 0;
		position: relative;
	}
	
	.banner-content {
		max-width: 1200px;
		margin: 0 auto;
		padding: 0 2rem;
		display: flex;
		align-items: center;
		gap: 1rem;
	}
	
	.banner-icon {
		color: #f59e0b;
		flex-shrink: 0;
	}
	
	.banner-message {
		flex: 1;
		color: #92400e;
	}
	
	.banner-message strong {
		display: block;
		margin-bottom: 0.25rem;
	}
	
	.banner-message p {
		margin: 0;
		font-size: 0.875rem;
	}
	
	.banner-actions {
		flex-shrink: 0;
	}
	
	.resend-button {
		background: white;
		color: #92400e;
		border: 1px solid #f59e0b;
		padding: 0.5rem 1rem;
		border-radius: 6px;
		font-size: 0.875rem;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.resend-button:hover:not(:disabled) {
		background: #fef3c7;
	}
	
	.resend-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	.success-text {
		color: #059669;
		font-size: 0.875rem;
		font-weight: 500;
	}
	
	.error-text {
		color: #dc2626;
		font-size: 0.875rem;
	}
	
	.dismiss-button {
		background: transparent;
		border: none;
		color: #92400e;
		cursor: pointer;
		padding: 0.25rem;
		margin-left: 1rem;
		transition: opacity 0.2s;
	}
	
	.dismiss-button:hover {
		opacity: 0.7;
	}
	
	@media (max-width: 768px) {
		.banner-content {
			flex-wrap: wrap;
			padding: 0 1rem;
		}
		
		.banner-message {
			width: 100%;
			margin-bottom: 0.5rem;
		}
		
		.banner-actions {
			margin-left: 2rem;
		}
	}
</style>