<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Chart from 'chart.js/auto';
  import type { Chart as ChartType } from 'chart.js';
  
  export let data: {
    labels: string[];
    datasets: Array<{
      data: number[];
      backgroundColor?: string[];
      borderColor?: string[];
      borderWidth?: number;
    }>;
  } = {
    labels: [],
    datasets: []
  };
  
  export let title = 'Pie Chart';
  export let showLegend = true;
  export let showTooltips = true;
  export let height = '100%';
  
  let canvas: HTMLCanvasElement;
  let chart: ChartType | null = null;
  let containerHeight = 300;
  
  const defaultColors = [
    '#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16'
  ];
  
  function createChart() {
    if (!canvas || !data.labels.length) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Ensure colors are set
    if (data.datasets[0] && !data.datasets[0].backgroundColor) {
      data.datasets[0].backgroundColor = defaultColors.slice(0, data.labels.length);
    }
    
    chart = new Chart(ctx, {
      type: 'pie',
      data: data,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: showLegend,
            position: 'bottom',
            labels: {
              padding: 15,
              font: {
                size: 12
              }
            }
          },
          tooltip: {
            enabled: showTooltips,
            callbacks: {
              label: function(context) {
                const label = context.label || '';
                const value = context.parsed || 0;
                const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
                const percentage = ((value / total) * 100).toFixed(1);
                return `${label}: ${value} (${percentage}%)`;
              }
            }
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
    
    chart.data = data;
    chart.update();
  }
  
  onMount(() => {
    // Get container height for responsive sizing
    const observer = new ResizeObserver(entries => {
      for (const entry of entries) {
        containerHeight = entry.contentRect.height || 300;
      }
    });
    
    if (canvas && canvas.parentElement) {
      observer.observe(canvas.parentElement);
    }
    
    createChart();
    
    return () => {
      observer.disconnect();
    };
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

<div class="pie-chart-widget" style="height: {height}">
  <canvas bind:this={canvas} style="max-height: {containerHeight - 20}px"></canvas>
</div>

<style>
  .pie-chart-widget {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px;
  }
  
  canvas {
    width: 100% !important;
  }
</style>