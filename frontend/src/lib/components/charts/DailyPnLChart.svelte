<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import type { Trade } from '$lib/stores/trades';
	import { Chart, registerables } from 'chart.js';
	import 'chartjs-adapter-date-fns';
	
	Chart.register(...registerables);
	
	export let trades: Trade[] = [];
	export let height = 300;
	
	let canvas: HTMLCanvasElement;
	let chart: Chart | null = null;
	
	function aggregateDailyPnL() {
		const dailyPnL = new Map<string, number>();
		
		trades.forEach(trade => {
			if (trade.exitDate) {
				const date = new Date(trade.exitDate).toISOString().split('T')[0];
				const currentPnL = dailyPnL.get(date) || 0;
				dailyPnL.set(date, currentPnL + trade.pnl);
			}
		});
		
		// Convert to array and sort by date
		const data = Array.from(dailyPnL.entries())
			.map(([date, pnl]) => ({
				x: new Date(date),
				y: pnl
			}))
			.sort((a, b) => a.x.getTime() - b.x.getTime());
		
		return data;
	}
	
	function createChart() {
		if (!canvas) return;
		
		const ctx = canvas.getContext('2d');
		if (!ctx) return;
		
		// Destroy existing chart
		if (chart) {
			chart.destroy();
		}
		
		const data = aggregateDailyPnL();
		
		if (data.length === 0) return;
		
		// Separate positive and negative days
		const positiveData = data.map(d => ({ ...d, y: d.y > 0 ? d.y : 0 }));
		const negativeData = data.map(d => ({ ...d, y: d.y < 0 ? d.y : 0 }));
		
		chart = new Chart(ctx, {
			type: 'bar',
			data: {
				datasets: [
					{
						label: 'Profit',
						data: positiveData,
						backgroundColor: 'rgba(16, 185, 129, 0.6)',
						borderColor: '#10b981',
						borderWidth: 1
					},
					{
						label: 'Loss',
						data: negativeData,
						backgroundColor: 'rgba(239, 68, 68, 0.6)',
						borderColor: '#ef4444',
						borderWidth: 1
					}
				]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				interaction: {
					mode: 'index',
					intersect: false
				},
				plugins: {
					title: {
						display: true,
						text: 'Daily P&L',
						font: {
							size: 16,
							weight: 'bold'
						},
						padding: {
							bottom: 20
						}
					},
					legend: {
						position: 'bottom'
					},
					tooltip: {
						callbacks: {
							label: (context) => {
								const value = context.parsed.y;
								return `${context.dataset.label}: ${new Intl.NumberFormat('en-US', {
									style: 'currency',
									currency: 'USD',
									signDisplay: 'always'
								}).format(value)}`;
							}
						}
					}
				},
				scales: {
					x: {
						type: 'time',
						time: {
							unit: 'day',
							displayFormats: {
								day: 'MMM d'
							}
						},
						title: {
							display: true,
							text: 'Date'
						},
						stacked: true
					},
					y: {
						title: {
							display: true,
							text: 'P&L ($)'
						},
						ticks: {
							callback: (value) => {
								return new Intl.NumberFormat('en-US', {
									style: 'currency',
									currency: 'USD',
									minimumFractionDigits: 0,
									maximumFractionDigits: 0
								}).format(value as number);
							}
						},
						stacked: true
					}
				}
			}
		});
	}
	
	onMount(() => {
		createChart();
	});
	
	onDestroy(() => {
		if (chart) {
			chart.destroy();
		}
	});
	
	$: if (canvas && trades) {
		createChart();
	}
</script>

<div class="chart-container" style="height: {height}px">
	<canvas bind:this={canvas}></canvas>
</div>

<style>
	.chart-container {
		position: relative;
		width: 100%;
		padding: 1rem;
		background: white;
		border-radius: 8px;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
	}
</style>