<script lang="ts">
	export let title: string;
	export let value: number;
	export let format: 'currency' | 'percent' | 'number' | 'streak' = 'number';
	export let trend: number | undefined = undefined;
	export let streakType: 'win' | 'loss' = 'win';
	
	function formatValue(val: number, fmt: string): string {
		switch (fmt) {
			case 'currency':
				return new Intl.NumberFormat('en-US', {
					style: 'currency',
					currency: 'USD'
				}).format(val);
			case 'percent':
				return `${val.toFixed(1)}%`;
			case 'streak':
				return `${val}`;
			default:
				return val.toLocaleString();
		}
	}
</script>

<div class="card metric">
	<h3>{title}</h3>
	<div class="value" class:profit={format === 'currency' && value > 0} class:loss={format === 'currency' && value < 0}>
		{#if format === 'streak'}
			<span class="streak-emoji">🔥</span>
		{/if}
		{formatValue(value, format)}
		{#if format === 'streak'}
			<span class="streak-type">{streakType}s</span>
		{/if}
	</div>
	{#if trend !== undefined}
		<div class="trend" class:profit={trend > 0} class:loss={trend < 0}>
			{trend > 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}%
		</div>
	{/if}
</div>

<style>
	.streak-emoji {
		font-size: 1.5rem;
		margin-right: 0.5rem;
	}
	
	.streak-type {
		font-size: 1rem;
		margin-left: 0.5rem;
		text-transform: capitalize;
		color: #666;
	}
	
	.value {
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	@media (max-width: 768px) {
		.card.metric {
			padding: 1rem;
		}
		
		.card.metric h3 {
			font-size: 0.875rem;
		}
		
		.value {
			font-size: 1.25rem;
		}
		
		.streak-emoji {
			font-size: 1.25rem;
			margin-right: 0.25rem;
		}
		
		.streak-type {
			font-size: 0.875rem;
			margin-left: 0.25rem;
		}
		
		.trend {
			font-size: 0.75rem;
		}
	}
	
	@media (max-width: 640px) {
		.card.metric {
			padding: 0.75rem;
		}
		
		.value {
			font-size: 1.125rem;
		}
	}
</style>