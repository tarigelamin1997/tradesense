<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Trash2, Download, Tag, Edit, X, CheckSquare, Square, MinusSquare } from 'lucide-svelte';
	
	export let selectedCount = 0;
	export let totalCount = 0;
	export let isAllSelected = false;
	export let isPartiallySelected = false;
	
	const dispatch = createEventDispatcher();
	
	let showBulkEdit = false;
	let bulkEditData = {
		strategy: '',
		side: '',
		updateStrategy: false,
		updateSide: false
	};
	
	let showBulkTag = false;
	let tagInput = '';
	
	function handleSelectAll() {
		if (isAllSelected) {
			dispatch('deselectAll');
		} else {
			dispatch('selectAll');
		}
	}
	
	function handleBulkDelete() {
		if (confirm(`Are you sure you want to delete ${selectedCount} trades? This action cannot be undone.`)) {
			dispatch('bulkDelete');
		}
	}
	
	function handleBulkExport() {
		dispatch('bulkExport');
	}
	
	function handleBulkEdit() {
		const updates: any = {};
		
		if (bulkEditData.updateStrategy && bulkEditData.strategy) {
			updates.strategy = bulkEditData.strategy;
		}
		
		if (bulkEditData.updateSide && bulkEditData.side) {
			updates.side = bulkEditData.side;
		}
		
		if (Object.keys(updates).length > 0) {
			dispatch('bulkEdit', { updates });
			showBulkEdit = false;
			bulkEditData = {
				strategy: '',
				side: '',
				updateStrategy: false,
				updateSide: false
			};
		}
	}
	
	function handleBulkTag() {
		if (tagInput.trim()) {
			dispatch('bulkTag', { tag: tagInput.trim() });
			showBulkTag = false;
			tagInput = '';
		}
	}
	
	function handleClearSelection() {
		dispatch('deselectAll');
	}
	
	// Common strategies (should match the trade form)
	const strategies = [
		'Momentum',
		'Mean Reversion',
		'Breakout',
		'Scalping',
		'Swing Trading',
		'Position Trading',
		'Day Trading',
		'News Trading',
		'Pairs Trading'
	];
</script>

