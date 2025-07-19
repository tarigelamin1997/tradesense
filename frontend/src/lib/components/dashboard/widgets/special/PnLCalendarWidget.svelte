<script lang="ts">
  import { onMount } from 'svelte';
  import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isToday, startOfWeek, endOfWeek } from 'date-fns';
  
  export let data: Array<{
    date: string; // YYYY-MM-DD format
    value: number; // P&L value
    trades?: number; // optional trade count
  }> = [];
  
  export let title: string = 'P&L Calendar';
  export let height: string = '100%';
  export let showLegend: boolean = true;
  
  let currentDate = new Date();
  let calendarDays: Date[] = [];
  let minValue = 0;
  let maxValue = 0;
  
  $: {
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const calendarStart = startOfWeek(monthStart);
    const calendarEnd = endOfWeek(monthEnd);
    
    calendarDays = eachDayOfInterval({ start: calendarStart, end: calendarEnd });
    
    // Calculate min/max for color scaling
    const values = data.map(d => d.value);
    if (values.length > 0) {
      minValue = Math.min(...values, 0);
      maxValue = Math.max(...values, 0);
    }
  }
  
  function getDayData(date: Date) {
    const dateStr = format(date, 'yyyy-MM-dd');
    return data.find(d => d.date === dateStr);
  }
  
  function getDayColor(value: number | undefined): string {
    if (value === undefined) return '#F3F4F6';
    
    if (value === 0) return '#E5E7EB';
    
    if (value > 0) {
      const intensity = Math.min(value / maxValue, 1);
      return `rgba(16, 185, 129, ${0.2 + intensity * 0.8})`;
    } else {
      const intensity = Math.min(Math.abs(value) / Math.abs(minValue), 1);
      return `rgba(239, 68, 68, ${0.2 + intensity * 0.8})`;
    }
  }
  
  function changeMonth(delta: number) {
    currentDate = new Date(currentDate.getFullYear(), currentDate.getMonth() + delta, 1);
  }
  
  function formatPnL(value: number): string {
    const absValue = Math.abs(value);
    if (absValue >= 1000) {
      return (value / 1000).toFixed(1) + 'k';
    }
    return value.toFixed(0);
  }
  
  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
</script>

<div class="pnl-calendar-widget" style="height: {height}">
  <div class="calendar-container">
    <div class="calendar-header">
      <button class="nav-button" on:click={() => changeMonth(-1)}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M10 12L6 8L10 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
      <h3>{format(currentDate, 'MMMM yyyy')}</h3>
      <button class="nav-button" on:click={() => changeMonth(1)}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M6 12L10 8L6 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
    
    <div class="calendar-grid">
      <div class="weekdays">
        {#each weekDays as day}
          <div class="weekday">{day}</div>
        {/each}
      </div>
      
      <div class="days">
        {#each calendarDays as day}
          {@const dayData = getDayData(day)}
          {@const isCurrentMonth = isSameMonth(day, currentDate)}
          {@const isTodayDate = isToday(day)}
          <div 
            class="day"
            class:other-month={!isCurrentMonth}
            class:today={isTodayDate}
            style="background-color: {getDayColor(dayData?.value)}"
            title="{format(day, 'MMM d, yyyy')}: {dayData ? `$${dayData.value.toFixed(2)}` : 'No trades'}"
          >
            <span class="day-number">{format(day, 'd')}</span>
            {#if dayData}
              <span class="day-value">
                {formatPnL(dayData.value)}
              </span>
              {#if dayData.trades}
                <span class="trade-count">{dayData.trades}</span>
              {/if}
            {/if}
          </div>
        {/each}
      </div>
    </div>
    
    {#if showLegend}
      <div class="legend">
        <div class="legend-item">
          <div class="legend-color" style="background-color: rgba(239, 68, 68, 0.8)"></div>
          <span>Loss</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background-color: #E5E7EB"></div>
          <span>Break Even</span>
        </div>
        <div class="legend-item">
          <div class="legend-color" style="background-color: rgba(16, 185, 129, 0.8)"></div>
          <span>Profit</span>
        </div>
      </div>
    {/if}
    
    <div class="summary">
      <div class="summary-item">
        <span class="summary-label">Month Total:</span>
        <span class="summary-value" style="color: {data.reduce((sum, d) => sum + d.value, 0) >= 0 ? '#10B981' : '#EF4444'}">
          ${data.reduce((sum, d) => sum + d.value, 0).toFixed(2)}
        </span>
      </div>
      <div class="summary-item">
        <span class="summary-label">Trading Days:</span>
        <span class="summary-value">{data.length}</span>
      </div>
    </div>
  </div>
</div>

<style>
  .pnl-calendar-widget {
    width: 100%;
    padding: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .calendar-container {
    width: 100%;
    max-width: 500px;
  }
  
  .calendar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .calendar-header h3 {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1F2937;
  }
  
  .nav-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.5rem;
    color: #6B7280;
    transition: all 0.2s;
  }
  
  .nav-button:hover {
    color: #374151;
    background: #F3F4F6;
    border-radius: 4px;
  }
  
  .calendar-grid {
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    overflow: hidden;
  }
  
  .weekdays {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    background: #F9FAFB;
    border-bottom: 1px solid #E5E7EB;
  }
  
  .weekday {
    padding: 0.5rem;
    text-align: center;
    font-size: 0.75rem;
    font-weight: 500;
    color: #6B7280;
  }
  
  .days {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
  }
  
  .day {
    aspect-ratio: 1;
    border: 1px solid #E5E7EB;
    margin: -1px 0 0 -1px;
    padding: 0.25rem;
    position: relative;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  
  .day:hover {
    z-index: 1;
    transform: scale(1.1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    border-color: #9CA3AF;
  }
  
  .day.other-month {
    opacity: 0.3;
  }
  
  .day.today {
    border: 2px solid #3B82F6;
    margin: -2px 0 0 -2px;
  }
  
  .day-number {
    font-size: 0.75rem;
    color: #374151;
    font-weight: 500;
  }
  
  .day-value {
    font-size: 0.75rem;
    font-weight: 600;
    color: #1F2937;
  }
  
  .trade-count {
    position: absolute;
    bottom: 0.125rem;
    right: 0.25rem;
    font-size: 0.625rem;
    color: #6B7280;
    background: rgba(255, 255, 255, 0.8);
    padding: 0 0.25rem;
    border-radius: 2px;
  }
  
  .legend {
    display: flex;
    justify-content: center;
    gap: 1.5rem;
    margin-top: 1rem;
  }
  
  .legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .legend-color {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #E5E7EB;
  }
  
  .legend-item span {
    font-size: 0.75rem;
    color: #6B7280;
  }
  
  .summary {
    display: flex;
    justify-content: space-around;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid #E5E7EB;
  }
  
  .summary-item {
    text-align: center;
  }
  
  .summary-label {
    font-size: 0.75rem;
    color: #6B7280;
    display: block;
  }
  
  .summary-value {
    font-size: 1.125rem;
    font-weight: 600;
    color: #1F2937;
  }
  
  @media (max-width: 480px) {
    .day {
      font-size: 0.625rem;
    }
    
    .day-value {
      font-size: 0.625rem;
    }
  }
</style>