<script lang="ts">
	import SkeletonLoader from '$lib/components/ui/SkeletonLoader.svelte';
</script>

<div class="space-y-4">
	<!-- Filters -->
	<div class="flex gap-4">
		<SkeletonLoader type="custom" width="150px" height="40px" />
		<SkeletonLoader type="custom" width="150px" height="40px" />
		<SkeletonLoader type="custom" width="150px" height="40px" />
	</div>

	<!-- Table -->
	<SkeletonLoader type="table" lines={10} />
</div>