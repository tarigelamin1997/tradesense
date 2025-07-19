<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import type { Trade } from '$lib/stores/trades';
	import { Chart, registerables } from 'chart.js';
	
	Chart.register(...registerables);
	
	export let trades: Trade[] = [];
	export let height = 300;
	
	let canvas: HTMLCanvasElement;
	let chart: Chart | null = null;
	
	interface StrategyStats {
		name: string;
		totalPnL: number;
		trades: number;
		winRate: number;
		avgPnL: number;
	}
	
	function calculateStrategyStats(): StrategyStats[] {
		const strategyMap = new Map<string, Trade[]>();
		
		// Group trades by strategy
		trades.forEach(trade => {
			const strategy = trade.strategy || 'No Strategy';
			const strategyTrades = strategyMap.get(strategy) || [];
			strategyTrades.push(trade);
			strategyMap.set(strategy, strategyTrades);
		});
		
		// Calculate stats for each strategy
		const stats: StrategyStats[] = [];
		
		strategyMap.forEach((strategyTrades, strategy) => {
			const totalPnL = strategyTrades.reduce((sum, t) => sum + t.pnl, 0);
			const wins = strategyTrades.filter(t => t.pnl > 0).length;
			const winRate = strategyTrades.length > 0 ? (wins / strategyTrades.length) * 100 : 0;
			const avgPnL = strategyTrades.length > 0 ? totalPnL / strategyTrades.length : 0;
			
			stats.push({
				name: strategy,
				totalPnL,
				trades: strategyTrades.length,
				winRate,
				avgPnL
			});
		});
		
		// Sort by total P&L
		return stats.sort((a, b) => b.totalPnL - a.totalPnL);
	}
	
	function createChart() {
		if (!canvas) return;
		
		const ctx = canvas.getContext('2d');
		if (!ctx) return;
		
		// Destroy existing chart
		if (chart) {
			chart.destroy();
		}
		
		const stats = calculateStrategyStats();
		
		if (stats.length === 0) return;
		
		const labels = stats.map(s => s.name);
		const totalPnLData = stats.map(s => s.totalPnL);
		const winRateData = stats.map(s => s.winRate);
		
		chart = new Chart(ctx, {
			type: 'bar',
			data: {
				labels,
				datasets: [
					{
						label: 'Total P&L',
						data: totalPnLData,
						backgroundColor: totalPnLData.map(pnl => 
							pnl >= 0 ? 'rgba(16, 185, 129, 0.6)' : 'rgba(239, 68, 68, 0.6)'
						),
						borderColor: totalPnLData.map(pnl => 
							pnl >= 0 ? '#10b981' : '#ef4444'
						),
						borderWidth: 1,
						yAxisID: 'y'
					},
					{
						label: 'Win Rate (%)',
						data: winRateData,
						type: 'line',
						borderColor: '#3b82f6',
						backgroundColor: 'rgba(59, 130, 246, 0.1)',
						borderWidth: 2,
						pointRadius: 4,
						pointHoverRadius: 6,
						yAxisID: 'y1'
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
						text: 'Strategy Performance',
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
							afterLabel: (context) => {
								const index = context.dataIndex;
								const strategy = stats[index];
								return [
									`Trades: ${strategy.trades}`,
									`Avg P&L: ${new Intl.NumberFormat('en-US', {
										style: 'currency',
										currency: 'USD'
									}).format(strategy.avgPnL)}`
								];
							}
						}
					}
				},
				scales: {
					x: {
						title: {
							display: true,
							text: 'Strategy'
						},
						ticks: {
							maxRotation: 45,
							minRotation: 45
						}
					},
					y: {
						type: 'linear',
						display: true,
						position: 'left',
						title: {
							display: true,
							text: 'Total P&L ($)'
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
						}
					},
					y1: {
						type: 'linear',
						display: true,
						position: 'right',
						title: {
							display: true,
							text: 'Win Rate (%)'
						},
						grid: {
							drawOnChartArea: false
						},
						ticks: {
							callback: (value) => `${value}%`
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