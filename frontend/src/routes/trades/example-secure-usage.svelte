<script lang="ts">
  import { onMount } from 'svelte';
  import { tradingApi } from '$lib/api/client';
  import { validateTrade, debounce } from '$lib/utils/validation';
  import { apiCache, performanceMonitor } from '$lib/utils/cache';
  import type { Trade, PaginatedResponse } from '$lib/types';
  
  // State with proper types
  let trades: Trade[] = [];
  let loading = false;
  let error: string | null = null;
  
  // Form state with validation
  let newTrade = {
    symbol: '',
    quantity: 0,
    price: 0,
    type: 'buy' as 'buy' | 'sell'
  };
  
  // Load trades with caching and error handling
  async function loadTrades() {
    loading = true;
    error = null;
    
    // Mark performance
    performanceMonitor.mark('trades-load-start');
    
    try {
      // This will use cache if available
      const response = await apiCache.fetch(
        'trades-list',
        () => tradingApi.getTrades({ 
          page: 1, 
          pageSize: 50 
        }),
        { ttl: 5 * 60 * 1000 } // 5 minute cache
      );
      
      trades = response.data;
      
      // Measure performance
      const duration = performanceMonitor.measure('trades-load', 'trades-load-start');
      console.log(`Trades loaded in ${duration}ms`);
      
    } catch (err: any) {
      error = err.message || 'Failed to load trades';
      console.error('Error loading trades:', err);
    } finally {
      loading = false;
    }
  }
  
  // Create trade with validation
  async function createTrade() {
    // Validate input
    const validation = validateTrade(newTrade);
    if (!validation.isValid) {
      error = Object.values(validation.errors).join(', ');
      return;
    }
    
    loading = true;
    error = null;
    
    try {
      const trade = await tradingApi.createTrade(newTrade);
      
      // Invalidate cache
      apiCache.invalidate('trades-list');
      
      // Add to list optimistically
      trades = [trade, ...trades];
      
      // Reset form
      newTrade = {
        symbol: '',
        quantity: 0,
        price: 0,
        type: 'buy'
      };
      
    } catch (err: any) {
      error = err.message || 'Failed to create trade';
      
      // Check specific error types
      if (err.statusCode === 429) {
        error = 'Too many requests. Please slow down.';
      } else if (err.statusCode === 401) {
        error = 'Session expired. Please login again.';
      }
    } finally {
      loading = false;
    }
  }
  
  // Debounced search
  const searchTrades = debounce(async (query: string) => {
    if (!query) {
      await loadTrades();
      return;
    }
    
    loading = true;
    try {
      const response = await tradingApi.getTrades({ 
        search: query,
        page: 1,
        pageSize: 50
      });
      trades = response.data;
    } catch (err: any) {
      error = err.message;
    } finally {
      loading = false;
    }
  }, 300);
  
  // Load on mount
  onMount(() => {
    loadTrades();
    
    // Listen for auth events
    const handleUnauthorized = () => {
      error = 'Your session has expired. Please login again.';
    };
    
    window.addEventListener('auth:unauthorized', handleUnauthorized);
    
    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  });
</script>

<div class="container">
  <h1>Secure Trading Example</h1>
  
  <!-- Error Display -->
  {#if error}
    <div class="error-banner">
      {error}
      <button on:click={() => error = null}>Dismiss</button>
    </div>
  {/if}
  
  <!-- Search -->
  <div class="search-bar">
    <input
      type="text"
      placeholder="Search trades..."
      on:input={(e) => searchTrades(e.currentTarget.value)}
      disabled={loading}
    />
  </div>
  
  <!-- Create Trade Form -->
  <form on:submit|preventDefault={createTrade} class="trade-form">
    <input
      type="text"
      bind:value={newTrade.symbol}
      placeholder="Symbol (e.g., AAPL)"
      required
      pattern="[A-Z0-9\-\.]+"
    />
    
    <input
      type="number"
      bind:value={newTrade.quantity}
      placeholder="Quantity"
      min="0.01"
      step="0.01"
      required
    />
    
    <input
      type="number"
      bind:value={newTrade.price}
      placeholder="Price"
      min="0.01"
      step="0.01"
      required
    />
    
    <select bind:value={newTrade.type}>
      <option value="buy">Buy</option>
      <option value="sell">Sell</option>
    </select>
    
    <button type="submit" disabled={loading}>
      {loading ? 'Processing...' : 'Add Trade'}
    </button>
  </form>
  
  <!-- Trades List -->
  {#if loading && trades.length === 0}
    <div class="loading">Loading trades...</div>
  {:else if trades.length === 0}
    <div class="empty">No trades found</div>
  {:else}
    <div class="trades-list">
      {#each trades as trade (trade.id)}
        <div class="trade-card">
          <h3>{trade.symbol}</h3>
          <p>{trade.type} {trade.quantity} @ ${trade.price}</p>
          <time>{new Date(trade.executedAt).toLocaleDateString()}</time>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  .error-banner {
    background: #fee;
    border: 1px solid #fcc;
    color: #c00;
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .search-bar {
    margin-bottom: 2rem;
  }
  
  .search-bar input {
    width: 100%;
    padding: 0.75rem;
    font-size: 1rem;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  
  .trade-form {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr auto;
    gap: 1rem;
    margin-bottom: 2rem;
  }
  
  .trade-form input,
  .trade-form select {
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  
  .trade-form button {
    padding: 0.5rem 1rem;
    background: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .trade-form button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .trades-list {
    display: grid;
    gap: 1rem;
  }
  
  .trade-card {
    padding: 1rem;
    border: 1px solid #eee;
    border-radius: 4px;
    background: #fafafa;
  }
  
  .loading,
  .empty {
    text-align: center;
    padding: 3rem;
    color: #666;
  }
</style>