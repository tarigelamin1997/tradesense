import React, { useState, useRef, useCallback } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  height?: string;
  enablePreview?: boolean;
  enableImageUpload?: boolean;
}

interface ToolbarButton {
  icon: string;
  label: string;
  action: () => void;
  shortcut?: string;
}

export const MarkdownEditor: React.FC<MarkdownEditorProps> = ({
  value,
  onChange,
  placeholder = "Start writing your trading notes...",
  height = "400px",
  enablePreview = true,
  enableImageUpload = true
}) => {
  const [isPreview, setIsPreview] = useState(false);
  const [selectedTab, setSelectedTab] = useState<'write' | 'preview'>('write');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showTemplates, setShowTemplates] = useState(false);

  const insertText = useCallback((before: string, after: string = '', placeholder: string = '') => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = value.substring(start, end) || placeholder;

    const newValue =
      value.substring(0, start) +
      before + selectedText + after +
      value.substring(end);

    onChange(newValue);

    // Restore cursor position
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(
        start + before.length,
        start + before.length + selectedText.length
      );
    }, 0);
  }, [value, onChange]);

  const formatActions = [
    {
      icon: '**B**',
      title: 'Bold',
      action: () => insertText('**', '**')
    },
    {
      icon: '*I*',
      title: 'Italic',
      action: () => insertText('*', '*')
    },
    {
      icon: '# H',
      title: 'Heading',
      action: () => insertText('## ')
    },
    {
      icon: '• L',
      title: 'List',
      action: () => insertText('- ')
    },
    {
      icon: '[L]',
      title: 'Link',
      action: () => insertText('[', '](url)')
    },
    {
      icon: '```',
      title: 'Code',
      action: () => insertText('```\n', '\n```')
    },
    {
      icon: '| T',
      title: 'Table',
      action: () => insertText(
        '| Column 1 | Column 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |\n'
      )
    },
    {
      icon: '📊',
      title: 'Trade Template',
      action: () => insertText(`
## Trade Analysis

**Setup:** 
**Entry:** 
**Exit:** 
**Result:** 
**Lessons:** 
`)
    }
  ];

  const renderMarkdown = (text: string): string => {
    // Simple markdown to HTML converter
    let html = text
      // Headers
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      // Bold
      .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
      // Italic
      .replace(/\*(.*)\*/gim, '<em>$1</em>')
      // Links
      .replace(/\[([^\]]*)\]\(([^\)]*)\)/gim, '<a href="$2" target="_blank">$1</a>')
      // Lists
      .replace(/^\s*\* (.*)$/gim, '<li>$1</li>')
      .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
      .replace(/^\s*\- (.*)$/gim, '<li>$1</li>')
      // Code blocks
      .replace(/```([\s\S]*?)```/gim, '<pre><code>$1</code></pre>')
      // Inline code
      .replace(/`([^`]*)`/gim, '<code>$1</code>')
      // Line breaks
      .replace(/\n/gim, '<br>');

    return html;
  };

    const templates = [
    {
      name: 'Trade Review',
      content: `# Trade Review - [Date]

## Trade Setup
- **Symbol**: 
- **Entry**: $
- **Exit**: $
- **Size**: 
- **Strategy**: 

## What Went Well
- 

## What Could Improve
- 

## Key Learnings
- 

## Emotional State
**Before Trade**: 
**During Trade**: 
**After Trade**: 

## Next Actions
- `
    },
    {
      name: 'Daily Journal',
      content: `# Daily Trading Journal - [Date]

## Market Overview
- **Market Sentiment**: 
- **Key Economic Events**: 
- **Sector Performance**: 

## Today's Trades
### Trade 1: [Symbol]
- **Setup**: 
- **Execution**: 
- **Result**: 

## Lessons Learned
- 

## Tomorrow's Plan
- **Watchlist**: 
- **Strategies to Focus**: 
- **Risk Management**: 

## Mood & Psychology
**Morning**: 
**End of Day**: `
    },
    {
      name: 'Weekly Review',
      content: `# Weekly Trading Review

## Performance Summary
- **Total P&L**: $
- **Win Rate**: %
- **Best Trade**: 
- **Worst Trade**: 

## Strategy Performance
| Strategy | Trades | Win Rate | P&L |
|----------|--------|----------|-----|
|          |        |          |     |

## Key Insights
1. 
2. 
3. 

## Areas for Improvement
- 

## Goals for Next Week
- `
    }
  ];

    const handleImageUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      // In a real implementation, you'd upload to a server
      // For now, we'll simulate with a placeholder
      const imageUrl = `![${file.name}](image-placeholder-${file.name})`;
      insertText(imageUrl, '', '');
    }
  }, [insertText]);

  return (
    <Card className="overflow-hidden">
      {/* Toolbar */}
      <div className="border-b border-gray-200 bg-gray-50 px-4 py-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1">
            {formatActions.map((action, index) => (
              <button
                key={index}
                onClick={action.action}
                title={action.title}
                className="px-2 py-1 text-sm font-mono border border-gray-300 rounded hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {action.icon}
              </button>
            ))}
          </div>

          <div className="flex rounded-lg bg-gray-200 p-1">
            <button
              onClick={() => setSelectedTab('write')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                selectedTab === 'write'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Write
            </button>
            <button
              onClick={() => setSelectedTab('preview')}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                selectedTab === 'preview'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Preview
            </button>
          </div>
        </div>
      </div>

      {/* Editor Content */}
      <div style={{ height }}>
        {selectedTab === 'write' ? (
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className="w-full h-full p-4 border-none resize-none focus:outline-none font-mono text-sm"
            style={{ minHeight: height }}
          />
        ) : (
          <div className="h-full overflow-auto">
            <div
              className="p-4 prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{
                __html: renderMarkdown(value) || '<p class="text-gray-500">Nothing to preview</p>'
              }}
            />
          </div>
        )}
      </div>

            {/* Templates dropdown */}
        {showTemplates && (
          <div className="absolute z-10 mt-2 w-64 bg-white border rounded-lg shadow-lg">
            <div className="p-2">
              <div className="text-sm font-medium text-gray-700 mb-2">Choose a template:</div>
              {templates.map((template, index) => (
                <button
                  key={index}
                  onClick={() => {
                    onChange(template.content);
                    setShowTemplates(false);
                  }}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 rounded"
                >
                  {template.name}
                </button>
              ))}
            </div>
          </div>
        )}

            {enableImageUpload && (
              <>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-3 py-1 text-sm border rounded hover:bg-gray-100 flex items-center gap-1"
                >
                  🖼️ Image
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
              </>
            )}

            <button
              onClick={() => setShowTemplates(!showTemplates)}
              className="px-3 py-1 text-sm border rounded hover:bg-gray-100"
            >
              📋 Templates
            </button>

      {/* Footer with tips */}
      <div className="border-t border-gray-200 bg-gray-50 px-4 py-2">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center space-x-4">
            <span>**bold** *italic* `code`</span>
            <span>## heading</span>
            <span>- list</span>
            <span>[link](url)</span>
          </div>
          <div className="text-right">
            <span>{value.length} characters</span>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default MarkdownEditor;