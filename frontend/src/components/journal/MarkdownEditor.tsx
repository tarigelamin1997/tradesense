import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Bold, Italic, Link, List, Code, Eye, EyeOff, Save, Upload } from 'lucide-react';

interface MarkdownEditorProps {
  value: string;
  onChange: (value: string) => void;
  onSave?: (content: string) => void;
  placeholder?: string;
  height?: string;
  autoSave?: boolean;
  readOnly?: boolean;
}

export const MarkdownEditor: React.FC<MarkdownEditorProps> = ({
  value,
  onChange,
  onSave,
  placeholder = "Write your trading notes in markdown...",
  height = "400px",
  autoSave = true,
  readOnly = false
}) => {
  const [showPreview, setShowPreview] = useState(false);
  const [isAutoSaving, setIsAutoSaving] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-save functionality
  useEffect(() => {
    if (!autoSave || !onSave) return;

    const autoSaveTimer = setTimeout(() => {
      setIsAutoSaving(true);
      onSave(value);
      setTimeout(() => setIsAutoSaving(false), 1000);
    }, 2000);

    return () => clearTimeout(autoSaveTimer);
  }, [value, autoSave, onSave]);

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

  const formatBold = () => insertText('**', '**');
  const formatItalic = () => insertText('*', '*');
  const formatCode = () => insertText('`', '`');
  const formatList = () => insertText('\n- ');
  const formatLink = () => insertText('[', '](url)');

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // In a real app, you'd upload to a server
      const imageUrl = URL.createObjectURL(file);
      insertText(`![${file.name}](${imageUrl})`);
    }
  };

  const renderMarkdown = (text: string) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 rounded">$1</code>')
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 underline">$1</a>')
      .replace(/^- (.+)$/gm, '<li class="ml-4">$1</li>')
      .replace(/\n/g, '<br>');
  };

  return (
    <div className="border border-gray-300 rounded-lg overflow-hidden">
      {/* Toolbar */}
      <div className="bg-gray-50 border-b border-gray-200 p-3 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <button
            onClick={formatBold}
            className="p-2 hover:bg-gray-200 rounded"
            title="Bold (Ctrl+B)"
            disabled={readOnly}
          >
            <Bold size={16} />
          </button>
          <button
            onClick={formatItalic}
            className="p-2 hover:bg-gray-200 rounded"
            title="Italic (Ctrl+I)"
            disabled={readOnly}
          >
            <Italic size={16} />
          </button>
          <button
            onClick={formatCode}
            className="p-2 hover:bg-gray-200 rounded"
            title="Code"
            disabled={readOnly}
          >
            <Code size={16} />
          </button>
          <button
            onClick={formatList}
            className="p-2 hover:bg-gray-200 rounded"
            title="List"
            disabled={readOnly}
          >
            <List size={16} />
          </button>
          <button
            onClick={formatLink}
            className="p-2 hover:bg-gray-200 rounded"
            title="Link"
            disabled={readOnly}
          >
            <Link size={16} />
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-2 hover:bg-gray-200 rounded"
            title="Upload Image"
            disabled={readOnly}
          >
            <Upload size={16} />
          </button>
        </div>

        <div className="flex items-center space-x-2">
          {isAutoSaving && (
            <span className="text-sm text-gray-500">Saving...</span>
          )}
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="p-2 hover:bg-gray-200 rounded flex items-center"
            title={showPreview ? "Hide Preview" : "Show Preview"}
          >
            {showPreview ? <EyeOff size={16} /> : <Eye size={16} />}
            <span className="ml-1 text-sm">
              {showPreview ? "Edit" : "Preview"}
            </span>
          </button>
          {onSave && (
            <button
              onClick={() => onSave(value)}
              className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center"
            >
              <Save size={16} className="mr-1" />
              Save
            </button>
          )}
        </div>
      </div>

      {/* Editor/Preview Area */}
      <div className="flex" style={{ height }}>
        {/* Editor */}
        {!showPreview && (
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            className="w-full p-4 resize-none focus:outline-none font-mono text-sm leading-relaxed"
            readOnly={readOnly}
            onKeyDown={(e) => {
              if (e.ctrlKey || e.metaKey) {
                if (e.key === 'b') {
                  e.preventDefault();
                  formatBold();
                } else if (e.key === 'i') {
                  e.preventDefault();
                  formatItalic();
                }
              }
            }}
          />
        )}

        {/* Preview */}
        {showPreview && (
          <div className="w-full p-4 overflow-y-auto bg-white">
            <div
              className="prose max-w-none"
              dangerouslySetInnerHTML={{
                __html: renderMarkdown(value) || '<p class="text-gray-400">Nothing to preview...</p>'
              }}
            />
          </div>
        )}
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        className="hidden"
      />

      {/* Status bar */}
      <div className="bg-gray-50 border-t border-gray-200 px-4 py-2 text-xs text-gray-500 flex justify-between">
        <span>{value.length} characters</span>
        <span>Markdown supported</span>
      </div>
    </div>
  );
};

export default MarkdownEditor;