<script lang="ts">
	export let stats = {
		totalTrades: 0,
		totalPnl: 0,
		winRate: 0,
		avgWin: 0,
		avgLoss: 0,
		profitFactor: 0
	};
	
	function formatCurrency(value: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD'
		}).format(value);
	}
</script>

<div class="stats-grid">
	<div class="stat-card">
		<h3>Total Trades</h3>
		<div class="value">{stats.totalTrades}</div>
	</div>
	
	<div class="stat-card">
		<h3>Total P&L</h3>
		<div class="value" class:profit={stats.totalPnl > 0} class:loss={stats.totalPnl < 0}>
			{formatCurrency(stats.totalPnl)}
		</div>
	</div>
	
	<div class="stat-card">
		<h3>Win Rate</h3>
		<div class="value">{stats.winRate.toFixed(1)}%</div>
	</div>
	
	<div class="stat-card">
		<h3>Avg Win</h3>
		<div class="value profit">{formatCurrency(stats.avgWin)}</div>
	</div>
	
	<div class="stat-card">
		<h3>Avg Loss</h3>
		<div class="value loss">{formatCurrency(stats.avgLoss)}</div>
	</div>
	
	<div class="stat-card">
		<h3>Profit Factor</h3>
		<div class="value">{stats.profitFactor.toFixed(2)}</div>
	</div>
</div>

<style>
	.stats-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}
	
	.stat-card {
		background: white;
		padding: 1.5rem;
		border-radius: 8px;
		box-shadow: 0 2px 4px rgba(0,0,0,0.1);
		text-align: center;
	}
	
	.stat-card h3 {
		font-size: 0.875rem;
		color: #666;
		margin-bottom: 0.5rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.value {
		font-size: 1.5rem;
		font-weight: bold;
		color: #333;
	}
</style>