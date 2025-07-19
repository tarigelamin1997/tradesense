<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import type { Trade } from '$lib/stores/trades';
	import { Chart, registerables } from 'chart.js';
	
	Chart.register(...registerables);
	
	export let trades: Trade[] = [];
	export let height = 300;
	export let bins = 10;
	
	let canvas: HTMLCanvasElement;
	let chart: Chart | null = null;
	
	function createHistogram() {
		if (trades.length === 0) return { labels: [], data: [] };
		
		const pnlValues = trades.map(t => t.pnl);
		const minPnL = Math.min(...pnlValues);
		const maxPnL = Math.max(...pnlValues);
		const range = maxPnL - minPnL;
		const binWidth = range / bins;
		
		// Create bins
		const histogram: number[] = new Array(bins).fill(0);
		const labels: string[] = [];
		
		// Count trades in each bin
		pnlValues.forEach(pnl => {
			const binIndex = Math.min(Math.floor((pnl - minPnL) / binWidth), bins - 1);
			histogram[binIndex]++;
		});
		
		// Create labels
		for (let i = 0; i < bins; i++) {
			const start = minPnL + (i * binWidth);
			const end = minPnL + ((i + 1) * binWidth);
			labels.push(`$${start.toFixed(0)} - $${end.toFixed(0)}`);
		}
		
		return { labels, data: histogram };
	}
	
	function createChart() {
		if (!canvas) return;
		
		const ctx = canvas.getContext('2d');
		if (!ctx) return;
		
		// Destroy existing chart
		if (chart) {
			chart.destroy();
		}
		
		const { labels, data } = createHistogram();
		
		if (labels.length === 0) return;
		
		// Color bars based on profit/loss
		const backgroundColors = labels.map(label => {
			const value = parseFloat(label.split('-')[0].replace('$', ''));
			return value >= 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)';
		});
		
		const borderColors = labels.map(label => {
			const value = parseFloat(label.split('-')[0].replace('$', ''));
			return value >= 0 ? '#10b981' : '#ef4444';
		});
		
		chart = new Chart(ctx, {
			type: 'bar',
			data: {
				labels,
				datasets: [{
					label: 'Number of Trades',
					data,
					backgroundColor: backgroundColors,
					borderColor: borderColors,
					borderWidth: 1
				}]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					title: {
						display: true,
						text: 'P&L Distribution',
						font: {
							size: 16,
							weight: 'bold'
						},
						padding: {
							bottom: 20
						}
					},
					legend: {
						display: false
					},
					tooltip: {
						callbacks: {
							label: (context) => {
								const count = context.parsed.y;
								const percentage = ((count / trades.length) * 100).toFixed(1);
								return `${count} trades (${percentage}%)`;
							}
						}
					}
				},
				scales: {
					x: {
						title: {
							display: true,
							text: 'P&L Range'
						},
						ticks: {
							maxRotation: 45,
							minRotation: 45
						}
					},
					y: {
						title: {
							display: true,
							text: 'Number of Trades'
						},
						beginAtZero: true,
						ticks: {
							stepSize: 1
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