<script lang="ts">
  import { onMount } from 'svelte';
  
  export let data: Array<{
    x: string | number;
    y: string | number;
    value: number;
  }> = [];
  
  export let title: string = 'Heatmap';
  export let xLabels: string[] = [];
  export let yLabels: string[] = [];
  export let colorScale: 'green' | 'red' | 'blue' | 'diverging' = 'green';
  export let showValues: boolean = true;
  export let height: string = '100%';
  
  let min = 0;
  let max = 0;
  
  $: {
    if (data.length > 0) {
      min = Math.min(...data.map(d => d.value));
      max = Math.max(...data.map(d => d.value));
    }
  }
  
  function getColor(value: number): string {
    const normalized = (value - min) / (max - min);
    
    switch (colorScale) {
      case 'green':
        return `rgba(16, 185, 129, ${normalized})`;
      case 'red':
        return `rgba(239, 68, 68, ${normalized})`;
      case 'blue':
        return `rgba(59, 130, 246, ${normalized})`;
      case 'diverging':
        if (value < 0) {
          return `rgba(239, 68, 68, ${Math.abs(value) / Math.abs(min)})`;
        } else {
          return `rgba(16, 185, 129, ${value / max})`;
        }
      default:
        return `rgba(156, 163, 175, ${normalized})`;
    }
  }
  
  function getCellData(x: string, y: string): { value: number; color: string } | null {
    const cell = data.find(d => String(d.x) === x && String(d.y) === y);
    if (!cell) return null;
    
    return {
      value: cell.value,
      color: getColor(cell.value)
    };
  }
  
  function formatValue(value: number): string {
    if (Math.abs(value) >= 1000) {
      return (value / 1000).toFixed(1) + 'k';
    }
    if (Math.abs(value) >= 1) {
      return value.toFixed(1);
    }
    return value.toFixed(2);
  }
</script>

<div class="heatmap-widget" style="height: {height}">
  <div class="heatmap-container">
    {#if data.length > 0}
      <div class="heatmap-grid">
        <!-- Y-axis labels -->
        <div class="y-labels">
          <div class="empty-cell"></div>
          {#each yLabels as label}
            <div class="y-label">{label}</div>
          {/each}
        </div>
        
        <!-- Grid content -->
        <div class="grid-content">
          <!-- X-axis labels -->
          <div class="x-labels">
            {#each xLabels as label}
              <div class="x-label">{label}</div>
            {/each}
          </div>
          
          <!-- Heatmap cells -->
          <div class="cells">
            {#each yLabels as yLabel}
              <div class="cell-row">
                {#each xLabels as xLabel}
                  {@const cellData = getCellData(xLabel, yLabel)}
                  <div 
                    class="cell"
                    style="background-color: {cellData ? cellData.color : '#F3F4F6'}"
                    title="{xLabel}, {yLabel}: {cellData ? cellData.value : 'N/A'}"
                  >
                    {#if showValues && cellData}
                      <span class="cell-value">
                        {formatValue(cellData.value)}
                      </span>
                    {/if}
                  </div>
                {/each}
              </div>
            {/each}
          </div>
        </div>
      </div>
      
      <!-- Legend -->
      <div class="legend">
        <div class="legend-bar" style="background: linear-gradient(to right, 
          {colorScale === 'diverging' ? 'rgba(239, 68, 68, 1)' : 'rgba(255, 255, 255, 0)'}, 
          {colorScale === 'diverging' ? 'rgba(255, 255, 255, 1)' : getColor(min)}, 
          {getColor(max)})">
        </div>
        <div class="legend-labels">
          <span>{formatValue(min)}</span>
          {#if colorScale === 'diverging'}
            <span>0</span>
          {/if}
          <span>{formatValue(max)}</span>
        </div>
      </div>
    {:else}
      <div class="no-data">No data available</div>
    {/if}
  </div>
</div>

<style>
  .heatmap-widget {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }
  
  .heatmap-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .heatmap-grid {
    display: flex;
    gap: 0.5rem;
    height: 100%;
  }
  
  .y-labels {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  
  .y-label, .x-label {
    font-size: 0.75rem;
    color: #6B7280;
    text-align: center;
    padding: 0.25rem;
  }
  
  .y-label {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    min-width: 60px;
  }
  
  .empty-cell {
    flex: 0 0 auto;
    height: 30px;
  }
  
  .grid-content {
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  
  .x-labels {
    display: flex;
    justify-content: space-between;
    height: 30px;
  }
  
  .x-label {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .cells {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .cell-row {
    display: flex;
    gap: 2px;
    flex: 1;
  }
  
  .cell {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    position: relative;
  }
  
  .cell:hover {
    transform: scale(1.05);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    z-index: 1;
  }
  
  .cell-value {
    font-size: 0.75rem;
    font-weight: 500;
    color: #1F2937;
    text-shadow: 0 0 2px rgba(255, 255, 255, 0.8);
  }
  
  .legend {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin-top: 0.5rem;
  }
  
  .legend-bar {
    height: 20px;
    border-radius: 4px;
    border: 1px solid #E5E7EB;
  }
  
  .legend-labels {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: #6B7280;
  }
  
  .no-data {
    text-align: center;
    color: #9CA3AF;
    padding: 2rem;
  }
</style>