
import React, { useState, useEffect } from 'react';
import { milestoneService, UserProgress, Milestone } from '../../../services/milestones';

interface MilestoneDashboardProps {
  className?: string;
}

const MilestoneDashboard: React.FC<MilestoneDashboardProps> = ({ className = '' }) => {
  const [progress, setProgress] = useState<UserProgress | null>(null);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [progressData, milestonesData] = await Promise.all([
        milestoneService.getUserProgress(),
        milestoneService.getMilestones({ limit: 20 })
      ]);
      setProgress(progressData);
      setMilestones(milestonesData);
    } catch (error) {
      console.error('Error loading milestone data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredMilestones = selectedCategory === 'all' 
    ? milestones 
    : milestones.filter(m => m.category === selectedCategory);

  const categories = ['all', 'journaling', 'performance', 'discipline', 'analytics'];

  if (loading) {
    return (
      <div className={`space-y-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!progress) {
    return <div className={className}>Failed to load milestone data</div>;
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Enhanced Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 text-white mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold mb-2">🏆 Trader Profile</h2>
            <p className="text-blue-100">Track your journey to trading mastery</p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold">Level {progress.level}</div>
            <div className="text-blue-100">{progress.total_xp.toLocaleString()} XP</div>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex justify-between text-sm mb-1">
            <span>Progress to Level {progress.level + 1}</span>
            <span>{progress.level_progress.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div 
              className="bg-white rounded-full h-2 transition-all duration-300"
              style={{ width: `${progress.level_progress}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Level Progress */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {milestoneService.getLevelTitle(progress.level)}
            </h3>
            <p className="text-sm text-gray-600">
              Level {progress.level} • {Math.round(progress.level_progress)}% to next level
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-600">{progress.total_xp}</div>
            <div className="text-xs text-gray-500">Total XP</div>
          </div>
        </div>
        
        {/* XP Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
          <div 
            className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-300"
            style={{ width: `${progress.level_progress}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-xs text-gray-500">
          <span>Current Level</span>
          <span>{progress.xp_to_next_level} XP to next level</span>
        </div>
      </div>

      {/* Active Streaks */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">📝</span>
            <div>
              <div className="font-semibold text-gray-900">
                {progress.active_streaks.journaling_days} days
              </div>
              <div className="text-sm text-gray-600">Journaling Streak</div>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">🚀</span>
            <div>
              <div className="font-semibold text-gray-900">
                {progress.active_streaks.win_streak} wins
              </div>
              <div className="text-sm text-gray-600">Current Win Streak</div>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">🧘</span>
            <div>
              <div className="font-semibold text-gray-900">
                {progress.active_streaks.discipline_streak} days
              </div>
              <div className="text-sm text-gray-600">Discipline Streak</div>
            </div>
          </div>
        </div>
      </div>

      {/* Category Filter */}
      <div className="flex space-x-2 overflow-x-auto">
        {categories.map(category => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
              selectedCategory === category
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {category.charAt(0).toUpperCase() + category.slice(1)}
          </button>
        ))}
      </div>

      {/* Milestones Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredMilestones.map(milestone => (
          <div
            key={milestone.id}
            className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
            style={{
              boxShadow: milestoneService.getRarityGlow(milestone.rarity)
            }}
          >
            <div className="flex items-start space-x-3">
              <div 
                className="text-3xl flex-shrink-0"
                style={{
                  filter: `drop-shadow(${milestoneService.getRarityGlow(milestone.rarity)})`
                }}
              >
                {milestone.badge_icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <h4 className="font-semibold text-gray-900 truncate">
                    {milestone.title}
                  </h4>
                  <span
                    className="px-2 py-1 text-xs font-medium rounded-full"
                    style={{
                      backgroundColor: `${milestoneService.getRarityColor(milestone.rarity)}20`,
                      color: milestoneService.getRarityColor(milestone.rarity)
                    }}
                  >
                    {milestone.rarity}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">
                  {milestone.description}
                </p>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>+{milestone.xp_points} XP</span>
                  <span>{new Date(milestone.achieved_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredMilestones.length === 0 && (
        <div className="text-center py-8">
          <div className="text-gray-400 text-lg mb-2">🎯</div>
          <p className="text-gray-600">
            {selectedCategory === 'all' 
              ? 'No milestones yet. Start trading to unlock achievements!'
              : `No ${selectedCategory} milestones yet. Keep working on your trading skills!`}
          </p>
        </div>
      )}

      {/* Category Summary */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="font-semibold text-gray-900 mb-3">Category Progress</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(progress.category_progress).map(([category, data]) => (
            <div key={category} className="text-center">
              <div className="text-xl font-bold text-gray-900">{data.count}</div>
              <div className="text-sm text-gray-600 capitalize">{category}</div>
              <div className="text-xs text-gray-500">{data.xp} XP</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default MilestoneDashboard;
