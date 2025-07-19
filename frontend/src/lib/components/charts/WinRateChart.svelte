<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import type { Trade } from '$lib/stores/trades';
	import { Chart, registerables } from 'chart.js';
	
	Chart.register(...registerables);
	
	export let trades: Trade[] = [];
	export let height = 300;
	
	let canvas: HTMLCanvasElement;
	let chart: Chart | null = null;
	
	function calculateWinRateData() {
		const wins = trades.filter(t => t.pnl > 0).length;
		const losses = trades.filter(t => t.pnl < 0).length;
		const breakeven = trades.filter(t => t.pnl === 0).length;
		
		return {
			wins,
			losses,
			breakeven,
			winRate: trades.length > 0 ? (wins / trades.length) * 100 : 0
		};
	}
	
	function createChart() {
		if (!canvas) return;
		
		const ctx = canvas.getContext('2d');
		if (!ctx) return;
		
		// Destroy existing chart
		if (chart) {
			chart.destroy();
		}
		
		const { wins, losses, breakeven, winRate } = calculateWinRateData();
		
		chart = new Chart(ctx, {
			type: 'doughnut',
			data: {
				labels: ['Wins', 'Losses', 'Breakeven'],
				datasets: [{
					data: [wins, losses, breakeven],
					backgroundColor: [
						'#10b981',
						'#ef4444',
						'#6b7280'
					],
					borderWidth: 0
				}]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					title: {
						display: true,
						text: `Win Rate: ${winRate.toFixed(1)}%`,
						font: {
							size: 16,
							weight: 'bold'
						},
						padding: {
							bottom: 20
						}
					},
					legend: {
						position: 'bottom',
						labels: {
							padding: 15,
							font: {
								size: 12
							},
							generateLabels: (chart) => {
								const data = chart.data;
								if (data.labels && data.datasets.length) {
									return data.labels.map((label, i) => {
										const value = data.datasets[0].data[i] as number;
										const total = trades.length;
										const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
										
										return {
											text: `${label}: ${value} (${percentage}%)`,
											fillStyle: data.datasets[0].backgroundColor[i],
											hidden: false,
											index: i
										};
									});
								}
								return [];
							}
						}
					},
					tooltip: {
						callbacks: {
							label: (context) => {
								const label = context.label || '';
								const value = context.parsed;
								const total = trades.length;
								const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
								
								return `${label}: ${value} trades (${percentage}%)`;
							}
						}
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