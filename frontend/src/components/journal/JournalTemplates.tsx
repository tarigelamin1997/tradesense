import React, { useState } from 'react';
import { FileText, TrendingUp, Target, Plus, ChevronDown } from 'lucide-react';
import { format } from 'date-fns';

export interface JournalTemplate {
  id: string;
  name: string;
  icon: React.ReactNode;
  content: string;
  variables?: string[];
}

export const DEFAULT_TEMPLATES: JournalTemplate[] = [
  {
    id: 'daily-review',
    name: 'Daily Review',
    icon: <FileText className="w-4 h-4" />,
    content: `<h1>Daily Trading Review - {DATE}</h1>

<h2>Market Conditions</h2>
<ul>
<li><strong>Overall trend:</strong> [Bullish/Bearish/Sideways]</li>
<li><strong>Key levels:</strong> </li>
<li><strong>Major news:</strong> </li>
</ul>

<h2>Trades Taken</h2>
<ul>
<li><strong>Total trades:</strong> </li>
<li><strong>Winners/Losers:</strong> </li>
<li><strong>P&L:</strong> $</li>
</ul>

<h2>What Went Well</h2>
<ul>
<li></li>
</ul>

<h2>What Could Improve</h2>
<ul>
<li></li>
</ul>

<h2>Lessons Learned</h2>
<ul>
<li></li>
</ul>

<h2>Tomorrow's Plan</h2>
<ul>
<li></li>
</ul>

<h2>Emotional State</h2>
<p><strong>Mood:</strong> [😊 😐 😔 😡 😰]<br>
<strong>Confidence:</strong> [1-10]</p>`,
    variables: ['DATE']
  },
  {
    id: 'trade-post-mortem',
    name: 'Trade Post-Mortem',
    icon: <TrendingUp className="w-4 h-4" />,
    content: `<h1>Trade Post-Mortem - {SYMBOL}</h1>

<h2>Trade Details</h2>
<ul>
<li><strong>Symbol:</strong> {SYMBOL}</li>
<li><strong>Entry/Exit:</strong> {ENTRY_PRICE} / {EXIT_PRICE}</li>
<li><strong>P&L:</strong> {PNL}</li>
<li><strong>Date:</strong> {DATE}</li>
</ul>

<h2>Pre-Trade Analysis</h2>
<p><strong>Why did I take this trade?</strong></p>
<p></p>

<p><strong>What was my thesis?</strong></p>
<p></p>

<p><strong>Risk/Reward planned:</strong></p>
<p></p>

<h2>Execution</h2>
<p><strong>Entry timing:</strong></p>
<p></p>

<p><strong>Position sizing:</strong></p>
<p></p>

<p><strong>Exit execution:</strong></p>
<p></p>

<h2>Results Analysis</h2>
<p><strong>What worked:</strong></p>
<ul>
<li></li>
</ul>

<p><strong>What didn't work:</strong></p>
<ul>
<li></li>
</ul>

<p><strong>Could I have done better?</strong></p>
<p></p>

<h2>Lessons for Next Time</h2>
<ul>
<li></li>
</ul>

<h2>Grade This Trade: [A-F]</h2>`,
    variables: ['SYMBOL', 'ENTRY_PRICE', 'EXIT_PRICE', 'PNL', 'DATE']
  },
  {
    id: 'strategy-planning',
    name: 'Strategy Planning',
    icon: <Target className="w-4 h-4" />,
    content: `<h1>Strategy Development - {STRATEGY_NAME}</h1>

<h2>Strategy Overview</h2>
<ul>
<li><strong>Name:</strong> {STRATEGY_NAME}</li>
<li><strong>Type:</strong> [Trend/Mean Reversion/Breakout/etc]</li>
<li><strong>Timeframe:</strong> </li>
<li><strong>Markets:</strong> </li>
</ul>

<h2>Entry Rules</h2>
<ol>
<li></li>
<li></li>
<li></li>
</ol>

<h2>Exit Rules</h2>
<ul>
<li><strong>Stop Loss:</strong> </li>
<li><strong>Take Profit:</strong> </li>
<li><strong>Time Exit:</strong> </li>
</ul>

<h2>Risk Management</h2>
<ul>
<li><strong>Position Size:</strong> </li>
<li><strong>Max Risk per Trade:</strong> </li>
<li><strong>Max Daily Loss:</strong> </li>
</ul>

<h2>Backtesting Notes</h2>
<p></p>

<h2>Forward Testing Plan</h2>
<p></p>`,
    variables: ['STRATEGY_NAME']
  }
];

