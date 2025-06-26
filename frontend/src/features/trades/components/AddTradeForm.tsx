
import React, { useState } from 'react';
import { useTradeStore } from '../../../store/trades';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { TradeCreateRequest } from '../../../services/trades';
import { PlaybookSelector } from './PlaybookSelector';

interface AddTradeFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
}

const AddTradeForm: React.FC<AddTradeFormProps> = ({ onSuccess, onCancel }) => {
  const { createTrade, isLoading, error } = useTradeStore();
  const [formData, setFormData] = useState<TradeCreateRequest>({
    symbol: '',
    direction: 'long',
    quantity: 1,
    entry_price: 0,
    entry_time: new Date().toISOString().slice(0, 16),
    strategy_tag: '',
    confidence_score: 5,
    notes: '',
    playbook_id: null
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createTrade(formData);
      onSuccess?.();
      // Reset form
      setFormData({
        symbol: '',
        direction: 'long',
        quantity: 1,
        entry_price: 0,
        entry_time: new Date().toISOString().slice(0, 16),
        strategy_tag: '',
        confidence_score: 5,
        notes: '',
        playbook_id: null
      });
    } catch (error) {
      // Error handled by store
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          name="symbol"
          placeholder="Symbol (e.g., AAPL, ES)"
          value={formData.symbol}
          onChange={handleChange}
          required
        />

        <select
          name="direction"
          value={formData.direction}
          onChange={handleChange}
          className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        >
          <option value="long">Long</option>
          <option value="short">Short</option>
        </select>

        <Input
          name="quantity"
          type="number"
          placeholder="Quantity"
          value={formData.quantity}
          onChange={handleChange}
          min="1"
          required
        />

        <Input
          name="entry_price"
          type="number"
          step="0.01"
          placeholder="Entry Price"
          value={formData.entry_price}
          onChange={handleChange}
          required
        />

        <Input
          name="entry_time"
          type="datetime-local"
          value={formData.entry_time}
          onChange={handleChange}
          required
        />

        <Input
          name="strategy_tag"
          placeholder="Strategy Tag (optional)"
          value={formData.strategy_tag}
          onChange={handleChange}
        />

        <Input
          name="confidence_score"
          type="number"
          min="1"
          max="10"
          placeholder="Confidence (1-10)"
          value={formData.confidence_score}
          onChange={handleChange}
        />
      </div>

      <textarea
        name="notes"
        placeholder="Trade notes (optional)"
        value={formData.notes}
        onChange={handleChange}
        rows={3}
        className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      <PlaybookSelector
        selectedPlaybookId={formData.playbook_id}
        onPlaybookChange={(playbookId) => setFormData(prev => ({ ...prev, playbook_id: playbookId }))}
      />

      <div className="flex space-x-3">
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Adding Trade...' : 'Add Trade'}
        </Button>
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  );
};

export default AddTradeForm;
