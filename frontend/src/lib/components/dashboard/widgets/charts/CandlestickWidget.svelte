<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Chart from 'chart.js/auto';
  import 'chartjs-adapter-date-fns';
  import type { Chart as ChartType } from 'chart.js';
  
  export let data: Array<{
    x: Date | string | number;
    o: number; // open
    h: number; // high
    l: number; // low
    c: number; // close
    v?: number; // volume
  }> = [];
  
  export let title: string = 'Price Chart';
  export let showVolume: boolean = true;
  export let height: string = '100%';
  
  let canvas: HTMLCanvasElement;
  let volumeCanvas: HTMLCanvasElement;
  let chart: ChartType | null = null;
  let volumeChart: ChartType | null = null;
  
  function createChart() {
    if (!canvas || !data.length) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Custom candlestick renderer
    const candlestickPlugin = {
      id: 'candlestick',
      beforeDatasetsDraw: (chart: any) => {
        const ctx = chart.ctx;
        const meta = chart.getDatasetMeta(0);
        
        meta.data.forEach((point: any, index: number) => {
          const { x, y } = point;
          const dataPoint = data[index];
          if (!dataPoint) return;
          
          const yScale = chart.scales.y;
          const open = yScale.getPixelForValue(dataPoint.o);
          const high = yScale.getPixelForValue(dataPoint.h);
          const low = yScale.getPixelForValue(dataPoint.l);
          const close = yScale.getPixelForValue(dataPoint.c);
          
          const isGreen = dataPoint.c >= dataPoint.o;
          const color = isGreen ? '#10B981' : '#EF4444';
          
          ctx.save();
          
          // Draw the wick
          ctx.beginPath();
          ctx.moveTo(x, high);
          ctx.lineTo(x, low);
          ctx.strokeStyle = color;
          ctx.lineWidth = 1;
          ctx.stroke();
          
          // Draw the body
          ctx.fillStyle = color;
          ctx.fillRect(x - 4, Math.min(open, close), 8, Math.abs(close - open) || 1);
          
          ctx.restore();
        });
      }
    };
    
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        datasets: [{
          label: title,
          data: data.map(d => ({ x: d.x, y: d.c })),
          borderColor: 'transparent',
          backgroundColor: 'transparent',
          pointRadius: 0,
          pointHoverRadius: 0,
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
                return new Date(items[0].parsed.x).toLocaleDateString();
              },
              label: (context) => {
                const index = context.dataIndex;
                const point = data[index];
                if (!point) return '';
                
                return [
                  `Open: ${point.o.toFixed(2)}`,
                  `High: ${point.h.toFixed(2)}`,
                  `Low: ${point.l.toFixed(2)}`,
                  `Close: ${point.c.toFixed(2)}`,
                  point.v ? `Volume: ${point.v.toLocaleString()}` : ''
                ].filter(Boolean);
              }
            }
          }
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
            }
          }
        }
      },
      plugins: [candlestickPlugin]
    });
    
    // Create volume chart if needed
    if (showVolume && volumeCanvas && data.some(d => d.v)) {
      const volumeCtx = volumeCanvas.getContext('2d');
      if (!volumeCtx) return;
      
      volumeChart = new Chart(volumeCtx, {
        type: 'bar',
        data: {
          datasets: [{
            label: 'Volume',
            data: data.map(d => ({ x: d.x, y: d.v || 0 })),
            backgroundColor: data.map(d => d.c >= d.o ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)'),
            borderWidth: 0,
            barPercentage: 0.8,
            categoryPercentage: 1.0,
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
              enabled: false
            }
          },
          scales: {
            x: {
              type: 'time',
              time: {
                unit: 'day'
              },
              display: false
            },
            y: {
              position: 'right',
              grid: {
                display: false
              },
              ticks: {
                callback: function(value: any) {
                  return (value / 1000000).toFixed(0) + 'M';
                }
              }
            }
          }
        }
      });
    }
  }
  
  function updateChart() {
    if (!chart) {
      createChart();
      return;
    }
    
    // Update data
    chart.data.datasets[0].data = data.map(d => ({ x: d.x, y: d.c }));
    chart.update('none');
    
    if (volumeChart) {
      volumeChart.data.datasets[0].data = data.map(d => ({ x: d.x, y: d.v || 0 }));
      volumeChart.data.datasets[0].backgroundColor = data.map(d => 
        d.c >= d.o ? 'rgba(16, 185, 129, 0.5)' : 'rgba(239, 68, 68, 0.5)'
      );
      volumeChart.update('none');
    }
  }
  
  onMount(() => {
    createChart();
  });
  
  onDestroy(() => {
    if (chart) chart.destroy();
    if (volumeChart) volumeChart.destroy();
  });
  
  $: if (data) {
    updateChart();
  }
</script>

<div class="candlestick-widget" style="height: {height}">
  <div class="chart-container" class:with-volume={showVolume}>
    <div class="price-chart">
      <canvas bind:this={canvas}></canvas>
    </div>
    {#if showVolume}
      <div class="volume-chart">
        <canvas bind:this={volumeCanvas}></canvas>
      </div>
    {/if}
  </div>
</div>

<style>
  .candlestick-widget {
    width: 100%;
    padding: 0.5rem;
  }
  
  .chart-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  .chart-container.with-volume .price-chart {
    flex: 3;
  }
  
  .chart-container.with-volume .volume-chart {
    flex: 1;
    margin-top: -20px;
  }
  
  .price-chart {
    flex: 1;
    position: relative;
  }
  
  .volume-chart {
    position: relative;
  }
  
  canvas {
    width: 100% !important;
    height: 100% !important;
  }
</style>