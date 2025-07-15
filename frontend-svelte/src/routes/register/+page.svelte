<script lang="ts">
	import { goto } from '$app/navigation';
	import { auth } from '$lib/api/auth';
	
	let email = '';
	let username = '';
	let password = '';
	let confirmPassword = '';
	let loading = false;
	let error = '';
	
	async function handleRegister(event: Event) {
		event.preventDefault();
		error = '';
		
		// Validate passwords match
		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}
		
		// Validate password strength
		if (password.length < 8) {
			error = 'Password must be at least 8 characters long';
			return;
		}
		
		loading = true;
		
		try {
			await auth.register({ email, username, password });
			goto('/');
		} catch (err: any) {
			console.error('Registration error in component:', err);
			// Extract the actual error message
			if (err.detail?.details?.message) {
				error = err.detail.details.message;
			} else if (err.message === 'Network Error') {
				error = 'Cannot connect to server. Please check if the backend is running.';
			} else {
				error = err.message || 'Registration failed. Please try again.';
			}
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Register - TradeSense</title>
</svelte:head>

<div class="auth-container">
	<div class="auth-card">
		<h1>Create Account</h1>
		<p class="subtitle">Start tracking your trades with TradeSense</p>
		
		{#if error}
			<div class="error-message">
				{error}
			</div>
		{/if}
		
		<form on:submit={handleRegister}>
			<div class="form-group">
				<label for="email">Email</label>
				<input
					id="email"
					type="email"
					bind:value={email}
					required
					placeholder="Enter your email"
					disabled={loading}
				/>
			</div>
			
			<div class="form-group">
				<label for="username">Username</label>
				<input
					id="username"
					type="text"
					bind:value={username}
					required
					placeholder="Choose a username"
					disabled={loading}
				/>
			</div>
			
			<div class="form-group">
				<label for="password">Password</label>
				<input
					id="password"
					type="password"
					bind:value={password}
					required
					placeholder="Create a password"
					disabled={loading}
				/>
				<p class="password-hint">Must be 8+ characters with uppercase, lowercase, number, and special character</p>
			</div>
			
			<div class="form-group">
				<label for="confirmPassword">Confirm Password</label>
				<input
					id="confirmPassword"
					type="password"
					bind:value={confirmPassword}
					required
					placeholder="Confirm your password"
					disabled={loading}
				/>
			</div>
			
			<button type="submit" class="submit-button" disabled={loading}>
				{loading ? 'Creating account...' : 'Create Account'}
			</button>
		</form>
		
		<div class="auth-footer">
			<p>Already have an account? <a href="/login">Sign in</a></p>
		</div>
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
	
	.password-hint {
		font-size: 0.75rem;
		color: #666;
		margin-top: 0.25rem;
	}
</style>