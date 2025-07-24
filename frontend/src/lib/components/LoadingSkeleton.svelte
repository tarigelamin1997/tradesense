<script lang="ts">
	export let variant: 'text' | 'title' | 'card' | 'table' | 'chart' = 'text';
	export let lines: number = 1;
	export let animate: boolean = true;
	export let width: string = '100%';
	export let height: string = 'auto';
</script>

<div 
	class="skeleton skeleton--{variant}" 
	class:skeleton--animated={animate}
	style="width: {width}; height: {height};"
	role="status"
	aria-label="Loading content"
>
	{#if variant === 'text'}
		{#each Array(lines) as _, i}
			<div class="skeleton__line" style="width: {i === lines - 1 ? '80%' : '100%'}"></div>
		{/each}
	{:else if variant === 'title'}
		<div class="skeleton__title"></div>
	{:else if variant === 'card'}
		<div class="skeleton__card">
			<div class="skeleton__card-header">
				<div class="skeleton__avatar"></div>
				<div class="skeleton__card-title">
					<div class="skeleton__line" style="width: 60%"></div>
					<div class="skeleton__line" style="width: 40%"></div>
				</div>
			</div>
			<div class="skeleton__card-body">
				{#each Array(3) as _}
					<div class="skeleton__line"></div>
				{/each}
			</div>
		</div>
	{:else if variant === 'table'}
		<div class="skeleton__table">
			<div class="skeleton__table-header">
				{#each Array(4) as _}
					<div class="skeleton__cell"></div>
				{/each}
			</div>
			{#each Array(5) as _}
				<div class="skeleton__table-row">
					{#each Array(4) as _}
						<div class="skeleton__cell"></div>
					{/each}
				</div>
			{/each}
		</div>
	{:else if variant === 'chart'}
		<div class="skeleton__chart">
			<div class="skeleton__chart-bars">
				{#each Array(7) as _, i}
					<div 
						class="skeleton__chart-bar" 
						style="height: {Math.random() * 60 + 40}%"
					></div>
				{/each}
			</div>
		</div>
	{/if}
	<span class="sr-only">Loading...</span>
</div>

<style>
	.skeleton {
		position: relative;
		overflow: hidden;
		background: #f0f0f0;
		border-radius: 0.25rem;
	}
	
	:global(.dark) .skeleton {
		background: #2a2a2a;
	}
	
	.skeleton--animated::after {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: linear-gradient(
			90deg,
			transparent,
			rgba(255, 255, 255, 0.3),
			transparent
		);
		animation: shimmer 1.5s infinite;
	}
	
	:global(.dark) .skeleton--animated::after {
		background: linear-gradient(
			90deg,
			transparent,
			rgba(255, 255, 255, 0.1),
			transparent
		);
	}
	
	@keyframes shimmer {
		0% {
			transform: translateX(-100%);
		}
		100% {
			transform: translateX(100%);
		}
	}
	
	.skeleton__line {
		height: 1rem;
		background: #e0e0e0;
		border-radius: 0.25rem;
		margin-bottom: 0.75rem;
	}
	
	:global(.dark) .skeleton__line {
		background: #3a3a3a;
	}
	
	.skeleton__line:last-child {
		margin-bottom: 0;
	}
	
	.skeleton__title {
		height: 2rem;
		background: #e0e0e0;
		border-radius: 0.25rem;
		width: 60%;
	}
	
	:global(.dark) .skeleton__title {
		background: #3a3a3a;
	}
	
	.skeleton__card {
		padding: 1.5rem;
		background: white;
		border-radius: 0.5rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
	
	:global(.dark) .skeleton__card {
		background: #1a1a1a;
	}
	
	.skeleton__card-header {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 1rem;
	}
	
	.skeleton__avatar {
		width: 3rem;
		height: 3rem;
		background: #e0e0e0;
		border-radius: 50%;
		flex-shrink: 0;
	}
	
	:global(.dark) .skeleton__avatar {
		background: #3a3a3a;
	}
	
	.skeleton__card-title {
		flex: 1;
	}
	
	.skeleton__card-body {
		margin-top: 1.5rem;
	}
	
	.skeleton__table {
		background: white;
		border-radius: 0.5rem;
		overflow: hidden;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
	
	:global(.dark) .skeleton__table {
		background: #1a1a1a;
	}
	
	.skeleton__table-header {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
		padding: 1rem;
		background: #f5f5f5;
		border-bottom: 1px solid #e0e0e0;
	}
	
	:global(.dark) .skeleton__table-header {
		background: #2a2a2a;
		border-bottom-color: #3a3a3a;
	}
	
	.skeleton__table-row {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1rem;
		padding: 1rem;
		border-bottom: 1px solid #e0e0e0;
	}
	
	:global(.dark) .skeleton__table-row {
		border-bottom-color: #3a3a3a;
	}
	
	.skeleton__table-row:last-child {
		border-bottom: none;
	}
	
	.skeleton__cell {
		height: 1rem;
		background: #e0e0e0;
		border-radius: 0.25rem;
	}
	
	:global(.dark) .skeleton__cell {
		background: #3a3a3a;
	}
	
	.skeleton__chart {
		height: 300px;
		padding: 2rem;
		background: white;
		border-radius: 0.5rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
	
	:global(.dark) .skeleton__chart {
		background: #1a1a1a;
	}
	
	.skeleton__chart-bars {
		display: flex;
		align-items: flex-end;
		justify-content: space-around;
		height: 100%;
		gap: 0.5rem;
	}
	
	.skeleton__chart-bar {
		flex: 1;
		background: #e0e0e0;
		border-radius: 0.25rem 0.25rem 0 0;
	}
	
	:global(.dark) .skeleton__chart-bar {
		background: #3a3a3a;
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
	
	@media (prefers-reduced-motion: reduce) {
		.skeleton--animated::after {
			animation: none;
		}
	}
</style>