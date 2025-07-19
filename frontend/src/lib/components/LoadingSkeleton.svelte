<script lang="ts">
	export let type: 'text' | 'card' | 'table' | 'chart' | 'stat' = 'text';
	export let lines: number = 1;
	export let height: string = 'auto';
	export let width: string = '100%';
</script>

{#if type === 'text'}
	<div class="skeleton-container">
		{#each Array(lines) as _, i}
			<div 
				class="skeleton skeleton-text" 
				style="width: {i === lines - 1 ? '60%' : width}"
			></div>
		{/each}
	</div>
{:else if type === 'card'}
	<div class="skeleton skeleton-card" style="height: {height}; width: {width}">
		<div class="skeleton-header">
			<div class="skeleton skeleton-text" style="width: 60%"></div>
			<div class="skeleton skeleton-text" style="width: 20%"></div>
		</div>
		<div class="skeleton-body">
			{#each Array(3) as _}
				<div class="skeleton skeleton-text"></div>
			{/each}
		</div>
	</div>
{:else if type === 'table'}
	<div class="skeleton-table">
		<!-- Header -->
		<div class="skeleton-row skeleton-header">
			{#each Array(5) as _}
				<div class="skeleton skeleton-cell"></div>
			{/each}
		</div>
		<!-- Rows -->
		{#each Array(lines || 5) as _}
			<div class="skeleton-row">
				{#each Array(5) as _}
					<div class="skeleton skeleton-cell"></div>
				{/each}
			</div>
		{/each}
	</div>
{:else if type === 'chart'}
	<div class="skeleton skeleton-chart" style="height: {height || '300px'}; width: {width}">
		<div class="chart-bars">
			{#each Array(8) as _, i}
				<div 
					class="skeleton-bar" 
					style="height: {Math.random() * 60 + 20}%"
				></div>
			{/each}
		</div>
	</div>
{:else if type === 'stat'}
	<div class="skeleton-stat">
		<div class="skeleton skeleton-text" style="width: 80px; height: 14px"></div>
		<div class="skeleton skeleton-text" style="width: 120px; height: 32px; margin-top: 8px"></div>
		<div class="skeleton skeleton-text" style="width: 60px; height: 12px; margin-top: 4px"></div>
	</div>
{/if}

<style>
	.skeleton {
		background: linear-gradient(
			90deg,
			#f0f0f0 25%,
			#e0e0e0 50%,
			#f0f0f0 75%
		);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
		border-radius: 4px;
	}
	
	@keyframes shimmer {
		0% {
			background-position: 200% 0;
		}
		100% {
			background-position: -200% 0;
		}
	}
	
	.skeleton-container {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.skeleton-text {
		height: 1rem;
		margin: 0.25rem 0;
	}
	
	/* Card Skeleton */
	.skeleton-card {
		padding: 1.5rem;
		background: white;
		border-radius: 8px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
	
	.skeleton-header {
		display: flex;
		justify-content: space-between;
		margin-bottom: 1rem;
	}
	
	.skeleton-body {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	/* Table Skeleton */
	.skeleton-table {
		background: white;
		border-radius: 8px;
		overflow: hidden;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
	
	.skeleton-row {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 1rem;
		padding: 1rem;
		border-bottom: 1px solid #f0f0f0;
	}
	
	.skeleton-header {
		background: #f9fafb;
		font-weight: 600;
	}
	
	.skeleton-cell {
		height: 1rem;
	}
	
	/* Chart Skeleton */
	.skeleton-chart {
		padding: 1.5rem;
		background: white;
		border-radius: 8px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		display: flex;
		align-items: flex-end;
		justify-content: center;
	}
	
	.chart-bars {
		display: flex;
		align-items: flex-end;
		gap: 0.5rem;
		width: 100%;
		height: 80%;
	}
	
	.skeleton-bar {
		flex: 1;
		background: linear-gradient(
			90deg,
			#f0f0f0 25%,
			#e0e0e0 50%,
			#f0f0f0 75%
		);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
		border-radius: 4px 4px 0 0;
		min-height: 20px;
	}
	
	/* Stat Skeleton */
	.skeleton-stat {
		background: white;
		padding: 1.5rem;
		border-radius: 8px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
	
	/* Mobile Styles */
	@media (max-width: 768px) {
		.skeleton-row {
			grid-template-columns: repeat(3, 1fr);
			gap: 0.5rem;
			padding: 0.75rem;
		}
		
		.skeleton-row > *:nth-child(n+4) {
			display: none;
		}
	}
</style>