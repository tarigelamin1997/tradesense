
import type { Meta, StoryObj } from '@storybook/react';
import { Input } from './Input';

const meta: Meta<typeof Input> = {
  title: 'UI/Input',
  component: Input,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A flexible input component for forms and user input.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    type: {
      control: 'select',
      options: ['text', 'email', 'password', 'number', 'search'],
      description: 'Input type',
    },
    placeholder: {
      control: 'text',
      description: 'Placeholder text',
    },
    disabled: {
      control: 'boolean',
      description: 'Disabled state',
    },
    error: {
      control: 'boolean',
      description: 'Error state',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    placeholder: 'Enter text...',
  },
};

export const Email: Story = {
  args: {
    type: 'email',
    placeholder: 'Enter your email',
  },
};

export const Password: Story = {
  args: {
    type: 'password',
    placeholder: 'Enter password',
  },
};

export const Number: Story = {
  args: {
    type: 'number',
    placeholder: 'Enter quantity',
  },
};

export const Search: Story = {
  args: {
    type: 'search',
    placeholder: 'Search trades...',
  },
};

export const Disabled: Story = {
  args: {
    placeholder: 'Disabled input',
    disabled: true,
    value: 'Cannot edit this',
  },
};

export const WithError: Story = {
  args: {
    placeholder: 'Enter email',
    error: true,
    value: 'invalid-email',
  },
};

export const TradingForm: Story = {
  render: () => (
    <div className="w-80 space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Symbol
        </label>
        <Input placeholder="e.g., AAPL" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Quantity
        </label>
        <Input type="number" placeholder="100" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Price
        </label>
        <Input type="number" placeholder="150.25" step="0.01" />
      </div>
    </div>
  ),
};

export const LoginForm: Story = {
  render: () => (
    <div className="w-80 space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Email
        </label>
        <Input type="email" placeholder="your@email.com" />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Password
        </label>
        <Input type="password" placeholder="••••••••" />
      </div>
    </div>
  ),
};
