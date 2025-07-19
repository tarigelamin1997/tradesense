<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { TrendingUp, TrendingDown, Minus } from 'lucide-svelte';
  
  export let symbols: string[] = ['SPY', 'QQQ', 'IWM', 'DIA'];
  export let title: string = 'Market Overview';
  export let refreshInterval: number = 5000; // 5 seconds
  export let height: string = '100%';
  
  interface MarketData {
    symbol: string;
    price: number;
    change: number;
    changePercent: number;
    volume: number;
    high: number;
    low: number;
    open: number;
    previousClose: number;
    lastUpdate: Date;
  }
  
  let marketData: MarketData[] = [];
  let loading = true;
  let error = '';
  let intervalId: number;
  
  // Generate mock data for demo
  function generateMockData(): MarketData[] {
    return symbols.map(symbol => {
      const basePrice = {
        SPY: 450,
        QQQ: 380,
        IWM: 220,
        DIA: 380,
        AAPL: 185,
        TSLA: 250,
        MSFT: 380,
        GOOGL: 140
      }[symbol] || 100;
      
      const change = (Math.random() - 0.5) * 5;
      const price = basePrice + change;
      
      return {
        symbol,
        price,
        change,
        changePercent: (change / basePrice) * 100,
        volume: Math.floor(Math.random() * 100000000),
        high: price + Math.random() * 2,
        low: price - Math.random() * 2,
        open: basePrice,
        previousClose: basePrice,
        lastUpdate: new Date()
      };
    });
  }
  
  async function fetchMarketData() {
    try {
      // In production, this would call your market data API
      // For now, using mock data
      marketData = generateMockData();
      loading = false;
    } catch (err) {
      error = 'Failed to fetch market data';
      loading = false;
    }
  }
  
  function getChangeIcon(change: number) {
    if (change > 0) return TrendingUp;
    if (change < 0) return TrendingDown;
    return Minus;
  }
  
  function getChangeColor(change: number) {
    if (change > 0) return '#10B981';
    if (change < 0) return '#EF4444';
    return '#6B7280';
  }
  
  function formatVolume(volume: number): string {
    if (volume >= 1000000000) {
      return (volume / 1000000000).toFixed(1) + 'B';
    }
    if (volume >= 1000000) {
      return (volume / 1000000).toFixed(1) + 'M';
    }
    if (volume >= 1000) {
      return (volume / 1000).toFixed(1) + 'K';
    }
    return volume.toString();
  }
  
  onMount(() => {
    fetchMarketData();
    
    if (refreshInterval > 0) {
      intervalId = setInterval(fetchMarketData, refreshInterval);
    }
  });
  
  onDestroy(() => {
    if (intervalId) {
      clearInterval(intervalId);
    }
  });
</script>

<div class="live-market-widget" style="height: {height}">
  {#if loading}
    <div class="loading">Loading market data...</div>
  {:else if error}
    <div class="error">{error}</div>
  {:else}
    <div class="market-grid">
      {#each marketData as data}
        <div class="market-card">
          <div class="symbol-row">
            <span class="symbol">{data.symbol}</span>
            <svelte:component 
              this={getChangeIcon(data.change)} 
              size={16} 
              color={getChangeColor(data.change)}
            />
          </div>
          
          <div class="price-row">
            <span class="price">${data.price.toFixed(2)}</span>
          </div>
          
          <div class="change-row">
            <span 
              class="change"
              style="color: {getChangeColor(data.change)}"
            >
              {data.change >= 0 ? '+' : ''}{data.change.toFixed(2)}
            </span>
            <span 
              class="change-percent"
              style="color: {getChangeColor(data.change)}"
            >
              ({data.changePercent >= 0 ? '+' : ''}{data.changePercent.toFixed(2)}%)
            </span>
          </div>
          
          <div class="stats-row">
            <div class="stat">
              <span class="stat-label">Vol</span>
              <span class="stat-value">{formatVolume(data.volume)}</span>
            </div>
            <div class="stat">
              <span class="stat-label">High</span>
              <span class="stat-value">${data.high.toFixed(2)}</span>
            </div>
            <div class="stat">
              <span class="stat-label">Low</span>
              <span class="stat-value">${data.low.toFixed(2)}</span>
            </div>
          </div>
        </div>
      {/each}
    </div>
    
    <div class="update-time">
      Last updated: {new Date().toLocaleTimeString()}
    </div>
  {/if}
</div>

<style>
  .live-market-widget {
    width: 100%;
    padding: 1rem;
    display: flex;
    flex-direction: column;
  }
  
  .loading, .error {
    text-align: center;
    padding: 2rem;
    color: #6B7280;
  }
  
  .error {
    color: #EF4444;
  }
  
  .market-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    flex: 1;
  }
  
  .market-card {
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 1rem;
    transition: all 0.2s;
  }
  
  .market-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  .symbol-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }
  
  .symbol {
    font-weight: 600;
    font-size: 1rem;
    color: #1F2937;
  }
  
  .price-row {
    margin-bottom: 0.25rem;
  }
  
  .price {
    font-size: 1.5rem;
    font-weight: 700;
    color: #111827;
  }
  
  .change-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    margin-bottom: 0.75rem;
    font-size: 0.875rem;
    font-weight: 500;
  }
  
  .stats-row {
    display: flex;
    justify-content: space-between;
    padding-top: 0.75rem;
    border-top: 1px solid #E5E7EB;
  }
  
  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  .stat-label {
    font-size: 0.625rem;
    color: #9CA3AF;
    text-transform: uppercase;
    margin-bottom: 0.125rem;
  }
  
  .stat-value {
    font-size: 0.75rem;
    color: #4B5563;
    font-weight: 500;
  }
  
  .update-time {
    text-align: center;
    font-size: 0.75rem;
    color: #9CA3AF;
    margin-top: 1rem;
  }
  
  @media (max-width: 768px) {
    .market-grid {
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    }
    
    .price {
      font-size: 1.25rem;
    }
  }
</style>