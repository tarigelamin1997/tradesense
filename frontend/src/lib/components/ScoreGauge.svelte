<script lang="ts">
  import { onMount } from 'svelte';
  
  export let score: number = 0;
  export let size: number = 200;
  export let strokeWidth: number = 15;
  export let animate: boolean = true;
  
  let mounted = false;
  let displayScore = animate ? 0 : score;
  
  $: radius = (size - strokeWidth) / 2;
  $: circumference = 2 * Math.PI * radius;
  $: dashArray = circumference;
  $: dashOffset = circumference - (displayScore / 100) * circumference;
  
  $: scoreColor = getScoreColor(displayScore);
  
  function getScoreColor(value: number): string {
    if (value >= 80) return '#10b981'; // Green
    if (value >= 60) return '#f59e0b'; // Amber
    if (value >= 40) return '#3b82f6'; // Blue
    return '#ef4444'; // Red
  }
  
  function getScoreGrade(value: number): string {
    if (value >= 90) return 'A+';
    if (value >= 80) return 'A';
    if (value >= 70) return 'B';
    if (value >= 60) return 'C';
    if (value >= 50) return 'D';
    return 'F';
  }
  
  onMount(() => {
    mounted = true;
    if (animate) {
      // Animate score from 0 to target
      const duration = 1500;
      const steps = 60;
      const increment = score / steps;
      let current = 0;
      
      const interval = setInterval(() => {
        current += increment;
        if (current >= score) {
          displayScore = score;
          clearInterval(interval);
        } else {
          displayScore = Math.round(current);
        }
      }, duration / steps);
      
      return () => clearInterval(interval);
    }
  });
  
  $: if (!animate) {
    displayScore = score;
  }
</script>

<div class="score-gauge" style="width: {size}px; height: {size}px;">
  <svg width={size} height={size} class="gauge-svg">
    <!-- Background circle -->
    <circle
      cx={size / 2}
      cy={size / 2}
      r={radius}
      stroke="#e5e7eb"
      stroke-width={strokeWidth}
      fill="none"
    />
    
    <!-- Score arc -->
    <circle
      cx={size / 2}
      cy={size / 2}
      r={radius}
      stroke={scoreColor}
      stroke-width={strokeWidth}
      fill="none"
      stroke-dasharray={dashArray}
      stroke-dashoffset={dashOffset}
      stroke-linecap="round"
      transform="rotate(-90 {size / 2} {size / 2})"
      class="score-arc"
      class:animated={mounted && animate}
    />
    
    <!-- Decorative elements -->
    <defs>
      <filter id="glow">
        <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
        <feMerge>
          <feMergeNode in="coloredBlur"/>
          <feMergeNode in="SourceGraphic"/>
        </feMerge>
      </filter>
    </defs>
    
    <!-- Center content -->
    <g transform="translate({size / 2}, {size / 2})">
      <!-- Score number -->
      <text
        x="0"
        y="0"
        text-anchor="middle"
        dominant-baseline="middle"
        class="score-text"
        fill={scoreColor}
      >
        {displayScore}
      </text>
      
      <!-- Score label -->
      <text
        x="0"
        y="25"
        text-anchor="middle"
        dominant-baseline="middle"
        class="score-label"
      >
        /100
      </text>
      
      <!-- Grade -->
      <text
        x="0"
        y="-30"
        text-anchor="middle"
        dominant-baseline="middle"
        class="score-grade"
        fill={scoreColor}
      >
        {getScoreGrade(displayScore)}
      </text>
    </g>
  </svg>
  
  <!-- Gradient overlay for depth -->
  <div class="gauge-overlay"></div>
</div>

<style>
  .score-gauge {
    position: relative;
    display: inline-block;
  }
  
  .gauge-svg {
    transform: rotate(0deg);
  }
  
  .score-arc {
    transition: stroke-dashoffset 0.3s ease;
  }
  
  .score-arc.animated {
    animation: drawArc 1.5s ease-out;
  }
  
  @keyframes drawArc {
    from {
      stroke-dashoffset: var(--circumference, 628);
    }
  }
  
  .score-text {
    font-size: 3rem;
    font-weight: 700;
    filter: url(#glow);
  }
  
  .score-label {
    font-size: 1rem;
    fill: #6b7280;
  }
  
  .score-grade {
    font-size: 1.5rem;
    font-weight: 600;
    filter: url(#glow);
  }
  
  .gauge-overlay {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background: radial-gradient(
      circle at center,
      transparent 60%,
      rgba(255, 255, 255, 0.03) 100%
    );
    pointer-events: none;
  }
</style>