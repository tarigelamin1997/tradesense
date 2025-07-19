<script lang="ts">
	import { priceUpdates } from '$lib/stores/websocket';
	import { TrendingUp, TrendingDown } from 'lucide-svelte';
	
	export let symbols: string[] = ['SPY', 'QQQ', 'IWM', 'VIX'];
	
	interface PriceData {
		symbol: string;
		price: number;
		change: number;
		changePercent: number;
		prevPrice: number;
	}
	
	let prices: Record<string, PriceData> = {};
	let animatingSymbols = new Set<string>();
	
	// Initialize with dummy data
	symbols.forEach(symbol => {
		prices[symbol] = {
			symbol,
			price: Math.random() * 500 + 100,
			change: (Math.random() - 0.5) * 10,
			changePercent: (Math.random() - 0.5) * 5,
			prevPrice: 0
		};
	});
	
	// Handle real-time price updates
	$: if ($priceUpdates) {
		handlePriceUpdate($priceUpdates);
	}
	
	function handlePriceUpdate(update: any) {
		if (update.symbol && prices[update.symbol]) {
			const prevPrice = prices[update.symbol].price;
			
			prices[update.symbol] = {
				...prices[update.symbol],
				price: update.price,
				change: update.change || update.price - prevPrice,
				changePercent: update.changePercent || ((update.price - prevPrice) / prevPrice) * 100,
				prevPrice
			};
			
			// Trigger animation
			animatingSymbols.add(update.symbol);
			setTimeout(() => {
				animatingSymbols.delete(update.symbol);
				animatingSymbols = animatingSymbols; // Trigger reactivity
			}, 500);
		}
	}
	
	function formatPrice(price: number): string {
		return price.toFixed(2);
	}
	
	function formatChange(change: number): string {
		return (change >= 0 ? '+' : '') + change.toFixed(2);
	}
	
	function formatPercent(percent: number): string {
		return (percent >= 0 ? '+' : '') + percent.toFixed(2) + '%';
	}
</script>

<div class="price-ticker">
	<div class="ticker-wrapper">
		<div class="ticker-items">
			{#each Object.values(prices) as price}
				<div 
					class="ticker-item"
					class:positive={price.change >= 0}
					class:negative={price.change < 0}
					class:animating={animatingSymbols.has(price.symbol)}
				>
					<div class="symbol">{price.symbol}</div>
					<div class="price">${formatPrice(price.price)}</div>
					<div class="change">
						{#if price.change >= 0}
							<TrendingUp size={14} />
						{:else}
							<TrendingDown size={14} />
						{/if}
						<span>{formatChange(price.change)}</span>
						<span class="percent">({formatPercent(price.changePercent)})</span>
					</div>
				</div>
			{/each}
		</div>
	</div>
</div>

<style>
	.price-ticker {
		background: #1a1a1a;
		color: white;
		padding: 0.75rem 0;
		overflow: hidden;
		position: relative;
	}
	
	.ticker-wrapper {
		max-width: 1200px;
		margin: 0 auto;
		padding: 0 2rem;
	}
	
	.ticker-items {
		display: flex;
		gap: 2rem;
		overflow-x: auto;
		scrollbar-width: none;
		-ms-overflow-style: none;
	}
	
	.ticker-items::-webkit-scrollbar {
		display: none;
	}
	
	.ticker-item {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.5rem 1rem;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 8px;
		transition: all 0.3s;
		white-space: nowrap;
	}
	
	.ticker-item.animating {
		animation: pulse 0.5s ease-out;
	}
	
	@keyframes pulse {
		0% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.05);
		}
		100% {
			transform: scale(1);
		}
	}
	
	.symbol {
		font-weight: 600;
		font-size: 0.875rem;
	}
	
	.price {
		font-size: 1rem;
		font-weight: 500;
	}
	
	.change {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.875rem;
	}
	
	.ticker-item.positive .change {
		color: #10b981;
	}
	
	.ticker-item.negative .change {
		color: #ef4444;
	}
	
	.percent {
		font-size: 0.75rem;
		opacity: 0.8;
	}
	
	@media (max-width: 768px) {
		.ticker-wrapper {
			padding: 0 1rem;
		}
		
		.ticker-items {
			gap: 1rem;
		}
		
		.ticker-item {
			padding: 0.25rem 0.75rem;
			gap: 0.5rem;
		}
		
		.symbol {
			font-size: 0.75rem;
		}
		
		.price {
			font-size: 0.875rem;
		}
		
		.change {
			font-size: 0.75rem;
		}
	}
</style>