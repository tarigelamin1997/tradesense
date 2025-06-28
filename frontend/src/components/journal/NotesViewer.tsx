
import React, { useState, useMemo } from 'react';
import { Calendar, Search, Filter, Tag, Download, Share2, BookOpen, TrendingUp } from 'lucide-react';

interface Note {
  id: string;
  title: string;
  content: string;
  createdAt: string;
  updatedAt: string;
  tags: string[];
  category: string;
  attachments?: string[];
  relatedTrades?: string[];
}

interface NotesViewerProps {
  notes: Note[];
  onNoteSelect?: (note: Note) => void;
  onEdit?: (note: Note) => void;
  onDelete?: (noteId: string) => void;
  className?: string;
}

export const NotesViewer: React.FC<NotesViewerProps> = ({
  notes,
  onNoteSelect,
  onEdit,
  onDelete,
  className = ""
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedTag, setSelectedTag] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'title' | 'category'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [viewMode, setViewMode] = useState<'list' | 'grid' | 'timeline'>('list');

  // Get unique categories and tags
  const categories = useMemo(() => {
    const cats = Array.from(new Set(notes.map(note => note.category)));
    return cats.sort();
  }, [notes]);

  const allTags = useMemo(() => {
    const tags = Array.from(new Set(notes.flatMap(note => note.tags)));
    return tags.sort();
  }, [notes]);

  // Filter and sort notes
  const filteredNotes = useMemo(() => {
    let filtered = notes.filter(note => {
      const matchesSearch = note.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           note.content.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = selectedCategory === 'all' || note.category === selectedCategory;
      const matchesTag = !selectedTag || note.tags.includes(selectedTag);
      
      return matchesSearch && matchesCategory && matchesTag;
    });

    // Sort notes
    filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'title':
          comparison = a.title.localeCompare(b.title);
          break;
        case 'category':
          comparison = a.category.localeCompare(b.category);
          break;
        case 'date':
        default:
          comparison = new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime();
          break;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [notes, searchTerm, selectedCategory, selectedTag, sortBy, sortOrder]);

  // Render markdown content preview
  const renderMarkdownPreview = (content: string, maxLength: number = 200) => {
    // Remove markdown syntax for preview
    let preview = content
      .replace(/#{1,6}\s+/g, '') // Remove headers
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold
      .replace(/\*(.*?)\*/g, '$1') // Remove italic
      .replace(/`(.*?)`/g, '$1') // Remove inline code
      .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Remove links
      .replace(/^\s*[-*+]\s+/gm, '• ') // Convert lists to bullets
      .replace(/^\s*\d+\.\s+/gm, '• ') // Convert numbered lists
      .replace(/^\s*>\s+/gm, '') // Remove quotes
      .replace(/\n{2,}/g, '\n') // Remove extra newlines
      .trim();

    if (preview.length > maxLength) {
      preview = preview.substring(0, maxLength) + '...';
    }

    return preview;
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'trading': return <TrendingUp size={16} className="text-green-600" />;
      case 'analysis': return <BookOpen size={16} className="text-blue-600" />;
      case 'research': return <Search size={16} className="text-purple-600" />;
      default: return <Calendar size={16} className="text-gray-600" />;
    }
  };

  const renderNoteCard = (note: Note) => (
    <div
      key={note.id}
      className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => onNoteSelect?.(note)}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {getCategoryIcon(note.category)}
          <h3 className="font-medium text-gray-900 truncate">{note.title}</h3>
        </div>
        <div className="text-xs text-gray-500">
          {new Date(note.updatedAt).toLocaleDateString()}
        </div>
      </div>
      
      <p className="text-sm text-gray-600 mb-3 line-clamp-3">
        {renderMarkdownPreview(note.content)}
      </p>
      
      {note.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {note.tags.slice(0, 3).map(tag => (
            <span
              key={tag}
              className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700"
            >
              <Tag size={10} className="mr-1" />
              {tag}
            </span>
          ))}
          {note.tags.length > 3 && (
            <span className="text-xs text-gray-500">
              +{note.tags.length - 3} more
            </span>
          )}
        </div>
      )}

      {note.relatedTrades && note.relatedTrades.length > 0 && (
        <div className="text-xs text-blue-600">
          Related to {note.relatedTrades.length} trade{note.relatedTrades.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );

  const renderTimelineView = () => (
    <div className="space-y-4">
      {filteredNotes.map((note, index) => (
        <div key={note.id} className="flex items-start space-x-3">
          <div className="flex flex-col items-center">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            {index < filteredNotes.length - 1 && (
              <div className="w-0.5 h-16 bg-gray-200 mt-2"></div>
            )}
          </div>
          <div className="flex-1 min-w-0">
            {renderNoteCard(note)}
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className={`notes-viewer ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">Trading Journal</h2>
          <div className="flex items-center gap-2">
            <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded">
              <Download size={20} />
            </button>
            <button className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded">
              <Share2 size={20} />
            </button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col lg:flex-row gap-4">
          <div className="flex-1 relative">
            <Search size={20} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search notes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>

          <select
            value={selectedTag}
            onChange={(e) => setSelectedTag(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Tags</option>
            {allTags.map(tag => (
              <option key={tag} value={tag}>{tag}</option>
            ))}
          </select>

          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split('-');
              setSortBy(field as typeof sortBy);
              setSortOrder(order as typeof sortOrder);
            }}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="date-desc">Newest First</option>
            <option value="date-asc">Oldest First</option>
            <option value="title-asc">Title A-Z</option>
            <option value="title-desc">Title Z-A</option>
            <option value="category-asc">Category A-Z</option>
          </select>
        </div>

        {/* View Mode Selector */}
        <div className="flex items-center gap-2 mt-4">
          <span className="text-sm text-gray-600 mr-2">View:</span>
          <button
            onClick={() => setViewMode('list')}
            className={`px-3 py-1 rounded ${viewMode === 'list' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700'}`}
          >
            List
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`px-3 py-1 rounded ${viewMode === 'grid' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700'}`}
          >
            Grid
          </button>
          <button
            onClick={() => setViewMode('timeline')}
            className={`px-3 py-1 rounded ${viewMode === 'timeline' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700'}`}
          >
            Timeline
          </button>
        </div>
      </div>

      {/* Notes Display */}
      <div className="mb-4 text-sm text-gray-600">
        Showing {filteredNotes.length} of {notes.length} notes
      </div>

      {filteredNotes.length === 0 ? (
        <div className="text-center py-12">
          <BookOpen size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No notes found</h3>
          <p className="text-gray-600">
            {searchTerm || selectedCategory !== 'all' || selectedTag
              ? "Try adjusting your filters to see more notes."
              : "Start writing your first trading journal entry!"}
          </p>
        </div>
      ) : (
        <>
          {viewMode === 'timeline' && renderTimelineView()}
          
          {viewMode !== 'timeline' && (
            <div className={
              viewMode === 'grid' 
                ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
                : "space-y-4"
            }>
              {filteredNotes.map(note => renderNoteCard(note))}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default NotesViewer;
