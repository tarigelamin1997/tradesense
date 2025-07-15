import React, { useState } from 'react';
import { 
  Trash2, 
  Download, 
  Tag, 
  Archive, 
  X,
  AlertTriangle,
  Check
} from 'lucide-react';

interface TradeBulkActionsProps {
  selectedCount: number;
  onDelete: () => Promise<void>;
  onExport: (format: 'csv' | 'excel') => void;
  onAddTags: (tags: string[]) => void;
  onArchive: () => void;
  onClearSelection: () => void;
}

const TradeBulkActions: React.FC<TradeBulkActionsProps> = ({
  selectedCount,
  onDelete,
  onExport,
  onAddTags,
  onArchive,
  onClearSelection
}) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showTagInput, setShowTagInput] = useState(false);
  const [tagInput, setTagInput] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [showUndoToast, setShowUndoToast] = useState(false);
  
  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await onDelete();
      setShowDeleteConfirm(false);
      setShowUndoToast(true);
      
      // Auto-hide undo toast after 10 seconds
      setTimeout(() => {
        setShowUndoToast(false);
      }, 10000);
    } catch (error) {
      console.error('Failed to delete trades:', error);
    } finally {
      setIsDeleting(false);
    }
  };
  
  const handleAddTags = () => {
    const tags = tagInput.split(',').map(t => t.trim()).filter(t => t);
    if (tags.length > 0) {
      onAddTags(tags);
      setTagInput('');
      setShowTagInput(false);
    }
  };
  
  if (selectedCount === 0) return null;
  
  return (
    <>
      {/* Bulk Actions Bar */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg p-4 z-40">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Selection Info */}
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium text-gray-700">
              {selectedCount} trade{selectedCount !== 1 ? 's' : ''} selected
            </span>
            <button
              onClick={onClearSelection}
              className="text-sm text-gray-500 hover:text-gray-700 flex items-center space-x-1"
            >
              <X className="w-4 h-4" />
              <span>Clear</span>
            </button>
          </div>
          
          {/* Actions */}
          <div className="flex items-center space-x-2">
            {/* Export Dropdown */}
            <div className="relative group">
              <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center space-x-2">
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
              <div className="absolute bottom-full mb-2 right-0 w-32 bg-white border border-gray-200 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
                <button
                  onClick={() => onExport('csv')}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
                >
                  Export as CSV
                </button>
                <button
                  onClick={() => onExport('excel')}
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50"
                >
                  Export as Excel
                </button>
              </div>
            </div>
            
            {/* Add Tags */}
            <button
              onClick={() => setShowTagInput(true)}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center space-x-2"
            >
              <Tag className="w-4 h-4" />
              <span>Add Tags</span>
            </button>
            
            {/* Archive */}
            <button
              onClick={onArchive}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 flex items-center space-x-2"
            >
              <Archive className="w-4 h-4" />
              <span>Archive</span>
            </button>
            
            {/* Delete */}
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center space-x-2"
            >
              <Trash2 className="w-4 h-4" />
              <span>Delete</span>
            </button>
          </div>
        </div>
      </div>
      
      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-red-100 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900">
                Delete {selectedCount} trade{selectedCount !== 1 ? 's' : ''}?
              </h3>
            </div>
            
            <p className="text-gray-600 mb-6">
              This action cannot be undone. All selected trades will be permanently deleted.
            </p>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                disabled={isDeleting}
              >
                {isDeleting && (
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                )}
                <span>Delete</span>
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Tag Input Modal */}
      {showTagInput && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Add Tags to {selectedCount} trade{selectedCount !== 1 ? 's' : ''}
            </h3>
            
            <input
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              placeholder="Enter tags separated by commas..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
              autoFocus
            />
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowTagInput(false);
                  setTagInput('');
                }}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={handleAddTags}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Add Tags
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Undo Toast */}
      {showUndoToast && (
        <div className="fixed bottom-20 right-4 bg-gray-900 text-white rounded-lg shadow-lg p-4 flex items-center space-x-3 z-50">
          <Check className="w-5 h-5 text-green-400" />
          <span>{selectedCount} trade{selectedCount !== 1 ? 's' : ''} deleted</span>
          <button
            onClick={() => {
              // Implement undo logic here
              setShowUndoToast(false);
            }}
            className="ml-4 text-blue-400 hover:text-blue-300 font-medium"
          >
            Undo
          </button>
        </div>
      )}
    </>
  );
};

export default TradeBulkActions;