interface JournalTemplatesProps {
  onSelectTemplate: (template: JournalTemplate) => void;
  customTemplates?: JournalTemplate[];
  tradeData?: {
    symbol?: string;
    entry_price?: number;
    exit_price?: number;
    pnl?: number;
  };
}

export const JournalTemplates: React.FC<JournalTemplatesProps> = ({
  onSelectTemplate,
  customTemplates = [],
  tradeData
}) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const [showCustomTemplate, setShowCustomTemplate] = useState(false);
  const [customTemplate, setCustomTemplate] = useState({
    name: '',
    content: ''
  });

  const allTemplates = [...DEFAULT_TEMPLATES, ...customTemplates];

  // Replace variables in template
  const processTemplate = (template: JournalTemplate) => {
    let processedContent = template.content;
    
    // Replace standard variables
    processedContent = processedContent.replace(/{DATE}/g, format(new Date(), 'MMMM d, yyyy'));
    
    // Replace trade-specific variables if trade data is provided
    if (tradeData) {
      if (tradeData.symbol) {
        processedContent = processedContent.replace(/{SYMBOL}/g, tradeData.symbol);
      }
      if (tradeData.entry_price !== undefined) {
        processedContent = processedContent.replace(/{ENTRY_PRICE}/g, `$${tradeData.entry_price.toFixed(2)}`);
      }
      if (tradeData.exit_price !== undefined) {
        processedContent = processedContent.replace(/{EXIT_PRICE}/g, `$${tradeData.exit_price.toFixed(2)}`);
      }
      if (tradeData.pnl !== undefined) {
        processedContent = processedContent.replace(/{PNL}/g, `$${tradeData.pnl.toFixed(2)}`);
      }
    }
    
    // Replace any remaining variables with placeholders
    processedContent = processedContent.replace(/{STRATEGY_NAME}/g, '[Strategy Name]');
    
    return {
      ...template,
      content: processedContent
    };
  };

  const handleSelectTemplate = (template: JournalTemplate) => {
    const processed = processTemplate(template);
    onSelectTemplate(processed);
    setShowDropdown(false);
  };

  const handleCreateCustomTemplate = () => {
    if (customTemplate.name && customTemplate.content) {
      const newTemplate: JournalTemplate = {
        id: `custom-${Date.now()}`,
        name: customTemplate.name,
        icon: <FileText className="w-4 h-4" />,
        content: customTemplate.content,
        variables: []
      };
      
      onSelectTemplate(newTemplate);
      setShowCustomTemplate(false);
      setCustomTemplate({ name: '', content: '' });
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        className="flex items-center space-x-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
      >
        <FileText className="w-4 h-4" />
        <span>Templates</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
      </button>
      
      {showDropdown && (
        <div className="absolute top-full left-0 mt-2 w-72 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
          <div className="p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Select a Template</h3>
            
            <div className="space-y-2">
              {allTemplates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => handleSelectTemplate(template)}
                  className="w-full flex items-start space-x-3 p-3 hover:bg-gray-50 rounded-lg transition-colors text-left"
                >
                  <div className="mt-0.5 text-gray-500">
                    {template.icon}
                  </div>
                  <div>
                    <p className="font-medium text-sm">{template.name}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {template.id === 'daily-review' && 'Review your daily trading performance'}
                      {template.id === 'trade-post-mortem' && 'Analyze a specific trade in detail'}
                      {template.id === 'strategy-planning' && 'Plan and document a trading strategy'}
                    </p>
                  </div>
                </button>
              ))}
              
              <button
                onClick={() => {
                  setShowCustomTemplate(true);
                  setShowDropdown(false);
                }}
                className="w-full flex items-center space-x-3 p-3 hover:bg-gray-50 rounded-lg transition-colors text-left border-t border-gray-100 pt-4"
              >
                <Plus className="w-4 h-4 text-gray-500" />
                <span className="font-medium text-sm">Create Custom Template</span>
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Custom Template Modal */}
      {showCustomTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Create Custom Template</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template Name
                </label>
                <input
                  type="text"
                  value={customTemplate.name}
                  onChange={(e) => setCustomTemplate({ ...customTemplate, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Weekly Review"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Template Content
                </label>
                <textarea
                  value={customTemplate.content}
                  onChange={(e) => setCustomTemplate({ ...customTemplate, content: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={10}
                  placeholder="Enter your template HTML content. Use {VARIABLE} for dynamic content."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Available variables: {'{DATE}'}, {'{SYMBOL}'}, {'{ENTRY_PRICE}'}, {'{EXIT_PRICE}'}, {'{PNL}'}
                </p>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowCustomTemplate(false);
                    setCustomTemplate({ name: '', content: '' });
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateCustomTemplate}
                  disabled={!customTemplate.name || !customTemplate.content}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Template
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default JournalTemplates;