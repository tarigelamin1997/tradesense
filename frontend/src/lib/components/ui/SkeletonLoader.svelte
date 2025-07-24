<script lang="ts">
	export let type: 'text' | 'title' | 'card' | 'table' | 'chart' | 'custom' = 'text';
	export let lines = 3;
	export let width = '100%';
	export let height = 'auto';
	export let rounded = true;
</script>

{#if type === 'text'}
	<div class="space-y-2" style="width: {width}">
		{#each Array(lines) as _, i}
			<div
				class="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse {rounded ? 'rounded' : ''}"
				style="width: {i === lines - 1 ? '60%' : '100%'}"
			/>
		{/each}
	</div>
{:else if type === 'title'}
	<div class="space-y-2" style="width: {width}">
		<div class="h-8 bg-gray-200 dark:bg-gray-700 animate-pulse {rounded ? 'rounded' : ''} w-3/4" />
		<div class="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse {rounded ? 'rounded' : ''} w-1/2" />
	</div>
{:else if type === 'card'}
	<div
		class="bg-white dark:bg-gray-800 {rounded ? 'rounded-lg' : ''} p-6 shadow-sm border border-gray-200 dark:border-gray-700"
		style="width: {width}; height: {height}"
	>
		<div class="space-y-4">
			<div class="h-6 bg-gray-200 dark:bg-gray-700 animate-pulse rounded w-3/4" />
			<div class="space-y-2">
				<div class="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
				<div class="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
				<div class="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse rounded w-5/6" />
			</div>
		</div>
	</div>
{:else if type === 'table'}
	<div class="overflow-hidden {rounded ? 'rounded-lg' : ''}" style="width: {width}">
		<div class="bg-gray-100 dark:bg-gray-800 p-4">
			<div class="grid grid-cols-4 gap-4">
				{#each Array(4) as _}
					<div class="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
				{/each}
			</div>
		</div>
		<div class="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
			{#each Array(lines) as _}
				<div class="p-4">
					<div class="grid grid-cols-4 gap-4">
						{#each Array(4) as _}
							<div class="h-4 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
						{/each}
					</div>
				</div>
			{/each}
		</div>
	</div>
{:else if type === 'chart'}
	<div
		class="bg-white dark:bg-gray-800 {rounded ? 'rounded-lg' : ''} p-6"
		style="width: {width}; height: {height || '300px'}"
	>
		<div class="h-6 bg-gray-200 dark:bg-gray-700 animate-pulse rounded w-1/3 mb-4" />
		<div class="relative h-full">
			<div class="absolute bottom-0 left-0 right-0 flex items-end justify-between h-4/5 gap-2">
				{#each Array(12) as _}
					<div
						class="bg-gray-200 dark:bg-gray-700 animate-pulse rounded-t flex-1"
						style="height: {Math.random() * 80 + 20}%"
					/>
				{/each}
			</div>
		</div>
	</div>
{:else if type === 'custom'}
	<div
		class="bg-gray-200 dark:bg-gray-700 animate-pulse {rounded ? 'rounded' : ''}"
		style="width: {width}; height: {height}"
	/>
{/if}

<style>
	@keyframes pulse {
		0%, 100% {
			opacity: 1;
		}
		50% {
			opacity: 0.5;
		}
	}

	.animate-pulse {
		animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
	}
</style>