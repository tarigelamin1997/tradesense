<script lang="ts">
	import type { SkipLink } from '$lib/utils/accessibility';
	
	export let links: SkipLink[] = [
		{ href: '#main-content', text: 'Skip to main content' },
		{ href: '#navigation', text: 'Skip to navigation' },
		{ href: '#search', text: 'Skip to search' }
	];
</script>

<nav class="skip-links" aria-label="Skip navigation">
	{#each links as link}
		<a href={link.href}>{link.text}</a>
	{/each}
</nav>

<style>
	.skip-links {
		position: absolute;
		top: -40px;
		left: 0;
		z-index: 9999;
		background: var(--color-primary, #10b981);
		transition: top 0.2s;
	}
	
	.skip-links:focus-within {
		top: 0;
	}
	
	.skip-links a {
		position: absolute;
		left: -10000px;
		top: auto;
		width: 1px;
		height: 1px;
		overflow: hidden;
		background: var(--color-primary, #10b981);
		color: white;
		padding: 0.75rem 1.5rem;
		text-decoration: none;
		border-radius: 0 0 0.5rem 0;
		font-weight: 500;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
	}
	
	.skip-links a:focus {
		position: static;
		width: auto;
		height: auto;
	}
	
	.skip-links a:hover {
		background: var(--color-primary-dark, #059669);
	}
	
	@media (prefers-reduced-motion: reduce) {
		.skip-links {
			transition: none;
		}
	}
</style>