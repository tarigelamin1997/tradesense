<script lang="ts">
	import { ChevronRight, Home } from 'lucide-svelte';
	import { page } from '$app/stores';
	
	export let items: Array<{ label: string; href?: string }> = [];
	export let showHome = true;
	
	// Auto-generate breadcrumbs from URL if items not provided
	$: autoItems = items.length > 0 ? items : generateFromPath($page.url.pathname);
	
	function generateFromPath(pathname: string): Array<{ label: string; href?: string }> {
		const segments = pathname.split('/').filter(Boolean);
		const breadcrumbs: Array<{ label: string; href?: string }> = [];
		
		segments.forEach((segment, index) => {
			const href = '/' + segments.slice(0, index + 1).join('/');
			const label = segment
				.split('-')
				.map(word => word.charAt(0).toUpperCase() + word.slice(1))
				.join(' ');
			
			breadcrumbs.push({
				label,
				href: index < segments.length - 1 ? href : undefined
			});
		});
		
		return breadcrumbs;
	}
</script>

<nav aria-label="Breadcrumb" class="flex items-center space-x-2 text-sm">
	{#if showHome}
		<a 
			href="/" 
			class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
			aria-label="Home"
		>
			<Home class="h-4 w-4" />
		</a>
		{#if autoItems.length > 0}
			<ChevronRight class="h-4 w-4 text-gray-400 dark:text-gray-600" />
		{/if}
	{/if}
	
	{#each autoItems as item, index}
		{#if item.href}
			<a 
				href={item.href}
				class="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
			>
				{item.label}
			</a>
		{:else}
			<span class="text-gray-900 dark:text-white font-medium">
				{item.label}
			</span>
		{/if}
		
		{#if index < autoItems.length - 1}
			<ChevronRight class="h-4 w-4 text-gray-400 dark:text-gray-600" />
		{/if}
	{/each}
</nav>

<style>
	/* Ensure breadcrumb doesn't wrap on small screens */
	nav {
		@apply flex-wrap;
	}
	
	@media (max-width: 640px) {
		nav {
			@apply text-xs;
		}
	}
</style>