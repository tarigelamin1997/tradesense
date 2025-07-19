<script lang="ts">
	import { onMount } from 'svelte';
	import { createChart, ColorType } from 'lightweight-charts';
	
	export let data: Array<{ date: string; pnl: number }>;
	
	let chartContainer: HTMLDivElement;
	
	onMount(() => {
		const chart = createChart(chartContainer, {
			width: chartContainer.clientWidth,
			height: 300,
			layout: {
				background: { type: ColorType.Solid, color: 'white' },
				textColor: '#333',
			},
			grid: {
				vertLines: { color: '#e0e0e0' },
				horzLines: { color: '#e0e0e0' },
			},
			crosshair: {
				mode: 0,
			},
			rightPriceScale: {
				borderColor: '#e0e0e0',
			},
			timeScale: {
				borderColor: '#e0e0e0',
			},
		});
		
		const histogramSeries = chart.addHistogramSeries({
			color: '#10b981',
			priceFormat: {
				type: 'price',
				precision: 2,
				minMove: 0.01,
			},
		});
		
		const chartData = data.map(d => ({
			time: d.date,
			value: d.pnl,
			color: d.pnl >= 0 ? '#10b981' : '#ef4444'
		}));
		
		histogramSeries.setData(chartData);
		chart.timeScale().fitContent();
		
		// Handle resize
		const handleResize = () => {
			chart.applyOptions({ width: chartContainer.clientWidth });
		};
		
		window.addEventListener('resize', handleResize);
		
		return () => {
			window.removeEventListener('resize', handleResize);
			chart.remove();
		};
	});
</script>

<div bind:this={chartContainer} class="chart-container"></div>

<style>
	.chart-container {
		width: 100%;
		height: 300px;
	}
</style>