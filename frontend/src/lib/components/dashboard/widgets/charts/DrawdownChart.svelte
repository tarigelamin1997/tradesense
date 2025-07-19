<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Chart from 'chart.js/auto';
  import 'chartjs-adapter-date-fns';
  import type { Chart as ChartType } from 'chart.js';
  
  export let data: Array<{
    date: Date | string;
    drawdown: number; // Percentage, negative values
    equity: number; // Account value
  }> = [];
  
  export let title: string = 'Drawdown Analysis';
  export let showMaxDrawdown: boolean = true;
  export let height: string = '100%';
  
  let canvas: HTMLCanvasElement;
  let chart: ChartType | null = null;
  
  $: maxDrawdown = data.length > 0 
    ? Math.min(...data.map(d => d.drawdown))
    : 0;
  
  $: currentDrawdown = data.length > 0 
    ? data[data.length - 1].drawdown 
    : 0;
  
  function createChart() {
    if (!canvas || !data.length) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.map(d => d.date),
        datasets: [{
          label: 'Drawdown %',
          data: data.map(d => d.drawdown),
          borderColor: '#EF4444',
          backgroundColor: (context) => {
            const ctx = context.chart.ctx;
            const gradient = ctx.createLinearGradient(0, 0, 0, context.chart.height);
            gradient.addColorStop(0, 'rgba(239, 68, 68, 0.1)');
            gradient.addColorStop(1, 'rgba(239, 68, 68, 0.3)');
            return gradient;
          },
          fill: true,
          tension: 0.1,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointBackgroundColor: '#EF4444',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: 'index',
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              title: (items) => {
                const date = new Date(items[0].parsed.x);
                return date.toLocaleDateString();
              },
              label: (context) => {
                const value = context.parsed.y;
                const index = context.dataIndex;
                const equity = data[index]?.equity || 0;
                return [
                  `Drawdown: ${value.toFixed(2)}%`,
                  `Equity: $${equity.toLocaleString()}`
                ];
              }
            }
          },
          annotation: showMaxDrawdown ? {
            annotations: {
              maxLine: {
                type: 'line',
                yMin: maxDrawdown,
                yMax: maxDrawdown,
                borderColor: '#DC2626',
                borderWidth: 2,
                borderDash: [5, 5],
                label: {
                  content: `Max: ${maxDrawdown.toFixed(2)}%`,
                  enabled: true,
                  position: 'end',
                  backgroundColor: '#DC2626',
                  color: 'white',
                  padding: 4,
                  font: {
                    size: 11
                  }
                }
              }
            }
          } : {}
        },
        scales: {
          x: {
            type: 'time',
            time: {
              unit: 'day'
            },
            grid: {
              display: false
            }
          },
          y: {
            position: 'right',
            grid: {
              color: '#E5E7EB'
            },
            ticks: {
              callback: function(value: any) {
                return value + '%';
              }
            },
            max: 0,
            suggestedMin: maxDrawdown * 1.1
          }
        }
      }
    });
  }
  
  function updateChart() {
    if (!chart) {
      createChart();
      return;
    }
    
    chart.data.labels = data.map(d => d.date);
    chart.data.datasets[0].data = data.map(d => d.drawdown);
    
    // Update max drawdown annotation
    if (chart.options.plugins?.annotation?.annotations?.maxLine) {
      chart.options.plugins.annotation.annotations.maxLine.yMin = maxDrawdown;
      chart.options.plugins.annotation.annotations.maxLine.yMax = maxDrawdown;
      chart.options.plugins.annotation.annotations.maxLine.label.content = `Max: ${maxDrawdown.toFixed(2)}%`;
    }
    
    // Update y-axis scale
    if (chart.options.scales?.y) {
      chart.options.scales.y.suggestedMin = maxDrawdown * 1.1;
    }
    
    chart.update();
  }
  
  onMount(() => {
    createChart();
  });
  
  onDestroy(() => {
    if (chart) {
      chart.destroy();
    }
  });
  
  $: if (chart && data) {
    updateChart();
  }
</script>

<div class="drawdown-widget" style="height: {height}">
  <div class="stats-row">
    <div class="stat">
      <span class="stat-label">Current Drawdown</span>
      <span class="stat-value" style="color: {currentDrawdown < -5 ? '#EF4444' : '#6B7280'}">
        {currentDrawdown.toFixed(2)}%
      </span>
    </div>
    <div class="stat">
      <span class="stat-label">Max Drawdown</span>
      <span class="stat-value" style="color: #DC2626">
        {maxDrawdown.toFixed(2)}%
      </span>
    </div>
    <div class="stat">
      <span class="stat-label">Recovery Required</span>
      <span class="stat-value">
        {Math.abs(currentDrawdown / (1 + currentDrawdown / 100) * 100).toFixed(1)}%
      </span>
    </div>
  </div>
  
  <div class="chart-container">
    <canvas bind:this={canvas}></canvas>
  </div>
  
  <div class="info-text">
    Drawdown measures the peak-to-trough decline in account value
  </div>
</div>

<style>
  .drawdown-widget {
    width: 100%;
    padding: 1rem;
    display: flex;
    flex-direction: column;
  }
  
  .stats-row {
    display: flex;
    justify-content: space-around;
    margin-bottom: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #E5E7EB;
  }
  
  .stat {
    text-align: center;
  }
  
  .stat-label {
    font-size: 0.75rem;
    color: #6B7280;
    display: block;
    margin-bottom: 0.25rem;
  }
  
  .stat-value {
    font-size: 1.25rem;
    font-weight: 600;
    color: #1F2937;
  }
  
  .chart-container {
    flex: 1;
    position: relative;
    min-height: 200px;
  }
  
  canvas {
    width: 100% !important;
    height: 100% !important;
  }
  
  .info-text {
    text-align: center;
    font-size: 0.75rem;
    color: #9CA3AF;
    margin-top: 0.5rem;
  }
  
  @media (max-width: 480px) {
    .stats-row {
      flex-direction: column;
      gap: 1rem;
    }
  }
</style>