<script lang="ts">
	export let title = '';
	export let data: any[] = [];
	export let type: 'line' | 'bar' | 'area' = 'line';
	export let height = '300px';
	export let loading = false;
	
	// Simple chart visualization using SVG
	let width = 600;
	let chartHeight = 250;
	let padding = 40;
	
	$: maxValue = Math.max(...(data.map(d => d.value || 0)), 0) || 100;
	$: minValue = Math.min(...(data.map(d => d.value || 0)), 0);
	$: range = maxValue - minValue || 1;
	
	$: xScale = (index: number) => {
		if (data.length <= 1) return padding;
		return padding + (index / (data.length - 1)) * (width - 2 * padding);
	};
	
	$: yScale = (value: number) => {
		return chartHeight - padding - ((value - minValue) / range) * (chartHeight - 2 * padding);
	};
	
	$: pathData = data.map((d, i) => {
		const x = xScale(i);
		const y = yScale(d.value || 0);
		return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
	}).join(' ');
	
	$: areaPath = data.length > 0 ? 
		`${pathData} L ${xScale(data.length - 1)} ${chartHeight - padding} L ${padding} ${chartHeight - padding} Z` : 
		'';
</script>

<div class="chart-container" style="height: {height}">
	{#if title}
		<h3 class="chart-title">{title}</h3>
	{/if}
	
	{#if loading}
		<div class="loading">Loading chart data...</div>
	{:else if data.length === 0}
		<div class="empty">No data available</div>
	{:else}
		<svg viewBox="0 0 {width} {chartHeight}" class="chart">
			<!-- Grid lines -->
			{#each Array(5) as _, i}
				<line 
					x1={padding} 
					x2={width - padding} 
					y1={padding + i * (chartHeight - 2 * padding) / 4} 
					y2={padding + i * (chartHeight - 2 * padding) / 4} 
					stroke="#e5e7eb" 
					stroke-width="1"
				/>
			{/each}
			
			<!-- Area (for area chart) -->
			{#if type === 'area'}
				<path 
					d={areaPath} 
					fill="rgba(59, 130, 246, 0.1)"
				/>
			{/if}
			
			<!-- Line (for line and area charts) -->
			{#if type === 'line' || type === 'area'}
				<path 
					d={pathData} 
					fill="none" 
					stroke="#3b82f6" 
					stroke-width="2"
				/>
			{/if}
			
			<!-- Bars (for bar chart) -->
			{#if type === 'bar'}
				{#each data as d, i}
					<rect 
						x={xScale(i) - 10} 
						y={yScale(d.value || 0)} 
						width="20" 
						height={chartHeight - padding - yScale(d.value || 0)}
						fill="#3b82f6"
						opacity="0.8"
					/>
				{/each}
			{/if}
			
			<!-- Data points -->
			{#if type === 'line' || type === 'area'}
				{#each data as d, i}
					<circle 
						cx={xScale(i)} 
						cy={yScale(d.value || 0)} 
						r="4" 
						fill="#3b82f6"
					/>
				{/each}
			{/if}
			
			<!-- X-axis labels -->
			{#each data as d, i}
				{#if i % Math.ceil(data.length / 5) === 0 || i === data.length - 1}
					<text 
						x={xScale(i)} 
						y={chartHeight - 10} 
						text-anchor="middle" 
						font-size="12" 
						fill="#6b7280"
					>
						{d.label || ''}
					</text>
				{/if}
			{/each}
			
			<!-- Y-axis labels -->
			{#each Array(5) as _, i}
				<text 
					x={padding - 10} 
					y={padding + i * (chartHeight - 2 * padding) / 4} 
					text-anchor="end" 
					dominant-baseline="middle"
					font-size="12" 
					fill="#6b7280"
				>
					{Math.round(maxValue - (i * range / 4))}
				</text>
			{/each}
		</svg>
	{/if}
</div>

<style>
	.chart-container {
		background: white;
		border-radius: 8px;
		padding: 1rem;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
		display: flex;
		flex-direction: column;
		position: relative;
	}
	
	.chart-title {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 1rem;
		color: #1f2937;
	}
	
	.chart {
		width: 100%;
		height: 100%;
		flex: 1;
	}
	
	.loading, .empty {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100%;
		color: #6b7280;
		font-size: 0.875rem;
	}
</style>