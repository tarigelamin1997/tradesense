<script lang="ts">
	import { onMount } from 'svelte';
	import { X, Download } from 'lucide-svelte';
	
	let deferredPrompt: any = null;
	let showPrompt = false;
	let isInstalled = false;
	
	onMount(() => {
		// Check if already installed
		if (window.matchMedia('(display-mode: standalone)').matches) {
			isInstalled = true;
			return;
		}
		
		// Listen for install prompt
		window.addEventListener('beforeinstallprompt', (e) => {
			e.preventDefault();
			deferredPrompt = e;
			// Show prompt after a delay
			setTimeout(() => {
				showPrompt = true;
			}, 30000); // Show after 30 seconds
		});
		
		// Listen for successful install
		window.addEventListener('appinstalled', () => {
			showPrompt = false;
			deferredPrompt = null;
			isInstalled = true;
		});
		
		// Check if iOS
		const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
		if (isIOS && !isInstalled) {
			// Show iOS-specific install instructions after delay
			setTimeout(() => {
				showPrompt = true;
			}, 60000); // Show after 1 minute on iOS
		}
	});
	
	async function handleInstall() {
		if (!deferredPrompt) {
			// iOS-specific instructions
			alert('To install TradeSense on iOS:\n1. Tap the Share button\n2. Select "Add to Home Screen"\n3. Tap "Add"');
			return;
		}
		
		// Show the install prompt
		deferredPrompt.prompt();
		
		// Wait for the user to respond
		const { outcome } = await deferredPrompt.userChoice;
		
		if (outcome === 'accepted') {
			console.log('User accepted the install prompt');
		}
		
		// Clear the deferred prompt
		deferredPrompt = null;
		showPrompt = false;
	}
	
	function handleDismiss() {
		showPrompt = false;
		// Don't show again for 7 days
		localStorage.setItem('pwa-prompt-dismissed', Date.now().toString());
	}
	
	// Check if previously dismissed
	onMount(() => {
		const dismissed = localStorage.getItem('pwa-prompt-dismissed');
		if (dismissed) {
			const dismissedTime = parseInt(dismissed);
			const daysSince = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24);
			if (daysSince < 7) {
				showPrompt = false;
			}
		}
	});
</script>

{#if showPrompt && !isInstalled}
	<div class="install-prompt">
		<div class="prompt-content">
			<button class="close-button" on:click={handleDismiss}>
				<X size={18} />
			</button>
			
			<div class="prompt-icon">
				<Download size={24} />
			</div>
			
			<div class="prompt-text">
				<h3>Install TradeSense</h3>
				<p>Add to your home screen for a better experience</p>
			</div>
			
			<div class="prompt-actions">
				<button class="dismiss-button" on:click={handleDismiss}>
					Not now
				</button>
				<button class="install-button" on:click={handleInstall}>
					Install
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.install-prompt {
		position: fixed;
		bottom: 20px;
		left: 50%;
		transform: translateX(-50%);
		z-index: 1000;
		animation: slideUp 0.3s ease-out;
		max-width: 90vw;
		width: 100%;
	}
	
	@keyframes slideUp {
		from {
			transform: translateX(-50%) translateY(100%);
			opacity: 0;
		}
		to {
			transform: translateX(-50%) translateY(0);
			opacity: 1;
		}
	}
	
	.prompt-content {
		background: white;
		border-radius: 12px;
		box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
		padding: 1.5rem;
		position: relative;
		max-width: 400px;
		margin: 0 auto;
	}
	
	.close-button {
		position: absolute;
		top: 0.75rem;
		right: 0.75rem;
		background: none;
		border: none;
		color: #666;
		cursor: pointer;
		padding: 0.25rem;
		border-radius: 4px;
		transition: all 0.2s;
	}
	
	.close-button:hover {
		background: #f3f4f6;
		color: #333;
	}
	
	.prompt-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 48px;
		height: 48px;
		background: #f0fdf4;
		border-radius: 12px;
		margin-bottom: 1rem;
		color: #10b981;
	}
	
	.prompt-text h3 {
		margin: 0 0 0.25rem;
		font-size: 1.125rem;
		color: #1a1a1a;
	}
	
	.prompt-text p {
		margin: 0;
		font-size: 0.875rem;
		color: #666;
	}
	
	.prompt-actions {
		display: flex;
		gap: 0.75rem;
		margin-top: 1.5rem;
	}
	
	.dismiss-button,
	.install-button {
		flex: 1;
		padding: 0.75rem 1rem;
		border: none;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.dismiss-button {
		background: #f3f4f6;
		color: #666;
	}
	
	.dismiss-button:hover {
		background: #e5e7eb;
		color: #333;
	}
	
	.install-button {
		background: #10b981;
		color: white;
	}
	
	.install-button:hover {
		background: #059669;
		transform: translateY(-1px);
		box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
	}
	
	/* Mobile adjustments */
	@media (max-width: 768px) {
		.install-prompt {
			bottom: 70px; /* Above mobile nav */
		}
	}
	
	@media (max-width: 640px) {
		.prompt-content {
			padding: 1.25rem;
		}
		
		.prompt-icon {
			width: 40px;
			height: 40px;
		}
		
		.prompt-text h3 {
			font-size: 1rem;
		}
		
		.prompt-text p {
			font-size: 0.8125rem;
		}
	}
</style>