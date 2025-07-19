<script lang="ts">
	import { goto } from '$app/navigation';
	import { Lock, Eye, EyeOff, AlertCircle, Check } from 'lucide-svelte';
	import { api } from '$lib/api/client.js';
	import { logger } from '$lib/utils/logger';
	
	let currentPassword = '';
	let newPassword = '';
	let confirmPassword = '';
	let loading = false;
	let error = '';
	let success = false;
	
	let showCurrentPassword = false;
	let showNewPassword = false;
	let showConfirmPassword = false;
	
	// Password strength indicators
	$: passwordStrength = calculatePasswordStrength(newPassword);
	
	function calculatePasswordStrength(password: string) {
		if (!password) return { score: 0, text: '', color: '' };
		
		let score = 0;
		const checks = {
			length: password.length >= 8,
			lowercase: /[a-z]/.test(password),
			uppercase: /[A-Z]/.test(password),
			numbers: /[0-9]/.test(password),
			special: /[^A-Za-z0-9]/.test(password)
		};
		
		// Calculate score
		if (checks.length) score += 20;
		if (checks.lowercase) score += 20;
		if (checks.uppercase) score += 20;
		if (checks.numbers) score += 20;
		if (checks.special) score += 20;
		
		// Additional bonus for length
		if (password.length >= 12) score += 10;
		if (password.length >= 16) score += 10;
		
		// Determine strength text and color
		let text = '';
		let color = '';
		
		if (score <= 40) {
			text = 'Weak';
			color = '#ef4444';
		} else if (score <= 60) {
			text = 'Fair';
			color = '#f59e0b';
		} else if (score <= 80) {
			text = 'Good';
			color = '#3b82f6';
		} else {
			text = 'Strong';
			color = '#10b981';
		}
		
		return { score: Math.min(score, 100), text, color, checks };
	}
	
	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		
		// Validation
		if (!currentPassword || !newPassword || !confirmPassword) {
			error = 'Please fill in all fields';
			return;
		}
		
		if (newPassword !== confirmPassword) {
			error = 'New passwords do not match';
			return;
		}
		
		if (newPassword === currentPassword) {
			error = 'New password must be different from current password';
			return;
		}
		
		if (newPassword.length < 8) {
			error = 'Password must be at least 8 characters long';
			return;
		}
		
		if (!passwordStrength.checks?.lowercase || !passwordStrength.checks?.numbers) {
			error = 'Password must contain both letters and numbers';
			return;
		}
		
		loading = true;
		
		try {
			await api.post('/api/v1/auth/change-password', {
				current_password: currentPassword,
				new_password: newPassword
			});
			
			success = true;
			
			// Redirect to settings after 2 seconds
			setTimeout(() => {
				goto('/settings');
			}, 2000);
			
		} catch (err: any) {
			logger.error('Password change failed:', err);
			
			if (err.message?.includes('incorrect') || err.message?.includes('wrong')) {
				error = 'Current password is incorrect';
			} else {
				error = err.message || 'Failed to change password. Please try again.';
			}
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Change Password - TradeSense</title>
</svelte:head>

<div class="container">
	<div class="password-card">
		{#if success}
			<div class="success-state">
				<div class="success-icon">
					<Check size={64} />
				</div>
				<h1>Password Changed!</h1>
				<p>Your password has been successfully updated. Redirecting to settings...</p>
			</div>
		{:else}
			<div class="header">
				<h1>Change Password</h1>
				<p>Choose a strong password to keep your account secure</p>
			</div>
			
			{#if error}
				<div class="error-message">
					<AlertCircle size={18} />
					{error}
				</div>
			{/if}
			
			<form on:submit={handleSubmit}>
				<div class="form-group">
					<label for="currentPassword">Current Password</label>
					<div class="password-input">
						<Lock size={20} />
						<input
							id="currentPassword"
							type={showCurrentPassword ? 'text' : 'password'}
							bind:value={currentPassword}
							placeholder="Enter current password"
							required
							disabled={loading}
						/>
						<button
							type="button"
							class="toggle-password"
							on:click={() => showCurrentPassword = !showCurrentPassword}
							aria-label="Toggle password visibility"
						>
							{#if showCurrentPassword}
								<EyeOff size={18} />
							{:else}
								<Eye size={18} />
							{/if}
						</button>
					</div>
				</div>
				
				<div class="form-group">
					<label for="newPassword">New Password</label>
					<div class="password-input">
						<Lock size={20} />
						<input
							id="newPassword"
							type={showNewPassword ? 'text' : 'password'}
							bind:value={newPassword}
							placeholder="Enter new password"
							required
							disabled={loading}
						/>
						<button
							type="button"
							class="toggle-password"
							on:click={() => showNewPassword = !showNewPassword}
							aria-label="Toggle password visibility"
						>
							{#if showNewPassword}
								<EyeOff size={18} />
							{:else}
								<Eye size={18} />
							{/if}
						</button>
					</div>
					
					{#if newPassword}
						<div class="password-strength">
							<div class="strength-bar">
								<div 
									class="strength-fill" 
									style="width: {passwordStrength.score}%; background-color: {passwordStrength.color}"
								></div>
							</div>
							<span class="strength-text" style="color: {passwordStrength.color}">
								{passwordStrength.text}
							</span>
						</div>
						
						<div class="password-requirements">
							<div class="requirement" class:met={passwordStrength.checks?.length}>
								<Check size={14} />
								At least 8 characters
							</div>
							<div class="requirement" class:met={passwordStrength.checks?.lowercase}>
								<Check size={14} />
								Contains lowercase letter
							</div>
							<div class="requirement" class:met={passwordStrength.checks?.uppercase}>
								<Check size={14} />
								Contains uppercase letter
							</div>
							<div class="requirement" class:met={passwordStrength.checks?.numbers}>
								<Check size={14} />
								Contains number
							</div>
							<div class="requirement" class:met={passwordStrength.checks?.special}>
								<Check size={14} />
								Contains special character
							</div>
						</div>
					{/if}
				</div>
				
				<div class="form-group">
					<label for="confirmPassword">Confirm New Password</label>
					<div class="password-input">
						<Lock size={20} />
						<input
							id="confirmPassword"
							type={showConfirmPassword ? 'text' : 'password'}
							bind:value={confirmPassword}
							placeholder="Confirm new password"
							required
							disabled={loading}
						/>
						<button
							type="button"
							class="toggle-password"
							on:click={() => showConfirmPassword = !showConfirmPassword}
							aria-label="Toggle password visibility"
						>
							{#if showConfirmPassword}
								<EyeOff size={18} />
							{:else}
								<Eye size={18} />
							{/if}
						</button>
					</div>
					{#if confirmPassword && newPassword && confirmPassword !== newPassword}
						<p class="field-error">Passwords do not match</p>
					{/if}
				</div>
				
				<div class="form-actions">
					<button
						type="button"
						class="cancel-button"
						on:click={() => goto('/settings')}
						disabled={loading}
					>
						Cancel
					</button>
					<button
						type="submit"
						class="submit-button"
						disabled={loading || !currentPassword || !newPassword || !confirmPassword}
					>
						{loading ? 'Changing...' : 'Change Password'}
					</button>
				</div>
			</form>
		{/if}
	</div>
</div>

<style>
	.container {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
		background: #f5f5f5;
	}
	
	.password-card {
		background: white;
		padding: 3rem;
		border-radius: 12px;
		box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
		width: 100%;
		max-width: 480px;
	}
	
	.header {
		text-align: center;
		margin-bottom: 2rem;
	}
	
	h1 {
		font-size: 2rem;
		margin-bottom: 0.5rem;
		color: #1a1a1a;
	}
	
	.header p {
		color: #6b7280;
	}
	
	.error-message {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: #fee;
		color: #dc2626;
		padding: 0.75rem 1rem;
		border-radius: 6px;
		margin-bottom: 1.5rem;
		font-size: 0.875rem;
	}
	
	.form-group {
		margin-bottom: 1.5rem;
	}
	
	label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
		color: #374151;
		font-size: 0.875rem;
	}
	
	.password-input {
		position: relative;
		display: flex;
		align-items: center;
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		transition: all 0.2s;
	}
	
	.password-input:focus-within {
		border-color: #10b981;
		background: white;
	}
	
	.password-input :global(svg:first-child) {
		position: absolute;
		left: 1rem;
		color: #6b7280;
		pointer-events: none;
	}
	
	input {
		flex: 1;
		padding: 0.875rem 3rem;
		background: transparent;
		border: none;
		outline: none;
		font-size: 1rem;
	}
	
	.toggle-password {
		position: absolute;
		right: 1rem;
		background: none;
		border: none;
		color: #6b7280;
		cursor: pointer;
		padding: 0.5rem;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: color 0.2s;
	}
	
	.toggle-password:hover {
		color: #374151;
	}
	
	/* Password Strength */
	.password-strength {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-top: 0.75rem;
	}
	
	.strength-bar {
		flex: 1;
		height: 4px;
		background: #e5e7eb;
		border-radius: 2px;
		overflow: hidden;
	}
	
	.strength-fill {
		height: 100%;
		transition: width 0.3s ease, background-color 0.3s ease;
	}
	
	.strength-text {
		font-size: 0.75rem;
		font-weight: 600;
		min-width: 60px;
		text-align: right;
	}
	
	.password-requirements {
		margin-top: 1rem;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.5rem;
	}
	
	.requirement {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.75rem;
		color: #9ca3af;
		transition: color 0.2s;
	}
	
	.requirement :global(svg) {
		opacity: 0;
		transition: opacity 0.2s;
	}
	
	.requirement.met {
		color: #10b981;
	}
	
	.requirement.met :global(svg) {
		opacity: 1;
	}
	
	.field-error {
		color: #dc2626;
		font-size: 0.75rem;
		margin-top: 0.5rem;
	}
	
	/* Form Actions */
	.form-actions {
		display: flex;
		gap: 1rem;
		margin-top: 2rem;
	}
	
	.cancel-button,
	.submit-button {
		flex: 1;
		padding: 0.875rem;
		border: none;
		border-radius: 6px;
		font-size: 1rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.cancel-button {
		background: white;
		color: #6b7280;
		border: 1px solid #e5e7eb;
	}
	
	.cancel-button:hover:not(:disabled) {
		background: #f9fafb;
		border-color: #d1d5db;
	}
	
	.submit-button {
		background: #10b981;
		color: white;
	}
	
	.submit-button:hover:not(:disabled) {
		background: #059669;
	}
	
	.cancel-button:disabled,
	.submit-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	/* Success State */
	.success-state {
		text-align: center;
		padding: 2rem 0;
	}
	
	.success-icon {
		color: #10b981;
		margin-bottom: 1.5rem;
	}
	
	.success-state h1 {
		margin-bottom: 1rem;
	}
	
	.success-state p {
		color: #6b7280;
	}
	
	/* Mobile Styles */
	@media (max-width: 640px) {
		.password-card {
			padding: 2rem;
		}
		
		h1 {
			font-size: 1.75rem;
		}
		
		.password-requirements {
			grid-template-columns: 1fr;
		}
		
		.form-actions {
			flex-direction: column;
		}
	}
</style>