<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import LoadingSkeleton from './LoadingSkeleton.svelte';
	
	export let variant: 'primary' | 'secondary' | 'danger' | 'ghost' = 'primary';
	export let size: 'small' | 'medium' | 'large' = 'medium';
	export let disabled: boolean = false;
	export let loading: boolean = false;
	export let type: 'button' | 'submit' | 'reset' = 'button';
	export let href: string | null = null;
	export let target: string | null = null;
	export let ariaLabel: string | null = null;
	export let ariaPressed: boolean | null = null;
	export let ariaExpanded: boolean | null = null;
	export let fullWidth: boolean = false;
	export let icon: any = null;
	export let iconPosition: 'left' | 'right' = 'left';
	
	const dispatch = createEventDispatcher();
	
	function handleClick(event: MouseEvent) {
		if (!disabled && !loading) {
			dispatch('click', event);
		}
	}
	
	function handleKeyDown(event: KeyboardEvent) {
		// Ensure buttons work with Enter and Space
		if ((event.key === 'Enter' || event.key === ' ') && !disabled && !loading) {
			event.preventDefault();
			dispatch('click', event);
		}
	}
	
	$: classes = [
		'button',
		`button--${variant}`,
		`button--${size}`,
		fullWidth && 'button--full-width',
		loading && 'button--loading',
		disabled && 'button--disabled'
	].filter(Boolean).join(' ');
</script>

{#if href && !disabled}
	<a
		{href}
		{target}
		class={classes}
		aria-label={ariaLabel}
		aria-disabled={disabled || loading}
		tabindex={disabled || loading ? -1 : 0}
		on:click={handleClick}
		on:keydown={handleKeyDown}
		role="button"
	>
		{#if loading}
			<span class="button__loader" aria-hidden="true">
				<svg class="spinner" viewBox="0 0 24 24">
					<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" />
				</svg>
			</span>
			<span class="sr-only">Loading...</span>
		{:else}
			{#if icon && iconPosition === 'left'}
				<span class="button__icon button__icon--left" aria-hidden="true">
					<svelte:component this={icon} size={size === 'small' ? 16 : size === 'large' ? 24 : 20} />
				</span>
			{/if}
			<span class="button__text">
				<slot />
			</span>
			{#if icon && iconPosition === 'right'}
				<span class="button__icon button__icon--right" aria-hidden="true">
					<svelte:component this={icon} size={size === 'small' ? 16 : size === 'large' ? 24 : 20} />
				</span>
			{/if}
		{/if}
	</a>
{:else}
	<button
		{type}
		{disabled}
		class={classes}
		aria-label={ariaLabel}
		aria-pressed={ariaPressed}
		aria-expanded={ariaExpanded}
		aria-busy={loading}
		on:click={handleClick}
	>
		{#if loading}
			<span class="button__loader" aria-hidden="true">
				<svg class="spinner" viewBox="0 0 24 24">
					<circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" />
				</svg>
			</span>
			<span class="sr-only">Loading...</span>
		{:else}
			{#if icon && iconPosition === 'left'}
				<span class="button__icon button__icon--left" aria-hidden="true">
					<svelte:component this={icon} size={size === 'small' ? 16 : size === 'large' ? 24 : 20} />
				</span>
			{/if}
			<span class="button__text">
				<slot />
			</span>
			{#if icon && iconPosition === 'right'}
				<span class="button__icon button__icon--right" aria-hidden="true">
					<svelte:component this={icon} size={size === 'small' ? 16 : size === 'large' ? 24 : 20} />
				</span>
			{/if}
		{/if}
	</button>
{/if}

<style>
	.button {
		position: relative;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		font-family: inherit;
		font-weight: 500;
		text-align: center;
		text-decoration: none;
		border: 1px solid transparent;
		border-radius: 0.375rem;
		cursor: pointer;
		transition: all var(--transition-fast, 150ms);
		white-space: nowrap;
		user-select: none;
		-webkit-tap-highlight-color: transparent;
	}
	
	/* Sizes */
	.button--small {
		padding: 0.375rem 0.75rem;
		font-size: 0.875rem;
		line-height: 1.25rem;
	}
	
	.button--medium {
		padding: 0.5rem 1rem;
		font-size: 1rem;
		line-height: 1.5rem;
	}
	
	.button--large {
		padding: 0.75rem 1.5rem;
		font-size: 1.125rem;
		line-height: 1.75rem;
	}
	
	/* Variants */
	.button--primary {
		background-color: var(--color-primary, #10b981);
		color: white;
	}
	
	.button--primary:hover:not(.button--disabled) {
		background-color: var(--color-primary-dark, #059669);
	}
	
	.button--primary:active:not(.button--disabled) {
		transform: scale(0.98);
	}
	
	.button--secondary {
		background-color: transparent;
		color: var(--color-primary, #10b981);
		border-color: var(--color-primary, #10b981);
	}
	
	.button--secondary:hover:not(.button--disabled) {
		background-color: var(--color-primary, #10b981);
		color: white;
	}
	
	.button--danger {
		background-color: var(--color-error, #ef4444);
		color: white;
	}
	
	.button--danger:hover:not(.button--disabled) {
		background-color: #dc2626;
	}
	
	.button--ghost {
		background-color: transparent;
		color: var(--color-text, #1f2937);
	}
	
	.button--ghost:hover:not(.button--disabled) {
		background-color: var(--color-surface, #f9fafb);
	}
	
	/* States */
	.button--disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.button--loading {
		color: transparent;
		cursor: wait;
	}
	
	.button--full-width {
		width: 100%;
	}
	
	/* Icons */
	.button__icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
	}
	
	.button__text {
		display: inline-flex;
		align-items: center;
	}
	
	/* Loading spinner */
	.button__loader {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.spinner {
		width: 1.5rem;
		height: 1.5rem;
		animation: spin 1s linear infinite;
	}
	
	.spinner circle {
		stroke-dasharray: 62.83185307179586;
		stroke-dashoffset: 47.12388980384689;
		animation: spinner-dash 1.5s ease-in-out infinite;
	}
	
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
	
	@keyframes spinner-dash {
		0% {
			stroke-dashoffset: 62.83185307179586;
		}
		50% {
			stroke-dashoffset: 15.707963267948966;
		}
		100% {
			stroke-dashoffset: 62.83185307179586;
		}
	}
	
	/* Focus styles */
	.button:focus {
		outline: 2px solid transparent;
		outline-offset: 2px;
	}
	
	.button:focus-visible {
		outline: 2px solid var(--color-primary, #10b981);
		outline-offset: 2px;
	}
	
	/* High contrast mode */
	@media (prefers-contrast: high) {
		.button {
			border-width: 2px;
		}
		
		.button--primary,
		.button--danger {
			border-color: currentColor;
		}
	}
	
	/* Reduced motion */
	@media (prefers-reduced-motion: reduce) {
		.button {
			transition: none;
		}
		
		.spinner {
			animation: none;
		}
		
		.spinner circle {
			animation: none;
			stroke-dashoffset: 31.415926535897932;
		}
	}
	
	/* Screen reader only text */
	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border-width: 0;
	}
</style>