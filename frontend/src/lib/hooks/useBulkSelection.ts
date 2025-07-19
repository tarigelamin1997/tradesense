import { writable, derived } from 'svelte/store';

export interface BulkSelectionOptions<T> {
	idField?: keyof T;
}

export function useBulkSelection<T extends Record<string, any>>(
	items: T[],
	options: BulkSelectionOptions<T> = {}
) {
	const { idField = 'id' } = options;
	
	// Store for selected item IDs
	const selectedIds = writable<Set<any>>(new Set());
	
	// Derived store for selected items
	const selectedItems = derived(
		selectedIds,
		($selectedIds) => items.filter(item => $selectedIds.has(item[idField]))
	);
	
	// Derived store for selection state
	const selectionState = derived(
		selectedIds,
		($selectedIds) => ({
			count: $selectedIds.size,
			hasSelection: $selectedIds.size > 0,
			isAllSelected: items.length > 0 && $selectedIds.size === items.length,
			isPartiallySelected: $selectedIds.size > 0 && $selectedIds.size < items.length
		})
	);
	
	// Select a single item
	function select(item: T) {
		selectedIds.update(ids => {
			const newIds = new Set(ids);
			newIds.add(item[idField]);
			return newIds;
		});
	}
	
	// Deselect a single item
	function deselect(item: T) {
		selectedIds.update(ids => {
			const newIds = new Set(ids);
			newIds.delete(item[idField]);
			return newIds;
		});
	}
	
	// Toggle selection of a single item
	function toggle(item: T) {
		selectedIds.update(ids => {
			const newIds = new Set(ids);
			const id = item[idField];
			
			if (newIds.has(id)) {
				newIds.delete(id);
			} else {
				newIds.add(id);
			}
			
			return newIds;
		});
	}
	
	// Select all items
	function selectAll() {
		selectedIds.set(new Set(items.map(item => item[idField])));
	}
	
	// Deselect all items
	function deselectAll() {
		selectedIds.set(new Set());
	}
	
	// Toggle all items
	function toggleAll() {
		selectedIds.update(ids => {
			if (ids.size === items.length) {
				return new Set();
			} else {
				return new Set(items.map(item => item[idField]));
			}
		});
	}
	
	// Select items by a predicate
	function selectBy(predicate: (item: T) => boolean) {
		const itemsToSelect = items.filter(predicate);
		selectedIds.update(ids => {
			const newIds = new Set(ids);
			itemsToSelect.forEach(item => newIds.add(item[idField]));
			return newIds;
		});
	}
	
	// Deselect items by a predicate
	function deselectBy(predicate: (item: T) => boolean) {
		const itemsToDeselect = items.filter(predicate);
		selectedIds.update(ids => {
			const newIds = new Set(ids);
			itemsToDeselect.forEach(item => newIds.delete(item[idField]));
			return newIds;
		});
	}
	
	// Check if an item is selected
	function isSelected(item: T): boolean {
		let selected = false;
		selectedIds.subscribe(ids => {
			selected = ids.has(item[idField]);
		})();
		return selected;
	}
	
	// Get selected IDs as array
	function getSelectedIds(): any[] {
		let ids: any[] = [];
		selectedIds.subscribe($ids => {
			ids = Array.from($ids);
		})();
		return ids;
	}
	
	// Get selected items as array
	function getSelectedItems(): T[] {
		let items: T[] = [];
		selectedItems.subscribe($items => {
			items = $items;
		})();
		return items;
	}
	
	return {
		// Stores
		selectedIds,
		selectedItems,
		selectionState,
		
		// Actions
		select,
		deselect,
		toggle,
		selectAll,
		deselectAll,
		toggleAll,
		selectBy,
		deselectBy,
		
		// Utilities
		isSelected,
		getSelectedIds,
		getSelectedItems
	};
}