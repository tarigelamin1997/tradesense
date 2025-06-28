
import React, { useState, useRef, useCallback, useMemo } from 'react';
import { Upload, Image, Bold, Italic, Link, List, Quote, Code, Eye, EyeOff, Save, Template, Undo, Redo } from 'lucide-react';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  onSave?: () => void;
  placeholder?: string;
  height?: string;
  enableImageUpload?: boolean;
  enableTemplates?: boolean;
  className?: string;
}

interface Template {
  name: string;
  content: string;
  category: string;
}

const PREDEFINED_TEMPLATES: Template[] = [
  {
    name: "Daily Trade Review",
    category: "Trading",
    content: `# Daily Trade Review - {date}

## Market Context
- Market conditions: 
- Volatility: 
- Key events: 

## Trades Executed
### Trade 1: {symbol}
- **Entry**: $
- **Exit**: $
- **Size**: 
- **P&L**: $
- **Setup**: 
- **Execution Quality**: /10

## Lessons Learned
- What went well:
- What to improve:
- Key insights:

## Tomorrow's Plan
- Focus areas:
- Watchlist:
- Risk limits:
`
  },
  {
    name: "Weekly Strategy Review",
    category: "Trading",
    content: `# Weekly Strategy Review - Week of {date}

## Performance Summary
- Total P&L: $
- Win Rate: %
- Best Trade: $
- Worst Trade: $
- Sharpe Ratio: 

## Strategy Analysis
### What Worked
- 

### What Didn't Work
- 

### Pattern Recognition
- 

## Emotional State
- Stress Level (1-10): 
- Confidence Level (1-10): 
- Key Emotional Challenges:

## Action Items for Next Week
1. 
2. 
3. 
`
  },
  {
    name: "Trade Post-Mortem",
    category: "Analysis",
    content: `# Trade Post-Mortem: {symbol}

## Trade Details
- **Date**: {date}
- **Symbol**: {symbol}
- **Direction**: Long/Short
- **Entry**: $
- **Exit**: $
- **Size**: 
- **Duration**: 
- **P&L**: $

## Setup Analysis
### Why I Entered
- 

### Market Context
- 

### Risk Management
- Stop Loss: $
- Target: $
- Risk/Reward: 

## Execution Review
### What Went Right
- 

### What Went Wrong
- 

### Lessons Learned
- 

## Future Improvements
1. 
2. 
3. 
`
  },
  {
    name: "Market Research Notes",
    category: "Research",
    content: `# Market Research - {symbol}

## Company Overview
- **Sector**: 
- **Market Cap**: 
- **Key Business**: 

## Technical Analysis
### Chart Patterns
- 

### Support/Resistance Levels
- Support: $
- Resistance: $

### Indicators
- RSI: 
- MACD: 
- Volume: 

## Fundamental Analysis
### Key Metrics
- P/E Ratio: 
- Revenue Growth: 
- Debt/Equity: 

### Catalysts
- Upcoming Events: 
- Earnings Date: 
- Expected Impact: 

## Trading Plan
- **Entry Strategy**: 
- **Stop Loss**: $
- **Target**: $
- **Position Size**: 
- **Risk Level**: 
`
  }
];

