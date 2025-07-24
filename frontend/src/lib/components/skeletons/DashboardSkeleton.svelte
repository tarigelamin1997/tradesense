<script lang="ts">
	import SkeletonLoader from '$lib/components/ui/SkeletonLoader.svelte';
</script>

<div class="space-y-6">
	<!-- Header Stats -->
	<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
		{#each Array(4) as _}
			<SkeletonLoader type="card" height="120px" />
		{/each}
	</div>

	<!-- Charts Section -->
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
		<SkeletonLoader type="chart" height="350px" />
		<SkeletonLoader type="chart" height="350px" />
	</div>

	<!-- Recent Trades Table -->
	<div>
		<SkeletonLoader type="title" width="200px" />
		<div class="mt-4">
			<SkeletonLoader type="table" lines={5} />
		</div>
	</div>
</div>