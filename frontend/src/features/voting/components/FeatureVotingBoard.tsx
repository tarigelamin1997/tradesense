
import React, { useState, useEffect } from 'react';
import { Card, Button, Input, Modal } from '../../../components/ui';
import { featureService } from '../../../services/features';

interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  category: string;
  status: string;
  priority: string;
  upvotes: number;
  downvotes: number;
  net_votes: number;
  user_vote?: 'upvote' | 'downvote';
  created_at: string;
  user_id: string;
}

interface NewFeatureRequest {
  title: string;
  description: string;
  category: string;
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
    category: 'analytics'
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

  useEffect(() => {
    loadFeatures();
  }, [selectedCategory, selectedStatus, sortBy]);

  const loadFeatures = async () => {
    try {
      setLoading(true);
      const params = {
        category: selectedCategory === 'all' ? undefined : selectedCategory,
        status: selectedStatus === 'all' ? undefined : selectedStatus,
        sort_by: sortBy
      };
      const data = await featureService.getFeatures(params);
      setFeatures(data);
    } catch (error) {
      console.error('Failed to load features:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleVote = async (featureId: string, voteType: 'upvote' | 'downvote') => {
    try {
      await featureService.voteOnFeature(featureId, voteType);
      // Update local state
      setFeatures(features.map(feature => {
        if (feature.id === featureId) {
          const wasUpvote = feature.user_vote === 'upvote';
          const wasDownvote = feature.user_vote === 'downvote';
          
          let newUpvotes = feature.upvotes;
          let newDownvotes = feature.downvotes;
          
          // Remove previous vote
          if (wasUpvote) newUpvotes--;
          if (wasDownvote) newDownvotes--;
          
          // Add new vote
          if (voteType === 'upvote') newUpvotes++;
          if (voteType === 'downvote') newDownvotes++;
          
          return {
            ...feature,
            upvotes: newUpvotes,
            downvotes: newDownvotes,
            net_votes: newUpvotes - newDownvotes,
            user_vote: feature.user_vote === voteType ? undefined : voteType
          };
        }
        return feature;
      }));
    } catch (error) {
      console.error('Failed to vote:', error);
    }
  };

  const handleCreateFeature = async () => {
    try {
      const created = await featureService.createFeature(newFeature);
      setFeatures([created, ...features]);
      setShowCreateModal(false);
      setNewFeature({ title: '', description: '', category: 'analytics' });
    } catch (error) {
      console.error('Failed to create feature:', error);
    }
  };

  const getStatusColor = (status: string) => {
    const colors = {
      proposed: 'bg-blue-100 text-blue-800',
      reviewing: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      in_progress: 'bg-purple-100 text-purple-800',
      completed: 'bg-gray-100 text-gray-800',
      rejected: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityColor = (priority: string) => {
    const colors = {
      critical: 'text-red-600',
      high: 'text-orange-600',
      medium: 'text-yellow-600',
      low: 'text-green-600'
    };
    return colors[priority] || 'text-gray-600';
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Feature Voting Board</h1>
        <Button onClick={() => setShowCreateModal(true)} className="bg-blue-600 hover:bg-blue-700">
          Request Feature
        </Button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              {categories.map(cat => (
                <option key={cat.value} value={cat.value}>{cat.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              {statuses.map(status => (
                <option key={status.value} value={status.value}>{status.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md"
            >
              <option value="votes">Most Voted</option>
              <option value="created_at">Newest</option>
              <option value="priority">Priority</option>
            </select>
          </div>
        </div>
      </div>

      {/* Feature List */}
      {loading ? (
        <div className="text-center py-8">Loading features...</div>
      ) : (
        <div className="space-y-4">
          {features.map(feature => (
            <Card key={feature.id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-xl font-semibold text-gray-900">{feature.title}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(feature.status)}`}>
                      {feature.status.replace('_', ' ')}
                    </span>
                    <span className={`text-sm font-medium ${getPriorityColor(feature.priority)}`}>
                      {feature.priority} priority
                    </span>
                  </div>
                  
                  <p className="text-gray-600 mb-3">{feature.description}</p>
                  
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span className="capitalize">{feature.category}</span>
                    <span>•</span>
                    <span>{new Date(feature.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                
                {/* Voting Controls */}
                <div className="flex items-center gap-2 ml-4">
                  <div className="text-center">
                    <Button
                      onClick={() => handleVote(feature.id, 'upvote')}
                      className={`p-2 ${feature.user_vote === 'upvote' ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600'} hover:bg-green-200`}
                    >
                      ↑
                    </Button>
                    <div className="text-lg font-bold text-gray-900">{feature.net_votes}</div>
                    <Button
                      onClick={() => handleVote(feature.id, 'downvote')}
                      className={`p-2 ${feature.user_vote === 'downvote' ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'} hover:bg-red-200`}
                    >
                      ↓
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Feature Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)}>
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-4">Request New Feature</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Title</label>
              <Input
                value={newFeature.title}
                onChange={(e) => setNewFeature({...newFeature, title: e.target.value})}
                placeholder="Brief feature title"
                className="w-full"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
              <select
                value={newFeature.category}
                onChange={(e) => setNewFeature({...newFeature, category: e.target.value})}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                {categories.slice(1).map(cat => (
                  <option key={cat.value} value={cat.value}>{cat.label}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <textarea
                value={newFeature.description}
                onChange={(e) => setNewFeature({...newFeature, description: e.target.value})}
                placeholder="Detailed description of the feature request"
                rows={4}
                className="w-full p-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>
          
          <div className="flex justify-end gap-2 mt-6">
            <Button
              onClick={() => setShowCreateModal(false)}
              className="bg-gray-300 hover:bg-gray-400 text-gray-700"
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateFeature}
              disabled={!newFeature.title || !newFeature.description}
              className="bg-blue-600 hover:bg-blue-700"
            >
              Submit Request
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default FeatureVotingBoard;
