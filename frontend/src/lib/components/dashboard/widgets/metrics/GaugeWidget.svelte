<script lang="ts">
  import { onMount } from 'svelte';
  
  export let value: number = 0;
  export let min: number = 0;
  export let max: number = 100;
  export let unit: string = '%';
  export let title: string = 'Gauge';
  export let segments: Array<{ value: number; color: string }> = [
    { value: 33, color: '#EF4444' },
    { value: 66, color: '#F59E0B' },
    { value: 100, color: '#10B981' }
  ];
  export let showValue: boolean = true;
  export let showMinMax: boolean = true;
  export let height: string = '100%';
  
  let rotation = -90; // Start at -90 degrees (left side)
  
  $: {
    // Calculate rotation based on value
    const percentage = (value - min) / (max - min);
    rotation = -90 + (percentage * 180); // -90 to +90 degrees
  }
  
  function getSegmentPath(startValue: number, endValue: number): string {
    const startAngle = ((startValue - min) / (max - min)) * Math.PI;
    const endAngle = ((endValue - min) / (max - min)) * Math.PI;
    
    const startX = 50 + 40 * Math.cos(Math.PI - startAngle);
    const startY = 50 + 40 * Math.sin(Math.PI - startAngle);
    const endX = 50 + 40 * Math.cos(Math.PI - endAngle);
    const endY = 50 + 40 * Math.sin(Math.PI - endAngle);
    
    const largeArc = endAngle - startAngle > Math.PI / 2 ? 1 : 0;
    
    return `M ${startX},${startY} A 40,40 0 ${largeArc} 1 ${endX},${endY}`;
  }
  
  function getColor(val: number): string {
    for (let i = segments.length - 1; i >= 0; i--) {
      if (val >= segments[i].value * (max - min) / 100 + min) {
        return segments[i].color;
      }
    }
    return segments[0].color;
  }
</script>

<div class="gauge-widget" style="height: {height}">
  <div class="gauge-container">
    <svg viewBox="0 0 100 60" class="gauge-svg">
      <!-- Background arc -->
      <path
        d="M 10,50 A 40,40 0 0 1 90,50"
        fill="none"
        stroke="#E5E7EB"
        stroke-width="8"
        stroke-linecap="round"
      />
      
      <!-- Segment arcs -->
      {#each segments as segment, i}
        {@const startVal = i === 0 ? min : segments[i-1].value * (max - min) / 100 + min}
        {@const endVal = segment.value * (max - min) / 100 + min}
        <path
          d={getSegmentPath(startVal, endVal)}
          fill="none"
          stroke={segment.color}
          stroke-width="8"
          stroke-linecap="round"
          opacity="0.3"
        />
      {/each}
      
      <!-- Value arc -->
      <path
        d="M 10,50 A 40,40 0 0 1 90,50"
        fill="none"
        stroke={getColor(value)}
        stroke-width="8"
        stroke-linecap="round"
        stroke-dasharray={`${(value - min) / (max - min) * 126} 126`}
      />
      
      <!-- Needle -->
      <g transform="translate(50, 50)">
        <line
          x1="0"
          y1="0"
          x2="30"
          y2="0"
          stroke="#374151"
          stroke-width="2"
          stroke-linecap="round"
          transform="rotate({rotation})"
        />
        <circle cx="0" cy="0" r="3" fill="#374151" />
      </g>
      
      <!-- Min/Max labels -->
      {#if showMinMax}
        <text x="10" y="58" text-anchor="start" class="gauge-label">
          {min}{unit}
        </text>
        <text x="90" y="58" text-anchor="end" class="gauge-label">
          {max}{unit}
        </text>
      {/if}
    </svg>
    
    {#if showValue}
      <div class="gauge-value" style="color: {getColor(value)}">
        {value.toFixed(1)}{unit}
      </div>
    {/if}
    
    <div class="gauge-title">{title}</div>
  </div>
</div>

<style>
  .gauge-widget {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }
  
  .gauge-container {
    width: 100%;
    max-width: 250px;
    text-align: center;
  }
  
  .gauge-svg {
    width: 100%;
    height: auto;
  }
  
  .gauge-label {
    font-size: 10px;
    fill: #6B7280;
  }
  
  .gauge-value {
    font-size: 2rem;
    font-weight: bold;
    margin-top: -1rem;
  }
  
  .gauge-title {
    font-size: 0.875rem;
    color: #6B7280;
    margin-top: 0.5rem;
  }
</style>