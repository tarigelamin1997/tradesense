import React, { useState, useCallback, useRef } from 'react';
import { Bold, Italic, List, Link, Image, Eye, Edit } from 'lucide-react';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  height?: string;
}

export const MarkdownEditor: React.FC<MarkdownEditorProps> = ({
  value,
  onChange,
  placeholder = "Write your trade notes...",
  height = "300px"
}) => {
  const [isPreview, setIsPreview] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const insertText = useCallback((before: string, after: string = '') => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = value.substring(start, end);

    const newText = value.substring(0, start) + 
                   before + selectedText + after + 
                   value.substring(end);

    onChange(newText);

    // Restore cursor position
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(
        start + before.length,
        start + before.length + selectedText.length
      );
    }, 0);
  }, [value, onChange]);

  const formatText = (type: string) => {
    switch (type) {
      case 'bold':
        insertText('**', '**');
        break;
      case 'italic':
        insertText('*', '*');
        break;
      case 'list':
        insertText('\n- ');
        break;
      case 'link':
        insertText('[', '](url)');
        break;
      case 'image':
        insertText('![alt text](', ')');
        break;
    }
  };

  const renderMarkdown = (text: string) => {
    let html = text
      // Bold
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Italic
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Links
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 underline">$1</a>')
      // Images
      .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="max-w-full h-auto my-2" />')
      // Lists
      .replace(/^- (.+)$/gm, '<li class="ml-4">$1</li>')
      // Line breaks
      .replace(/\n/g, '<br />');

    // Wrap lists
    html = html.replace(/((<li class="ml-4">.*?<\/li>)+)/g, '<ul class="list-disc pl-4 my-2">$1</ul>');

    return { __html: html };
  };

  return (
    <div className="border border-gray-300 rounded-lg overflow-hidden">
      {/* Toolbar */}
      <div className="bg-gray-50 border-b px-3 py-2 flex items-center gap-2">
        <button
          onClick={() => formatText('bold')}
          className="p-1 hover:bg-gray-200 rounded"
          title="Bold"
        >
          <Bold size={16} />
        </button>
        <button
          onClick={() => formatText('italic')}
          className="p-1 hover:bg-gray-200 rounded"
          title="Italic"
        >
          <Italic size={16} />
        </button>
        <button
          onClick={() => formatText('list')}
          className="p-1 hover:bg-gray-200 rounded"
          title="List"
        >
          <List size={16} />
        </button>
        <button
          onClick={() => formatText('link')}
          className="p-1 hover:bg-gray-200 rounded"
          title="Link"
        >
          <Link size={16} />
        </button>
        <button
          onClick={() => formatText('image')}
          className="p-1 hover:bg-gray-200 rounded"
          title="Image"
        >
          <Image size={16} />
        </button>

        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setIsPreview(!isPreview)}
            className={`flex items-center gap-1 px-2 py-1 rounded text-sm ${
              isPreview ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-200'
            }`}
          >
            {isPreview ? <Edit size={14} /> : <Eye size={14} />}
            {isPreview ? 'Edit' : 'Preview'}
          </button>
        </div>
      </div>

      {/* Editor/Preview */}
      <div style={{ height }}>
        {isPreview ? (
          <div 
            className="p-3 h-full overflow-y-auto prose prose-sm max-w-none"
            dangerouslySetInnerHTML={renderMarkdown(value)}
          />
        ) : (
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className="w-full h-full p-3 border-none outline-none resize-none font-mono text-sm"
          />
        )}
      </div>
    </div>
  );
};