{#if selectedCount > 0}
	<div class="bulk-actions-bar">
		<div class="selection-info">
			<button
				type="button"
				class="select-all-button"
				on:click={handleSelectAll}
				title={isAllSelected ? 'Deselect all' : 'Select all'}
			>
				{#if isAllSelected}
					<CheckSquare size={20} />
				{:else if isPartiallySelected}
					<MinusSquare size={20} />
				{:else}
					<Square size={20} />
				{/if}
			</button>
			
			<span class="selection-count">
				{selectedCount} of {totalCount} selected
			</span>
			
			<button
				type="button"
				class="clear-selection"
				on:click={handleClearSelection}
				title="Clear selection"
			>
				<X size={16} />
			</button>
		</div>
		
		<div class="bulk-actions">
			<button
				type="button"
				class="bulk-action"
				on:click={() => showBulkEdit = true}
				title="Edit selected trades"
			>
				<Edit size={16} />
				Edit
			</button>
			
			<button
				type="button"
				class="bulk-action"
				on:click={() => showBulkTag = true}
				title="Tag selected trades"
			>
				<Tag size={16} />
				Tag
			</button>
			
			<button
				type="button"
				class="bulk-action"
				on:click={handleBulkExport}
				title="Export selected trades"
			>
				<Download size={16} />
				Export
			</button>
			
			<div class="separator"></div>
			
			<button
				type="button"
				class="bulk-action danger"
				on:click={handleBulkDelete}
				title="Delete selected trades"
			>
				<Trash2 size={16} />
				Delete
			</button>
		</div>
		
		<!-- Bulk Edit Modal -->
		{#if showBulkEdit}
			<div class="modal-backdrop" on:click={() => showBulkEdit = false}>
				<div class="modal" on:click|stopPropagation>
					<div class="modal-header">
						<h3>Edit {selectedCount} Trades</h3>
						<button type="button" class="close-button" on:click={() => showBulkEdit = false}>
							<X size={20} />
						</button>
					</div>
					
					<div class="modal-body">
						<p class="modal-description">
							Select the fields you want to update for all selected trades.
						</p>
						
						<div class="edit-field">
							<label class="checkbox-label">
								<input
									type="checkbox"
									bind:checked={bulkEditData.updateStrategy}
								/>
								<span>Update Strategy</span>
							</label>
							{#if bulkEditData.updateStrategy}
								<select bind:value={bulkEditData.strategy}>
									<option value="">Select strategy...</option>
									{#each strategies as strategy}
										<option value={strategy}>{strategy}</option>
									{/each}
								</select>
							{/if}
						</div>
						
						<div class="edit-field">
							<label class="checkbox-label">
								<input
									type="checkbox"
									bind:checked={bulkEditData.updateSide}
								/>
								<span>Update Side</span>
							</label>
							{#if bulkEditData.updateSide}
								<select bind:value={bulkEditData.side}>
									<option value="">Select side...</option>
									<option value="long">Long</option>
									<option value="short">Short</option>
								</select>
							{/if}
						</div>
					</div>
					
					<div class="modal-footer">
						<button type="button" class="cancel-button" on:click={() => showBulkEdit = false}>
							Cancel
						</button>
						<button
							type="button"
							class="save-button"
							on:click={handleBulkEdit}
							disabled={(!bulkEditData.updateStrategy || !bulkEditData.strategy) && 
								(!bulkEditData.updateSide || !bulkEditData.side)}
						>
							Update Trades
						</button>
					</div>
				</div>
			</div>
		{/if}
		
		<!-- Bulk Tag Modal -->
		{#if showBulkTag}
			<div class="modal-backdrop" on:click={() => showBulkTag = false}>
				<div class="modal" on:click|stopPropagation>
					<div class="modal-header">
						<h3>Tag {selectedCount} Trades</h3>
						<button type="button" class="close-button" on:click={() => showBulkTag = false}>
							<X size={20} />
						</button>
					</div>
					
					<div class="modal-body">
						<p class="modal-description">
							Add a tag to all selected trades. This will append to existing notes.
						</p>
						
						<input
							type="text"
							bind:value={tagInput}
							placeholder="Enter tag..."
							on:keypress={(e) => e.key === 'Enter' && handleBulkTag()}
							class="tag-input"
						/>
						
						<div class="tag-suggestions">
							<span>Suggestions:</span>
							<button type="button" on:click={() => tagInput = 'reviewed'}>reviewed</button>
							<button type="button" on:click={() => tagInput = 'profitable'}>profitable</button>
							<button type="button" on:click={() => tagInput = 'mistake'}>mistake</button>
							<button type="button" on:click={() => tagInput = 'learning'}>learning</button>
						</div>
					</div>
					
					<div class="modal-footer">
						<button type="button" class="cancel-button" on:click={() => showBulkTag = false}>
							Cancel
						</button>
						<button
							type="button"
							class="save-button"
							on:click={handleBulkTag}
							disabled={!tagInput.trim()}
						>
							Add Tag
						</button>
					</div>
				</div>
			</div>
		{/if}
	</div>
{/if}

<style>
	.bulk-actions-bar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem;
		background: #f9fafb;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		margin-bottom: 1rem;
		gap: 1rem;
		flex-wrap: wrap;
		animation: slideIn 0.2s ease-out;
	}
	
	@keyframes slideIn {
		from {
			opacity: 0;
			transform: translateY(-10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	
	.selection-info {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	
	.select-all-button {
		background: none;
		border: none;
		padding: 0.25rem;
		cursor: pointer;
		color: #666;
		display: flex;
		align-items: center;
		border-radius: 4px;
		transition: all 0.2s;
	}
	
	.select-all-button:hover {
		background: #e5e7eb;
		color: #333;
	}
	
	.selection-count {
		font-size: 0.875rem;
		font-weight: 500;
		color: #333;
	}
	
	.clear-selection {
		background: none;
		border: none;
		padding: 0.25rem;
		cursor: pointer;
		color: #999;
		display: flex;
		align-items: center;
		border-radius: 4px;
		transition: all 0.2s;
	}
	
	.clear-selection:hover {
		background: #e5e7eb;
		color: #666;
	}
	
	.bulk-actions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	
	.bulk-action {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 0.875rem;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
		white-space: nowrap;
	}
	
	.bulk-action:hover {
		background: #f3f4f6;
		border-color: #d1d5db;
		color: #333;
	}
	
	.bulk-action.danger {
		color: #dc2626;
		border-color: #fee;
	}
	
	.bulk-action.danger:hover {
		background: #fef2f2;
		border-color: #fecaca;
	}
	
	.separator {
		width: 1px;
		height: 24px;
		background: #e5e7eb;
		margin: 0 0.5rem;
	}
	
	/* Modal Styles */
	.modal-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 1rem;
	}
	
	.modal {
		background: white;
		border-radius: 12px;
		box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
		max-width: 500px;
		width: 100%;
	}
	
	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		border-bottom: 1px solid #e0e0e0;
	}
	
	.modal-header h3 {
		font-size: 1.25rem;
		margin: 0;
	}
	
	.close-button {
		background: none;
		border: none;
		color: #666;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 6px;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.close-button:hover {
		background: #f3f4f6;
		color: #333;
	}
	
	.modal-body {
		padding: 1.5rem;
	}
	
	.modal-description {
		color: #666;
		margin: 0 0 1.5rem 0;
		line-height: 1.5;
	}
	
	.edit-field {
		margin-bottom: 1.5rem;
	}
	
	.checkbox-label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
		margin-bottom: 0.75rem;
	}
	
	.checkbox-label input {
		cursor: pointer;
	}
	
	.checkbox-label span {
		font-weight: 500;
		color: #333;
	}
	
	.edit-field select {
		width: 100%;
		padding: 0.625rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 0.875rem;
		background: white;
		cursor: pointer;
	}
	
	.tag-input {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 1rem;
		margin-bottom: 1rem;
	}
	
	.tag-input:focus {
		outline: none;
		border-color: #10b981;
	}
	
	.tag-suggestions {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}
	
	.tag-suggestions span {
		font-size: 0.875rem;
		color: #666;
	}
	
	.tag-suggestions button {
		padding: 0.25rem 0.75rem;
		background: #f3f4f6;
		border: 1px solid #e5e7eb;
		border-radius: 16px;
		font-size: 0.875rem;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.tag-suggestions button:hover {
		background: #e5e7eb;
		border-color: #d1d5db;
		color: #333;
	}
	
	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: 1rem;
		padding: 1.5rem;
		border-top: 1px solid #e0e0e0;
		background: #f9fafb;
		border-radius: 0 0 12px 12px;
	}
	
	.cancel-button, .save-button {
		padding: 0.625rem 1.25rem;
		border: none;
		border-radius: 6px;
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.cancel-button {
		background: white;
		color: #666;
		border: 1px solid #e0e0e0;
	}
	
	.cancel-button:hover {
		background: #f3f4f6;
		border-color: #d1d5db;
		color: #333;
	}
	
	.save-button {
		background: #10b981;
		color: white;
	}
	
	.save-button:hover:not(:disabled) {
		background: #059669;
	}
	
	.save-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
	
	@media (max-width: 640px) {
		.bulk-actions-bar {
			flex-direction: column;
			align-items: stretch;
		}
		
		.bulk-actions {
			justify-content: center;
			flex-wrap: wrap;
		}
	}
</style>