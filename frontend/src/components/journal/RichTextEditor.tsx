import React, { useCallback, useMemo, useRef, useState } from 'react';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { useDropzone } from 'react-dropzone';
import { ImageIcon, Link, AtSign, Table, Code } from 'lucide-react';

// Custom toolbar modules
const modules = {
  toolbar: {
    container: [
      [{ 'header': [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      ['blockquote', 'code-block'],
      [{ 'list': 'ordered'}, { 'list': 'bullet' }, { 'list': 'check' }],
      [{ 'script': 'sub'}, { 'script': 'super' }],
      [{ 'indent': '-1'}, { 'indent': '+1' }],
      ['link', 'image', 'video'],
      [{ 'color': [] }, { 'background': [] }],
      ['clean']
    ],
    handlers: {}
  },
  clipboard: {
    matchVisual: false
  },
  imageResize: {
    modules: ['Resize', 'DisplaySize', 'Toolbar']
  }
};

interface RichTextEditorProps {
  value: string;
  onChange: (content: string) => void;
  onTradeMention?: (tradeId: string) => void;
  placeholder?: string;
  height?: number;
  readOnly?: boolean;
  onImageUpload?: (file: File) => Promise<string>;
  availableTrades?: Array<{
    id: string;
    symbol: string;
    date: string;
  }>;
}

export const RichTextEditor: React.FC<RichTextEditorProps> = ({
  value,
  onChange,
  onTradeMention,
  placeholder = "What happened in the markets today?",
  height = 400,
  readOnly = false,
  onImageUpload,
  availableTrades = []
}) => {
  const [showTradeSuggestions, setShowTradeSuggestions] = useState(false);
  const [tradeSuggestions, setTradeSuggestions] = useState<typeof availableTrades>([]);
  const [currentMentionIndex, setCurrentMentionIndex] = useState(0);
  const quillRef = useRef<ReactQuill>(null);

  // Handle image uploads
  const handleImageUpload = useCallback(async (file: File) => {
    if (!onImageUpload) {
      // Default: convert to base64
      return new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }
    return onImageUpload(file);
  }, [onImageUpload]);

  // Custom image handler
  const imageHandler = useCallback(() => {
    const input = document.createElement('input');
    input.setAttribute('type', 'file');
    input.setAttribute('accept', 'image/*');
    input.click();

    input.onchange = async () => {
      const file = input.files?.[0];
      if (file) {
        try {
          const url = await handleImageUpload(file);
          const quill = quillRef.current?.getEditor();
          if (quill) {
            const range = quill.getSelection();
            if (range) {
              quill.insertEmbed(range.index, 'image', url);
            }
          }
        } catch (error) {
          console.error('Failed to upload image:', error);
        }
      }
    };
  }, [handleImageUpload]);

  // Handle drag and drop
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    },
    onDrop: async (acceptedFiles) => {
      for (const file of acceptedFiles) {
        try {
          const url = await handleImageUpload(file);
          const quill = quillRef.current?.getEditor();
          if (quill) {
            const range = quill.getSelection() || { index: quill.getLength() };
            quill.insertEmbed(range.index, 'image', url);
          }
        } catch (error) {
          console.error('Failed to upload image:', error);
        }
      }
    },
    noClick: true,
    noKeyboard: true
  });

  // Handle @ mentions for trades
  const handleTextChange = useCallback((content: string, delta: any, source: string, editor: any) => {
    const text = editor.getText();
    const selection = editor.getSelection();
    
    if (selection && source === 'user') {
      const textBeforeCursor = text.substring(0, selection.index);
      const lastAtIndex = textBeforeCursor.lastIndexOf('@');
      
      if (lastAtIndex !== -1 && lastAtIndex === selection.index - 1) {
        // Just typed @
        setShowTradeSuggestions(true);
        setCurrentMentionIndex(selection.index);
        setTradeSuggestions(availableTrades);
      } else if (showTradeSuggestions && lastAtIndex !== -1) {
        // Typing after @
        const searchText = textBeforeCursor.substring(lastAtIndex + 1);
        const filtered = availableTrades.filter(trade => 
          trade.symbol.toLowerCase().includes(searchText.toLowerCase())
        );
        setTradeSuggestions(filtered);
      } else {
        setShowTradeSuggestions(false);
      }
    }
    
    onChange(content);
  }, [onChange, availableTrades, showTradeSuggestions]);

  // Insert trade mention
  const insertTradeMention = useCallback((trade: typeof availableTrades[0]) => {
    const quill = quillRef.current?.getEditor();
    if (quill) {
      const text = quill.getText();
      const lastAtIndex = text.lastIndexOf('@', currentMentionIndex);
      
      if (lastAtIndex !== -1) {
        const lengthToRemove = currentMentionIndex - lastAtIndex;
        quill.deleteText(lastAtIndex, lengthToRemove);
        
        // Insert the trade mention as a link
        quill.insertText(lastAtIndex, `@${trade.symbol}`, {
          link: `#trade-${trade.id}`,
          color: '#3B82F6',
          bold: true
        });
        
        // Move cursor after the mention
        quill.setSelection(lastAtIndex + trade.symbol.length + 1, 0);
      }
    }
    
    setShowTradeSuggestions(false);
    if (onTradeMention) {
      onTradeMention(trade.id);
    }
  }, [currentMentionIndex, onTradeMention]);

  // Update modules with custom handlers
  const updatedModules = useMemo(() => ({
    ...modules,
    toolbar: {
      ...modules.toolbar,
      handlers: {
        image: imageHandler
      }
    }
  }), [imageHandler]);

  return (
    <div className="relative">
      <div {...getRootProps()} className={`relative ${isDragActive ? 'ring-2 ring-blue-500' : ''}`}>
        <input {...getInputProps()} />
        
        {isDragActive && (
          <div className="absolute inset-0 bg-blue-50 bg-opacity-90 z-10 flex items-center justify-center">
            <div className="text-center">
              <ImageIcon className="w-12 h-12 text-blue-600 mx-auto mb-2" />
              <p className="text-blue-600 font-medium">Drop images here</p>
            </div>
          </div>
        )}
        
        <ReactQuill
          ref={quillRef}
          theme="snow"
          value={value}
          onChange={handleTextChange}
          modules={updatedModules}
          placeholder={placeholder}
          readOnly={readOnly}
          style={{ height: `${height}px`, marginBottom: '50px' }}
        />
      </div>
      
      {/* Trade suggestions dropdown */}
      {showTradeSuggestions && tradeSuggestions.length > 0 && (
        <div className="absolute z-20 mt-1 w-64 bg-white border border-gray-200 rounded-lg shadow-lg">
          <div className="p-2">
            <p className="text-xs text-gray-500 mb-2">Select a trade to mention</p>
            {tradeSuggestions.slice(0, 5).map((trade) => (
              <button
                key={trade.id}
                onClick={() => insertTradeMention(trade)}
                className="w-full text-left px-3 py-2 hover:bg-gray-100 rounded flex items-center justify-between"
              >
                <span className="font-medium">{trade.symbol}</span>
                <span className="text-xs text-gray-500">{trade.date}</span>
              </button>
            ))}
          </div>
        </div>
      )}
      
      {/* Custom toolbar additions */}
      <div className="absolute bottom-2 right-2 flex space-x-2">
        <button
          onClick={() => {
            const quill = quillRef.current?.getEditor();
            if (quill) {
              const range = quill.getSelection();
              if (range) {
                quill.insertText(range.index, '@');
                quill.setSelection(range.index + 1, 0);
              }
            }
          }}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
          title="Mention a trade"
        >
          <AtSign className="w-4 h-4" />
        </button>
        
        <button
          onClick={() => {
            const quill = quillRef.current?.getEditor();
            if (quill) {
              const range = quill.getSelection();
              if (range) {
                const table = `
<table>
  <tr>
    <th>Metric</th>
    <th>Value</th>
  </tr>
  <tr>
    <td>Entry</td>
    <td>$0.00</td>
  </tr>
  <tr>
    <td>Exit</td>
    <td>$0.00</td>
  </tr>
</table>`;
                quill.clipboard.dangerouslyPasteHTML(range.index, table);
              }
            }
          }}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
          title="Insert table"
        >
          <Table className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export default RichTextEditor;