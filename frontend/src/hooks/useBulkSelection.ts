import { useState, useCallback, useMemo } from 'react';

export const useBulkSelection = <T extends { id: number }>(items: T[]) => {
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [lastSelectedId, setLastSelectedId] = useState<number | null>(null);
  
  // Check if an item is selected
  const isSelected = useCallback((id: number) => {
    return selectedIds.has(id);
  }, [selectedIds]);
  
  // Toggle single selection
  const toggleSelection = useCallback((id: number) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
    setLastSelectedId(id);
  }, []);
  
  // Toggle range selection (Shift+click)
  const toggleRangeSelection = useCallback((id: number) => {
    if (!lastSelectedId) {
      toggleSelection(id);
      return;
    }
    
    const itemIds = items.map(item => item.id);
    const lastIndex = itemIds.indexOf(lastSelectedId);
    const currentIndex = itemIds.indexOf(id);
    
    if (lastIndex === -1 || currentIndex === -1) {
      toggleSelection(id);
      return;
    }
    
    const start = Math.min(lastIndex, currentIndex);
    const end = Math.max(lastIndex, currentIndex);
    
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      for (let i = start; i <= end; i++) {
        newSet.add(itemIds[i]);
      }
      return newSet;
    });
    
    setLastSelectedId(id);
  }, [items, lastSelectedId, toggleSelection]);
  
  // Select all visible items
  const selectAll = useCallback(() => {
    setSelectedIds(new Set(items.map(item => item.id)));
  }, [items]);
  
  // Clear all selections
  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
    setLastSelectedId(null);
  }, []);
  
  // Toggle all - if any selected, clear all; if none selected, select all
  const toggleAll = useCallback(() => {
    if (selectedIds.size > 0) {
      clearSelection();
    } else {
      selectAll();
    }
  }, [selectedIds.size, clearSelection, selectAll]);
  
  // Get selected items
  const selectedItems = useMemo(() => {
    return items.filter(item => selectedIds.has(item.id));
  }, [items, selectedIds]);
  
  // Handle click with modifier keys
  const handleItemClick = useCallback((id: number, event: React.MouseEvent) => {
    if (event.shiftKey) {
      event.preventDefault(); // Prevent text selection
      toggleRangeSelection(id);
    } else if (event.ctrlKey || event.metaKey) {
      toggleSelection(id);
    } else {
      // Regular click - clear others and select this one
      setSelectedIds(new Set([id]));
      setLastSelectedId(id);
    }
  }, [toggleRangeSelection, toggleSelection]);
  
  return {
    selectedIds: Array.from(selectedIds),
    selectedCount: selectedIds.size,
    selectedItems,
    isSelected,
    toggleSelection,
    toggleRangeSelection,
    selectAll,
    clearSelection,
    toggleAll,
    handleItemClick,
    isAllSelected: items.length > 0 && selectedIds.size === items.length,
    isPartiallySelected: selectedIds.size > 0 && selectedIds.size < items.length
  };
};