<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	
	const dispatch = createEventDispatcher();
	
	let symbol = '';
	let side = '';
	let dateFrom = '';
	let dateTo = '';
	
	function handleFilter() {
		dispatch('filter', {
			symbol,
			side,
			dateFrom,
			dateTo
		});
	}
	
	function handleReset() {
		symbol = '';
		side = '';
		dateFrom = '';
		dateTo = '';
		handleFilter();
	}
</script>

<div class="filters card">
	<div class="filter-grid">
		<div class="filter-group">
			<label for="symbol">Symbol</label>
			<input 
				id="symbol"
				type="text" 
				bind:value={symbol} 
				on:input={handleFilter}
				placeholder="e.g., AAPL"
			/>
		</div>
		
		<div class="filter-group">
			<label for="side">Side</label>
			<select id="side" bind:value={side} on:change={handleFilter}>
				<option value="">All</option>
				<option value="long">Long</option>
				<option value="short">Short</option>
			</select>
		</div>
		
		<div class="filter-group">
			<label for="dateFrom">From Date</label>
			<input 
				id="dateFrom"
				type="date" 
				bind:value={dateFrom} 
				on:change={handleFilter}
			/>
		</div>
		
		<div class="filter-group">
			<label for="dateTo">To Date</label>
			<input 
				id="dateTo"
				type="date" 
				bind:value={dateTo} 
				on:change={handleFilter}
			/>
		</div>
		
		<div class="filter-group filter-actions">
			<button on:click={handleReset} class="reset">Reset</button>
		</div>
	</div>
</div>

<style>
	.filters {
		margin-bottom: 2rem;
	}
	
	.filter-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		align-items: end;
	}
	
	.filter-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.filter-actions {
		justify-content: flex-end;
	}
	
	label {
		font-size: 0.875rem;
		color: #666;
		font-weight: 500;
	}
	
	input, select {
		padding: 0.5rem;
		border: 1px solid #e0e0e0;
		border-radius: 4px;
		font-size: 1rem;
		background: white;
	}
	
	input:focus, select:focus {
		outline: none;
		border-color: #10b981;
	}
	
	.reset {
		background: #666;
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
	}
	
	.reset:hover {
		background: #555;
	}
</style>