<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Edit, Copy, Trash2, TrendingUp, TrendingDown, Target, AlertTriangle } from 'lucide-svelte';
	
	export let playbook: any;
	
	const dispatch = createEventDispatcher();
	
	function handleEdit() {
		dispatch('edit');
	}
	
	function handleClone() {
		dispatch('clone');
	}
	
	function handleDelete() {
		dispatch('delete');
	}
	
	function formatDate(dateString: string) {
		const date = new Date(dateString);
		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}
</script>

<div class="playbook-detail card">
	<div class="detail-header">
		<div>
			<h2>{playbook.title}</h2>
			<div class="detail-meta">
				<span class="strategy-type">{playbook.strategy_type}</span>
				<span>{playbook.timeframe}</span>
				<span class="status" class:active={playbook.is_active}>
					{playbook.is_active ? 'Active' : 'Inactive'}
				</span>
			</div>
		</div>
		<div class="detail-actions">
			<button class="icon-button" on:click={handleEdit} title="Edit">
				<Edit size={18} />
			</button>
			<button class="icon-button" on:click={handleClone} title="Clone">
				<Copy size={18} />
			</button>
			<button class="icon-button danger" on:click={handleDelete} title="Delete">
				<Trash2 size={18} />
			</button>
		</div>
	</div>
	
	<!-- Market Conditions -->
	<section class="detail-section">
		<h3>Market Conditions</h3>
		<p>{playbook.market_conditions}</p>
	</section>
	
	<!-- Entry Rules -->
	<section class="detail-section">
		<h3><Target size={18} /> Entry Rules</h3>
		<ol class="rules-list">
			{#each playbook.entry_rules as rule}
				<li>{rule}</li>
			{/each}
		</ol>
	</section>
	
	<!-- Exit Rules -->
	<section class="detail-section">
		<h3><AlertTriangle size={18} /> Exit Rules</h3>
		<ol class="rules-list">
			{#each playbook.exit_rules as rule}
				<li>{rule}</li>
			{/each}
		</ol>
	</section>
	
	<!-- Risk Management -->
	<section class="detail-section">
		<h3>Risk Management</h3>
		<div class="risk-grid">
			<div class="risk-item">
				<h4>Risk Rules</h4>
				<p>{playbook.risk_management}</p>
			</div>
			<div class="risk-item">
				<h4>Position Sizing</h4>
				<p>{playbook.position_sizing}</p>
			</div>
		</div>
	</section>
	
	<!-- Indicators -->
	{#if playbook.indicators.length > 0}
		<section class="detail-section">
			<h3>Indicators</h3>
			<div class="indicators">
				{#each playbook.indicators as indicator}
					<span class="indicator-tag">{indicator}</span>
				{/each}
			</div>
		</section>
	{/if}
	
	<!-- Backtest Results -->
	{#if playbook.backtest_results}
		<section class="detail-section">
			<h3>Backtest Results</h3>
			<div class="backtest-results">
				<div class="metric">
					<span class="metric-label">Win Rate</span>
					<span class="metric-value" class:positive={playbook.backtest_results.win_rate >= 50}>
						{playbook.backtest_results.win_rate}%
					</span>
				</div>
				<div class="metric">
					<span class="metric-label">Profit Factor</span>
					<span class="metric-value" class:positive={playbook.backtest_results.profit_factor >= 1.5}>
						{playbook.backtest_results.profit_factor}
					</span>
				</div>
				<div class="metric">
					<span class="metric-label">Avg Win</span>
					<span class="metric-value positive">
						${playbook.backtest_results.avg_win}
					</span>
				</div>
				<div class="metric">
					<span class="metric-label">Avg Loss</span>
					<span class="metric-value negative">
						-${playbook.backtest_results.avg_loss}
					</span>
				</div>
				<div class="metric">
					<span class="metric-label">Max Drawdown</span>
					<span class="metric-value negative">
						-{playbook.backtest_results.max_drawdown}%
					</span>
				</div>
			</div>
		</section>
	{/if}
	
	<!-- Notes -->
	{#if playbook.notes}
		<section class="detail-section">
			<h3>Notes</h3>
			<p class="notes">{playbook.notes}</p>
		</section>
	{/if}
	
	<!-- Tags -->
	{#if playbook.tags.length > 0}
		<section class="detail-section">
			<h3>Tags</h3>
			<div class="tags">
				{#each playbook.tags as tag}
					<span class="tag">{tag}</span>
				{/each}
			</div>
		</section>
	{/if}
	
	<!-- Footer -->
	<div class="detail-footer">
		<div class="footer-meta">
			<span>Created: {formatDate(playbook.created_at)}</span>
			<span>Updated: {formatDate(playbook.updated_at)}</span>
		</div>
	</div>
</div>

<style>
	.playbook-detail {
		padding: 2rem;
		position: sticky;
		top: 1rem;
		max-height: calc(100vh - 200px);
		overflow-y: auto;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 2rem;
		padding-bottom: 1.5rem;
		border-bottom: 2px solid #e0e0e0;
	}
	
	.detail-header h2 {
		font-size: 1.75rem;
		margin-bottom: 0.5rem;
		color: #1a1a1a;
	}
	
	.detail-meta {
		display: flex;
		gap: 1rem;
		align-items: center;
	}
	
	.strategy-type {
		background: #e0f2fe;
		color: #0369a1;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.875rem;
		text-transform: capitalize;
	}
	
	.status {
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.875rem;
		background: #fee;
		color: #dc2626;
	}
	
	.status.active {
		background: #d1fae5;
		color: #059669;
	}
	
	.detail-actions {
		display: flex;
		gap: 0.5rem;
	}
	
	.icon-button {
		padding: 0.5rem;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.icon-button:hover {
		background: #f3f4f6;
		border-color: #d1d5db;
		color: #333;
	}
	
	.icon-button.danger:hover {
		background: #fef2f2;
		border-color: #fecaca;
		color: #ef4444;
	}
	
	.detail-section {
		margin-bottom: 2rem;
	}
	
	.detail-section h3 {
		font-size: 1.25rem;
		margin-bottom: 1rem;
		color: #333;
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.detail-section p {
		color: #666;
		line-height: 1.6;
	}
	
	.rules-list {
		list-style: none;
		padding: 0;
		counter-reset: rule-counter;
	}
	
	.rules-list li {
		counter-increment: rule-counter;
		position: relative;
		padding-left: 2rem;
		margin-bottom: 0.75rem;
		line-height: 1.6;
		color: #333;
	}
	
	.rules-list li::before {
		content: counter(rule-counter);
		position: absolute;
		left: 0;
		top: 0;
		width: 1.5rem;
		height: 1.5rem;
		background: #10b981;
		color: white;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.875rem;
		font-weight: 600;
	}
	
	.risk-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1.5rem;
	}
	
	.risk-item {
		padding: 1rem;
		background: #f9fafb;
		border-radius: 8px;
	}
	
	.risk-item h4 {
		font-size: 0.875rem;
		font-weight: 600;
		color: #666;
		margin-bottom: 0.5rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	
	.risk-item p {
		margin: 0;
		font-size: 0.875rem;
	}
	
	.indicators {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}
	
	.indicator-tag {
		background: #fef3c7;
		color: #92400e;
		padding: 0.375rem 1rem;
		border-radius: 20px;
		font-size: 0.875rem;
		font-weight: 500;
	}
	
	.backtest-results {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
		padding: 1.5rem;
		background: #f9fafb;
		border-radius: 8px;
	}
	
	.metric {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
	}
	
	.metric-label {
		font-size: 0.75rem;
		color: #666;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 0.25rem;
	}
	
	.metric-value {
		font-size: 1.5rem;
		font-weight: 600;
		color: #333;
	}
	
	.metric-value.positive {
		color: #10b981;
	}
	
	.metric-value.negative {
		color: #ef4444;
	}
	
	.notes {
		background: #f9fafb;
		padding: 1rem;
		border-radius: 8px;
		font-size: 0.875rem;
		line-height: 1.6;
	}
	
	.tags {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
	}
	
	.tag {
		background: #e0e7ff;
		color: #4338ca;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.875rem;
	}
	
	.detail-footer {
		margin-top: 2rem;
		padding-top: 1.5rem;
		border-top: 1px solid #e0e0e0;
	}
	
	.footer-meta {
		display: flex;
		gap: 2rem;
		font-size: 0.875rem;
		color: #999;
	}
	
	@media (max-width: 1024px) {
		.playbook-detail {
			position: static;
			max-height: none;
		}
		
		.risk-grid {
			grid-template-columns: 1fr;
		}
	}
	
	@media (max-width: 640px) {
		.detail-header {
			flex-direction: column;
			gap: 1rem;
		}
		
		.backtest-results {
			grid-template-columns: 1fr 1fr;
		}
		
		.footer-meta {
			flex-direction: column;
			gap: 0.5rem;
		}
	}
</style>