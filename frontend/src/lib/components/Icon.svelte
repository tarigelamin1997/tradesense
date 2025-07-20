<script lang="ts">
	import * as icons from 'lucide-svelte';
	
	export let name: string;
	export let size: number = 24;
	export let strokeWidth: number = 2;
	export let color: string = 'currentColor';
	
	let className = '';
	export { className as class };
	
	// Convert kebab-case to PascalCase
	function toPascalCase(str: string) {
		return str
			.split('-')
			.map(word => word.charAt(0).toUpperCase() + word.slice(1))
			.join('');
	}
	
	// Get the icon component
	$: iconName = toPascalCase(name);
	$: IconComponent = icons[iconName] || icons.HelpCircle;
</script>

<svelte:component 
	this={IconComponent} 
	{size} 
	{strokeWidth}
	{color}
	class={className}
	{...$$restProps}
/>