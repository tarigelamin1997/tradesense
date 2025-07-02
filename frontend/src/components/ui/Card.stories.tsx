
import type { Meta, StoryObj } from '@storybook/react';
import { Card, CardHeader, CardTitle, CardContent } from './Card';
import { Button } from './Button';

const meta: Meta<typeof Card> = {
  title: 'UI/Card',
  component: Card,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A flexible card component for displaying content in a contained format.',
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    className: {
      control: 'text',
      description: 'Additional CSS classes',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Basic: Story = {
  render: () => (
    <Card className="w-80">
      <CardContent className="p-6">
        <p>This is a basic card with some content.</p>
      </CardContent>
    </Card>
  ),
};

export const WithHeader: Story = {
  render: () => (
    <Card className="w-80">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
      </CardHeader>
      <CardContent>
        <p>This card has a header with a title.</p>
      </CardContent>
    </Card>
  ),
};

export const TradingMetric: Story = {
  render: () => (
    <Card className="w-80">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-gray-600">Total Profit</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-green-600">$12,345.67</div>
        <p className="text-sm text-gray-500 mt-1">+8.3% from last month</p>
      </CardContent>
    </Card>
  ),
};

export const WithActions: Story = {
  render: () => (
    <Card className="w-80">
      <CardHeader>
        <CardTitle>Upload Trades</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p>Upload your trading data to get started with analytics.</p>
        <div className="flex gap-2">
          <Button size="sm">Upload CSV</Button>
          <Button variant="outline" size="sm">Learn More</Button>
        </div>
      </CardContent>
    </Card>
  ),
};

export const Dashboard: Story = {
  render: () => (
    <div className="grid grid-cols-2 gap-4 w-96">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm text-gray-600">Win Rate</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xl font-bold">68.5%</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm text-gray-600">Avg. Trade</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xl font-bold">$125.43</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm text-gray-600">Total Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xl font-bold">1,247</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm text-gray-600">Sharpe Ratio</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xl font-bold">1.85</div>
        </CardContent>
      </Card>
    </div>
  ),
};
