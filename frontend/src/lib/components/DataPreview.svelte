<script lang="ts">
	import { Eye, EyeOff } from 'lucide-svelte';
	
	export let data: any[] = [];
	export let columns: string[] = [];
	export let title = 'Data Preview';
	export let maxRows = 10;
	
	let showAll = false;
	$: displayData = showAll ? data : data.slice(0, maxRows);
	$: hasMore = data.length > maxRows;
</script>

<div class="data-preview">
	<div class="preview-header">
		<h3>{title}</h3>
		<p>Showing {displayData.length} of {data.length} rows</p>
		{#if hasMore}
			<button
				type="button"
				class="toggle-btn"
				on:click={() => showAll = !showAll}
			>
				{#if showAll}
					<EyeOff size={16} />
					Show Less
				{:else}
					<Eye size={16} />
					Show All
				{/if}
			</button>
		{/if}
	</div>
	
	{#if data.length > 0}
		<div class="table-container">
			<table>
				<thead>
					<tr>
						<th class="row-number">#</th>
						{#each columns as column}
							<th>{column}</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each displayData as row, index}
						<tr>
							<td class="row-number">{index + 1}</td>
							{#each columns as column}
								<td>
									{#if row[column] !== null && row[column] !== undefined}
										{row[column]}
									{:else}
										<span class="empty">-</span>
									{/if}
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		
		{#if hasMore && !showAll}
			<div class="more-indicator">
				... and {data.length - maxRows} more rows
			</div>
		{/if}
	{:else}
		<div class="no-data">
			No data to preview
		</div>
	{/if}
</div>

<style>
	.data-preview {
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		padding: 1.5rem;
		margin-top: 1rem;
	}
	
	.preview-header {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 1rem;
		flex-wrap: wrap;
	}
	
	.preview-header h3 {
		font-size: 1.125rem;
		font-weight: 600;
		margin: 0;
		flex: 1;
	}
	
	.preview-header p {
		font-size: 0.875rem;
		color: #666;
		margin: 0;
	}
	
	.toggle-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: #f3f4f6;
		border: none;
		border-radius: 6px;
		font-size: 0.875rem;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.toggle-btn:hover {
		background: #e5e7eb;
		color: #333;
	}
	
	.table-container {
		overflow-x: auto;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
	}
	
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}
	
	thead {
		background: #f9f9f9;
		border-bottom: 2px solid #e0e0e0;
	}
	
	th {
		padding: 0.75rem 1rem;
		text-align: left;
		font-weight: 600;
		color: #666;
		white-space: nowrap;
		position: sticky;
		top: 0;
		background: #f9f9f9;
		z-index: 1;
	}
	
	th.row-number {
		width: 50px;
		text-align: center;
		color: #999;
	}
	
	tbody tr {
		border-bottom: 1px solid #f0f0f0;
	}
	
	tbody tr:hover {
		background: #fafafa;
	}
	
	tbody tr:last-child {
		border-bottom: none;
	}
	
	td {
		padding: 0.75rem 1rem;
		color: #333;
		max-width: 200px;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	td.row-number {
		text-align: center;
		color: #999;
		font-size: 0.75rem;
		background: #fafafa;
		font-weight: 500;
	}
	
	.empty {
		color: #ccc;
	}
	
	.more-indicator {
		text-align: center;
		padding: 1rem;
		color: #666;
		font-size: 0.875rem;
		font-style: italic;
		border-top: 1px solid #f0f0f0;
		margin-top: 1rem;
	}
	
	.no-data {
		text-align: center;
		padding: 3rem;
		color: #999;
		font-size: 0.875rem;
	}
	
	@media (max-width: 768px) {
		.data-preview {
			padding: 1rem;
		}
		
		th, td {
			padding: 0.5rem;
			font-size: 0.75rem;
		}
		
		td {
			max-width: 120px;
		}
	}
</style>