export const MarkdownEditor: React.FC<MarkdownEditorProps> = ({
  value,
  onChange,
  onSave,
  placeholder = "Start writing your trading journal...",
  height = "400px",
  enableImageUpload = true,
  enableTemplates = true,
  className = ""
}) => {
  const [showPreview, setShowPreview] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [history, setHistory] = useState<string[]>([value]);
  const [historyIndex, setHistoryIndex] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Update history when value changes
  const updateHistory = useCallback((newValue: string) => {
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(newValue);
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  }, [history, historyIndex]);

  const insertText = useCallback((before: string, after: string = '') => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = value.substring(start, end);
    const newText = value.substring(0, start) + before + selectedText + after + value.substring(end);
    
    onChange(newText);
    updateHistory(newText);

    // Restore cursor position
    setTimeout(() => {
      textarea.focus();
      const newCursorPos = start + before.length + selectedText.length;
      textarea.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  }, [value, onChange, updateHistory]);

  const insertAtCursor = useCallback((text: string) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const newText = value.substring(0, start) + text + value.substring(start);
    
    onChange(newText);
    updateHistory(newText);

    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + text.length, start + text.length);
    }, 0);
  }, [value, onChange, updateHistory]);

  const formatActions = {
    bold: () => insertText('**', '**'),
    italic: () => insertText('*', '*'),
    heading: () => insertText('\n## '),
    list: () => insertText('\n- '),
    numberedList: () => insertText('\n1. '),
    quote: () => insertText('\n> '),
    code: () => insertText('`', '`'),
    codeBlock: () => insertText('\n```\n', '\n```\n'),
    link: () => insertText('[', '](url)'),
    hr: () => insertText('\n---\n'),
    table: () => insertText('\n| Column 1 | Column 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |\n')
  };

  const handleImageUpload = useCallback(async (file: File) => {
    try {
      // Create a FormData object for the file upload
      const formData = new FormData();
      formData.append('file', file);

      // You would typically upload to your backend here
      // For now, we'll create a local URL for preview
      const imageUrl = URL.createObjectURL(file);
      const imageMarkdown = `\n![${file.name}](${imageUrl})\n`;
      
      insertAtCursor(imageMarkdown);
      
      // In a real implementation, you'd upload to your server:
      // const response = await fetch('/api/upload/image', {
      //   method: 'POST',
      //   body: formData
      // });
      // const { url } = await response.json();
      // insertAtCursor(`\n![${file.name}](${url})\n`);
      
    } catch (error) {
      console.error('Error uploading image:', error);
    }
  }, [insertAtCursor]);

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type.startsWith('image/')) {
      handleImageUpload(file);
    }
    // Reset input
    event.target.value = '';
  }, [handleImageUpload]);

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    const files = Array.from(event.dataTransfer.files);
    const imageFile = files.find(file => file.type.startsWith('image/'));
    if (imageFile) {
      handleImageUpload(imageFile);
    }
  }, [handleImageUpload]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
    if (event.ctrlKey || event.metaKey) {
      switch (event.key) {
        case 'b':
          event.preventDefault();
          formatActions.bold();
          break;
        case 'i':
          event.preventDefault();
          formatActions.italic();
          break;
        case 's':
          event.preventDefault();
          onSave?.();
          break;
        case 'z':
          if (event.shiftKey) {
            // Redo
            event.preventDefault();
            if (historyIndex < history.length - 1) {
              setHistoryIndex(historyIndex + 1);
              onChange(history[historyIndex + 1]);
            }
          } else {
            // Undo
            event.preventDefault();
            if (historyIndex > 0) {
              setHistoryIndex(historyIndex - 1);
              onChange(history[historyIndex - 1]);
            }
          }
          break;
      }
    }
  }, [formatActions, onSave, history, historyIndex, onChange]);

  const applyTemplate = useCallback((template: Template) => {
    const now = new Date();
    const dateStr = now.toLocaleDateString();
    const timeStr = now.toLocaleTimeString();
    
    let content = template.content
      .replace(/{date}/g, dateStr)
      .replace(/{time}/g, timeStr)
      .replace(/{symbol}/g, 'SYMBOL');
    
    onChange(content);
    updateHistory(content);
    setShowTemplates(false);
  }, [onChange, updateHistory]);

  // Render markdown preview
  const renderPreview = useMemo(() => {
    if (!showPreview) return null;

    // Basic markdown rendering (you might want to use a proper markdown library)
    let html = value
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>')
      .replace(/^\- (.*$)/gim, '<li>$1</li>')
      .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
      .replace(/\n/g, '<br>');

    return (
      <div 
        className="prose prose-sm max-w-none p-4 bg-gray-50 border rounded-lg overflow-auto"
        style={{ height }}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  }, [value, showPreview, height]);

  return (
    <div className={`markdown-editor ${className}`}>
      {/* Toolbar */}
      <div className="border border-gray-300 rounded-t-lg bg-white p-2 flex flex-wrap items-center gap-1">
        {/* Formatting Buttons */}
        <div className="flex items-center gap-1 border-r pr-2 mr-2">
          <button
            onClick={formatActions.bold}
            className="p-1 hover:bg-gray-100 rounded"
            title="Bold (Ctrl+B)"
          >
            <Bold size={16} />
          </button>
          <button
            onClick={formatActions.italic}
            className="p-1 hover:bg-gray-100 rounded"
            title="Italic (Ctrl+I)"
          >
            <Italic size={16} />
          </button>
          <button
            onClick={formatActions.link}
            className="p-1 hover:bg-gray-100 rounded"
            title="Insert Link"
          >
            <Link size={16} />
          </button>
        </div>

        {/* Structure Buttons */}
        <div className="flex items-center gap-1 border-r pr-2 mr-2">
          <button
            onClick={formatActions.list}
            className="p-1 hover:bg-gray-100 rounded"
            title="Bullet List"
          >
            <List size={16} />
          </button>
          <button
            onClick={formatActions.quote}
            className="p-1 hover:bg-gray-100 rounded"
            title="Quote"
          >
            <Quote size={16} />
          </button>
          <button
            onClick={formatActions.code}
            className="p-1 hover:bg-gray-100 rounded"
            title="Inline Code"
          >
            <Code size={16} />
          </button>
        </div>

        {/* Media Buttons */}
        {enableImageUpload && (
          <div className="flex items-center gap-1 border-r pr-2 mr-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-1 hover:bg-gray-100 rounded"
              title="Upload Image"
            >
              <Image size={16} />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        )}

        {/* History Buttons */}
        <div className="flex items-center gap-1 border-r pr-2 mr-2">
          <button
            onClick={() => {
              if (historyIndex > 0) {
                setHistoryIndex(historyIndex - 1);
                onChange(history[historyIndex - 1]);
              }
            }}
            disabled={historyIndex <= 0}
            className="p-1 hover:bg-gray-100 rounded disabled:opacity-50"
            title="Undo (Ctrl+Z)"
          >
            <Undo size={16} />
          </button>
          <button
            onClick={() => {
              if (historyIndex < history.length - 1) {
                setHistoryIndex(historyIndex + 1);
                onChange(history[historyIndex + 1]);
              }
            }}
            disabled={historyIndex >= history.length - 1}
            className="p-1 hover:bg-gray-100 rounded disabled:opacity-50"
            title="Redo (Ctrl+Shift+Z)"
          >
            <Redo size={16} />
          </button>
        </div>

        {/* View Buttons */}
        <div className="flex items-center gap-1 border-r pr-2 mr-2">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className={`p-1 rounded ${showPreview ? 'bg-blue-100 text-blue-600' : 'hover:bg-gray-100'}`}
            title="Toggle Preview"
          >
            {showPreview ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>

        {/* Template Button */}
        {enableTemplates && (
          <div className="flex items-center gap-1 border-r pr-2 mr-2">
            <button
              onClick={() => setShowTemplates(!showTemplates)}
              className="p-1 hover:bg-gray-100 rounded"
              title="Templates"
            >
              <Template size={16} />
            </button>
          </div>
        )}

        {/* Save Button */}
        {onSave && (
          <button
            onClick={onSave}
            className="p-1 hover:bg-gray-100 rounded text-green-600"
            title="Save (Ctrl+S)"
          >
            <Save size={16} />
          </button>
        )}

        {/* Character Count */}
        <div className="ml-auto text-xs text-gray-500">
          {value.length} characters
        </div>
      </div>

      {/* Templates Panel */}
      {showTemplates && (
        <div className="border-l border-r border-gray-300 bg-white p-4 max-h-64 overflow-y-auto">
          <h4 className="font-medium mb-3">Templates</h4>
          <div className="grid gap-2">
            {PREDEFINED_TEMPLATES.map((template, index) => (
              <button
                key={index}
                onClick={() => applyTemplate(template)}
                className="text-left p-2 border rounded hover:bg-gray-50 transition-colors"
              >
                <div className="font-medium text-sm">{template.name}</div>
                <div className="text-xs text-gray-500">{template.category}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Editor/Preview Area */}
      <div className="flex border-l border-r border-b border-gray-300 rounded-b-lg overflow-hidden">
        {!showPreview && (
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => {
              onChange(e.target.value);
              // Don't update history on every keystroke, only on significant changes
            }}
            onBlur={() => updateHistory(value)}
            onKeyDown={handleKeyDown}
            onDrop={handleDrop}
            onDragOver={(e) => e.preventDefault()}
            placeholder={placeholder}
            className="w-full p-4 resize-none outline-none font-mono text-sm"
            style={{ height }}
          />
        )}
        
        {showPreview && (
          <div className="w-full">
            {renderPreview}
          </div>
        )}
      </div>

      {/* Helper Text */}
      <div className="text-xs text-gray-500 mt-1">
        Tip: Use Ctrl+B for bold, Ctrl+I for italic, Ctrl+S to save. Drag & drop images to upload.
      </div>
    </div>
  );
};

export default MarkdownEditor;
