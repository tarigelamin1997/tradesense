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
	let isMobile = false;
	
	function prepareCumulativeData() {
		// Sort trades by exit date
		const sortedTrades = [...trades]
			.filter(t => t.exitDate)
			.sort((a, b) => new Date(a.exitDate).getTime() - new Date(b.exitDate).getTime());
		
		// Calculate cumulative P&L
		let cumulativePnL = 0;
		const data = sortedTrades.map(trade => {
			cumulativePnL += trade.pnl;
			return {
				x: new Date(trade.exitDate),
				y: cumulativePnL
			};
		});
		
		// Add starting point
		if (data.length > 0) {
			data.unshift({
				x: new Date(data[0].x.getTime() - 86400000), // 1 day before first trade
				y: 0
			});
		}
		
		return data;
	}
	
	function createChart() {
		const data = prepareCumulativeData();
		
		if (!canvas || data.length === 0) return;
		
		const ctx = canvas.getContext('2d');
		if (!ctx) return;
		
		// Destroy existing chart
		if (chart) {
			chart.destroy();
		}
		
		// Determine if overall P&L is positive or negative
		const finalPnL = data[data.length - 1]?.y || 0;
		const isPositive = finalPnL >= 0;
		
		chart = new Chart(ctx, {
			type: 'line',
			data: {
				datasets: [{
					label: 'Cumulative P&L',
					data: data,
					borderColor: isPositive ? '#10b981' : '#ef4444',
					backgroundColor: isPositive ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
					fill: true,
					tension: 0.1,
					pointRadius: isMobile ? 2 : 4,
					pointHoverRadius: isMobile ? 4 : 6,
					pointBackgroundColor: isPositive ? '#10b981' : '#ef4444',
					pointBorderColor: '#fff',
					pointBorderWidth: 2
				}]
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
						text: isMobile ? 'Cumulative P&L' : 'Cumulative P&L Over Time',
						font: {
							size: isMobile ? 14 : 16,
							weight: 'bold'
						},
						padding: {
							bottom: isMobile ? 10 : 20
						}
					},
					legend: {
						display: false
					},
					tooltip: {
						callbacks: {
							label: (context) => {
								const value = context.parsed.y;
								const change = context.dataIndex > 0 
									? value - data[context.dataIndex - 1].y 
									: value;
								
								return [
									`Cumulative: ${new Intl.NumberFormat('en-US', {
										style: 'currency',
										currency: 'USD'
									}).format(value)}`,
									`Trade P&L: ${new Intl.NumberFormat('en-US', {
										style: 'currency',
										currency: 'USD',
										signDisplay: 'always'
									}).format(change)}`
								];
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
								day: isMobile ? 'M/d' : 'MMM d'
							}
						},
						title: {
							display: !isMobile,
							text: 'Date'
						},
						grid: {
							display: false
						},
						ticks: {
							font: {
								size: isMobile ? 10 : 12
							},
							maxTicksLimit: isMobile ? 5 : 10
						}
					},
					y: {
						title: {
							display: !isMobile,
							text: 'Cumulative P&L ($)'
						},
						ticks: {
							callback: (value) => {
								const formatted = new Intl.NumberFormat('en-US', {
									style: 'currency',
									currency: 'USD',
									minimumFractionDigits: 0,
									maximumFractionDigits: 0
								}).format(value as number);
								return isMobile ? formatted.replace(/\$/g, '') : formatted;
							},
							font: {
								size: isMobile ? 10 : 12
							},
							maxTicksLimit: isMobile ? 6 : 10
						},
						grid: {
							color: 'rgba(0, 0, 0, 0.05)'
						}
					}
				}
			}
		});
	}
	
	onMount(() => {
		// Check if mobile
		const checkMobile = () => {
			isMobile = window.innerWidth <= 768;
			createChart();
		};
		
		checkMobile();
		window.addEventListener('resize', checkMobile);
		
		return () => {
			window.removeEventListener('resize', checkMobile);
		};
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
	
	@media (max-width: 768px) {
		.chart-container {
			padding: 0.75rem;
		}
	}
	
	@media (max-width: 640px) {
		.chart-container {
			padding: 0.5rem;
		}
	}
</style>