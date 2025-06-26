
import React, { useState, useEffect } from 'react';
import { Card, Button, Modal, Input } from '../../../components/ui';
import { featuresService } from '../../../services/features';

interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  category: string;
  status: string;
  priority: string;
  upvotes: number;
  downvotes: number;
  created_at: string;
  user_id: string;
}

interface NewFeatureRequest {
  title: string;
  description: string;
  category: string;
  priority?: string;
}

const FeatureVotingBoard: React.FC = () => {
  const [features, setFeatures] = useState<FeatureRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('votes');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newFeature, setNewFeature] = useState<NewFeatureRequest>({
    title: '',
    description: '',
    category: 'analytics',
    priority: 'medium'
  });

  const categories = [
    { value: 'all', label: 'All Categories' },
    { value: 'analytics', label: 'Analytics' },
    { value: 'ui', label: 'User Interface' },
    { value: 'integration', label: 'Integration' },
    { value: 'performance', label: 'Performance' },
    { value: 'security', label: 'Security' },
    { value: 'other', label: 'Other' }
  ];

  const statuses = [
    { value: 'all', label: 'All Statuses' },
    { value: 'proposed', label: 'Proposed' },
    { value: 'reviewing', label: 'Under Review' },
    { value: 'approved', label: 'Approved' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'completed', label: 'Completed' },
    { value: 'rejected', label: 'Rejected' }
  ];

  const priorities = [
    { value: 'low', label: 'Low', color: 'text-gray-500' },
    { value: 'medium', label: 'Medium', color: 'text-blue-500' },
    { value: 'high', label: 'High', color: 'text-orange-500' },
    { value: 'critical', label: 'Critical', color: 'text-red-500' }
  ];

  useEffect(() => {
    loadFeatures();
  }, [selectedCategory, selectedStatus, sortBy]);

  const loadFeatures = async () => {
    try {
      setLoading(true);
      const response = await featuresService.getFeatures({
        category: selectedCategory,
        status: selectedStatus,
        sort_by: sortBy
      });
      setFeatures(response.data);
    } catch (error) {
      console.error('Failed to load features:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVote = async (featureId: string, voteType: 'upvote' | 'downvote') => {
    try {
      await featuresService.voteOnFeature({
        feature_request_id: featureId,
        vote_type: voteType
      });
      loadFeatures(); // Refresh to show updated vote counts
    } catch (error) {
      console.error('Failed to vote:', error);
    }
  };

  const handleCreateFeature = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await featuresService.createFeature(newFeature);
      setShowCreateModal(false);
      setNewFeature({
        title: '',
        description: '',
        category: 'analytics',
        priority: 'medium'
      });
      loadFeatures();
    } catch (error) {
      console.error('Failed to create feature:', error);
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      proposed: 'bg-gray-100 text-gray-800',
      reviewing: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      in_progress: 'bg-blue-100 text-blue-800',
      completed: 'bg-purple-100 text-purple-800',
      rejected: 'bg-red-100 text-red-800'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityColor = (priority: string) => {
    const priority_obj = priorities.find(p => p.value === priority);
    return priority_obj?.color || 'text-gray-500';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Feature Voting Board</h1>
        <Button onClick={() => setShowCreateModal(true)} className="bg-blue-600 hover:bg-blue-700">
          Suggest Feature
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Category
          </label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            {categories.map(cat => (
              <option key={cat.value} value={cat.value}>{cat.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            {statuses.map(status => (
              <option key={status.value} value={status.value}>{status.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Sort by
          </label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="votes">Most Votes</option>
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
            <option value="priority">Priority</option>
          </select>
        </div>
      </div>

      {/* Feature List */}
      <div className="space-y-4">
        {features.map((feature) => (
          <Card key={feature.id} className="p-6">
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {feature.title}
                  </h3>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(feature.status)}`}>
                    {feature.status.charAt(0).toUpperCase() + feature.status.slice(1)}
                  </span>
                  <span className={`text-sm font-medium ${getPriorityColor(feature.priority)}`}>
                    {feature.priority.charAt(0).toUpperCase() + feature.priority.slice(1)} Priority
                  </span>
                </div>
                
                <p className="text-gray-700 mb-3">{feature.description}</p>
                
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span className="bg-gray-100 px-2 py-1 rounded">
                    {feature.category}
                  </span>
                  <span>
                    Created {new Date(feature.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {/* Voting */}
              <div className="flex flex-col items-center gap-2 ml-6">
                <Button
                  onClick={() => handleVote(feature.id, 'upvote')}
                  className="p-2 bg-green-50 hover:bg-green-100 text-green-600 border border-green-200"
                  size="sm"
                >
                  ▲ {feature.upvotes}
                </Button>
                
                <div className="text-sm font-medium text-gray-700">
                  {feature.upvotes - feature.downvotes}
                </div>
                
                <Button
                  onClick={() => handleVote(feature.id, 'downvote')}
                  className="p-2 bg-red-50 hover:bg-red-100 text-red-600 border border-red-200"
                  size="sm"
                >
                  ▼ {feature.downvotes}
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {features.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No features found matching your criteria.</p>
          <Button 
            onClick={() => setShowCreateModal(true)}
            className="mt-4 bg-blue-600 hover:bg-blue-700"
          >
            Be the first to suggest a feature!
          </Button>
        </div>
      )}

      {/* Create Feature Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Suggest New Feature"
      >
        <form onSubmit={handleCreateFeature} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Feature Title
            </label>
            <Input
              type="text"
              value={newFeature.title}
              onChange={(e) => setNewFeature({ ...newFeature, title: e.target.value })}
              placeholder="Brief, descriptive title..."
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={newFeature.description}
              onChange={(e) => setNewFeature({ ...newFeature, description: e.target.value })}
              placeholder="Detailed description of the feature..."
              rows={4}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={newFeature.category}
              onChange={(e) => setNewFeature({ ...newFeature, category: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              {categories.filter(cat => cat.value !== 'all').map(cat => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Priority
            </label>
            <select
              value={newFeature.priority}
              onChange={(e) => setNewFeature({ ...newFeature, priority: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              {priorities.map(priority => (
                <option key={priority.value} value={priority.value}>{priority.label}</option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              onClick={() => setShowCreateModal(false)}
              variant="outline"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700"
            >
              Submit Feature
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default FeatureVotingBoard;
