
import React, { useState, useCallback } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  height?: string;
}

export const MarkdownEditor: React.FC<MarkdownEditorProps> = ({
  value,
  onChange,
  placeholder = "Write your trade notes here...",
  height = "300px"
}) => {
  const [isPreview, setIsPreview] = useState(false);
  const [selectedText, setSelectedText] = useState({ start: 0, end: 0 });

  const insertMarkdown = useCallback((before: string, after: string = '') => {
    const textarea = document.querySelector('.markdown-textarea') as HTMLTextAreaElement;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selectedText = value.substring(start, end);
    
    const newText = value.substring(0, start) + before + selectedText + after + value.substring(end);
    onChange(newText);

    // Restore cursor position
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(start + before.length, start + before.length + selectedText.length);
    }, 10);
  }, [value, onChange]);

  const formatBold = () => insertMarkdown('**', '**');
  const formatItalic = () => insertMarkdown('*', '*');
  const formatHeading = () => insertMarkdown('## ');
  const formatBulletList = () => insertMarkdown('- ');
  const formatNumberedList = () => insertMarkdown('1. ');
  const formatCode = () => insertMarkdown('`', '`');
  const formatCodeBlock = () => insertMarkdown('```\n', '\n```');
  const formatQuote = () => insertMarkdown('> ');

  const renderMarkdown = (text: string) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^## (.*$)/gm, '<h2>$1</h2>')
      .replace(/^### (.*$)/gm, '<h3>$1</h3>')
      .replace(/^- (.*$)/gm, '<li>$1</li>')
      .replace(/^1\. (.*$)/gm, '<li>$1</li>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/```\n(.*?)\n```/gs, '<pre><code>$1</code></pre>')
      .replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>')
      .replace(/\n/g, '<br>');
  };

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={formatBold}
            title="Bold (Ctrl+B)"
            className="px-2 py-1"
          >
            <strong>B</strong>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={formatItalic}
            title="Italic (Ctrl+I)"
            className="px-2 py-1"
          >
            <em>I</em>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={formatHeading}
            title="Heading"
            className="px-2 py-1"
          >
            H2
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={formatBulletList}
            title="Bullet List"
            className="px-2 py-1"
          >
            •
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={formatNumberedList}
            title="Numbered List"
            className="px-2 py-1"
          >
            1.
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={formatCode}
            title="Inline Code"
            className="px-2 py-1"
          >
            &lt;/&gt;
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={formatQuote}
            title="Quote"
            className="px-2 py-1"
          >
            "
          </Button>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant={!isPreview ? "default" : "outline"}
            size="sm"
            onClick={() => setIsPreview(false)}
          >
            Write
          </Button>
          <Button
            variant={isPreview ? "default" : "outline"}
            size="sm"
            onClick={() => setIsPreview(true)}
          >
            Preview
          </Button>
        </div>
      </div>

      {!isPreview ? (
        <textarea
          className="markdown-textarea w-full p-3 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
          style={{ height }}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          onKeyDown={(e) => {
            if (e.ctrlKey && e.key === 'b') {
              e.preventDefault();
              formatBold();
            }
            if (e.ctrlKey && e.key === 'i') {
              e.preventDefault();
              formatItalic();
            }
          }}
        />
      ) : (
        <div
          className="w-full p-3 border border-gray-200 rounded-lg bg-gray-50 prose prose-sm max-w-none"
          style={{ height, overflow: 'auto' }}
          dangerouslySetInnerHTML={{ __html: renderMarkdown(value) }}
        />
      )}

      <div className="flex justify-between items-center mt-2 text-xs text-gray-500">
        <div>
          {value.length} characters
        </div>
        <div>
          Supports: **bold**, *italic*, ## headings, - lists, `code`, > quotes
        </div>
      </div>
    </Card>
  );
};
