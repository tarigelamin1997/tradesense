<script lang="ts">
	import SkeletonLoader from '$lib/components/ui/SkeletonLoader.svelte';
	
	export let fields = 5;
</script>

<div class="max-w-2xl mx-auto space-y-6">
	<SkeletonLoader type="title" />
	
	<div class="space-y-4">
		{#each Array(fields) as _}
			<div class="space-y-2">
				<SkeletonLoader type="custom" width="100px" height="20px" />
				<SkeletonLoader type="custom" width="100%" height="40px" />
			</div>
		{/each}
	</div>
	
	<div class="flex gap-4">
		<SkeletonLoader type="custom" width="120px" height="40px" />
		<SkeletonLoader type="custom" width="120px" height="40px" />
	</div>
</div>