<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	
	// Props
	export let items: any[] = [];
	export let itemHeight: number = 50;
	export let buffer: number = 5; // Extra items to render outside viewport
	export let key: string = 'id'; // Key property for keyed each blocks
	
	// State
	let container: HTMLDivElement;
	let viewport: HTMLDivElement;
	let scrollTop = 0;
	let viewportHeight = 0;
	let visibleStart = 0;
	let visibleEnd = 0;
	
	// Computed values
	$: totalHeight = items.length * itemHeight;
	$: visibleCount = Math.ceil(viewportHeight / itemHeight) + buffer * 2;
	$: visibleStart = Math.max(0, Math.floor(scrollTop / itemHeight) - buffer);
	$: visibleEnd = Math.min(items.length, visibleStart + visibleCount);
	$: visibleItems = items.slice(visibleStart, visibleEnd);
	$: offsetY = visibleStart * itemHeight;
	
	// Handle scroll
	function handleScroll() {
		if (!viewport) return;
		scrollTop = viewport.scrollTop;
	}
	
	// Handle resize
	function handleResize() {
		if (!viewport) return;
		viewportHeight = viewport.clientHeight;
	}
	
	// Lifecycle
	onMount(() => {
		if (!browser) return;
		
		handleResize();
		window.addEventListener('resize', handleResize);
		
		return () => {
			window.removeEventListener('resize', handleResize);
		};
	});
	
	// Scroll to item
	export function scrollToItem(index: number) {
		if (!viewport) return;
		const offset = index * itemHeight;
		viewport.scrollTop = offset;
	}
	
	// Get current scroll position
	export function getScrollPosition() {
		return {
			index: Math.floor(scrollTop / itemHeight),
			offset: scrollTop % itemHeight
		};
	}
</script>

<div 
	class="virtual-list-container"
	bind:this={container}
	role="region"
	aria-label="Scrollable list"
>
	<div 
		class="virtual-list-viewport"
		bind:this={viewport}
		on:scroll={handleScroll}
		tabindex="0"
		aria-rowcount={items.length}
	>
		<div 
			class="virtual-list-spacer" 
			style="height: {totalHeight}px"
			aria-hidden="true"
		>
			<div 
				class="virtual-list-content"
				style="transform: translateY({offsetY}px)"
			>
				{#each visibleItems as item, i (item[key])}
					<div 
						class="virtual-list-item"
						style="height: {itemHeight}px"
						role="row"
						aria-rowindex={visibleStart + i + 1}
					>
						<slot {item} index={visibleStart + i} />
					</div>
				{/each}
			</div>
		</div>
	</div>
	
	<!-- Screen reader announcement for navigation -->
	<div class="sr-only" role="status" aria-live="polite" aria-atomic="true">
		Showing items {visibleStart + 1} to {visibleEnd} of {items.length}
	</div>
</div>

<style>
	.virtual-list-container {
		position: relative;
		height: 100%;
		overflow: hidden;
	}
	
	.virtual-list-viewport {
		position: relative;
		height: 100%;
		overflow-y: auto;
		overflow-x: hidden;
		-webkit-overflow-scrolling: touch;
	}
	
	.virtual-list-spacer {
		position: relative;
		width: 100%;
	}
	
	.virtual-list-content {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		will-change: transform;
	}
	
	.virtual-list-item {
		position: relative;
		width: 100%;
		overflow: hidden;
	}
	
	/* Improve scroll performance */
	.virtual-list-viewport::-webkit-scrollbar {
		width: 12px;
	}
	
	.virtual-list-viewport::-webkit-scrollbar-track {
		background: #f1f1f1;
		border-radius: 6px;
	}
	
	.virtual-list-viewport::-webkit-scrollbar-thumb {
		background: #888;
		border-radius: 6px;
	}
	
	.virtual-list-viewport::-webkit-scrollbar-thumb:hover {
		background: #555;
	}
	
	/* Dark mode scrollbar */
	:global(.dark) .virtual-list-viewport::-webkit-scrollbar-track {
		background: #2a2a2a;
	}
	
	:global(.dark) .virtual-list-viewport::-webkit-scrollbar-thumb {
		background: #666;
	}
	
	:global(.dark) .virtual-list-viewport::-webkit-scrollbar-thumb:hover {
		background: #888;
	}
	
	/* Focus styles */
	.virtual-list-viewport:focus {
		outline: 2px solid #10b981;
		outline-offset: -2px;
	}
	
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
	
	/* Smooth scrolling */
	@media (prefers-reduced-motion: no-preference) {
		.virtual-list-viewport {
			scroll-behavior: smooth;
		}
	}
</style>