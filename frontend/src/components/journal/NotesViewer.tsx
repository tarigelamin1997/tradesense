
import React from 'react';
import { Card } from '../ui/Card';

interface NotesViewerProps {
  content: string;
  title?: string;
  timestamp?: string;
  className?: string;
}

export const NotesViewer: React.FC<NotesViewerProps> = ({
  content,
  title,
  timestamp,
  className = ""
}) => {
  const renderMarkdown = (text: string) => {
    if (!text) return '';
    
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^## (.*$)/gm, '<h2 class="text-lg font-semibold mt-4 mb-2">$1</h2>')
      .replace(/^### (.*$)/gm, '<h3 class="text-md font-semibold mt-3 mb-2">$1</h3>')
      .replace(/^- (.*$)/gm, '<li class="ml-4">• $1</li>')
      .replace(/^1\. (.*$)/gm, '<li class="ml-4">1. $1</li>')
      .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono">$1</code>')
      .replace(/```\n(.*?)\n```/gs, '<pre class="bg-gray-100 p-3 rounded mt-2 mb-2 overflow-x-auto"><code class="font-mono text-sm">$1</code></pre>')
      .replace(/^> (.*$)/gm, '<blockquote class="border-l-4 border-blue-200 pl-4 italic text-gray-600 my-2">$1</blockquote>')
      .replace(/\n/g, '<br>');
  };

  if (!content || content.trim() === '') {
    return (
      <Card className={`p-4 ${className}`}>
        <div className="text-gray-400 italic text-center py-4">
          No notes available
        </div>
      </Card>
    );
  }

  return (
    <Card className={`p-4 ${className}`}>
      {title && (
        <div className="border-b border-gray-200 pb-2 mb-3">
          <h3 className="font-semibold text-gray-900">{title}</h3>
          {timestamp && (
            <p className="text-xs text-gray-500 mt-1">{timestamp}</p>
          )}
        </div>
      )}
      
      <div
        className="prose prose-sm max-w-none text-gray-700 leading-relaxed"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }}
      />
    </Card>
  );
};
