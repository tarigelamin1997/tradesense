
import React, { useState, useEffect } from 'react';
import { 
  User, 
  TrendingUp, 
  Award, 
  Target, 
  Calendar,
  Edit3,
  Camera,
  Save,
  X,
  Trophy,
  Star,
  Zap,
  Shield,
  Crown,
  Medal,
  ArrowUp,
  ArrowDown,
  DollarSign,
  Percent,
  BarChart3,
  Clock,
  Fire
} from 'lucide-react';

interface TraderProfile {
  id: string;
  username: string;
  email: string;
  displayName: string;
  bio: string;
  avatar: string;
  tradingExperience: string;
  riskTolerance: 'conservative' | 'moderate' | 'aggressive';
  tradingGoals: string[];
  customization: {
    theme: 'light' | 'dark' | 'auto';
    primaryColor: string;
    showPublicStats: boolean;
    publicDisplayName: string;
  };
}

interface TradingStats {
  totalTrades: number;
  winRate: number;
  totalPnL: number;
  avgWin: number;
  avgLoss: number;
  maxWin: number;
  maxLoss: number;
  profitFactor: number;
  sharpeRatio: number;
  maxDrawdown: number;
  currentStreak: number;
  bestStreak: number;
  totalTradingDays: number;
  activeDays: number;
  avgDailyPnL: number;
  consistency: number;
}

interface Achievement {
  id: string;
  title: string;
  description: string;
  category: 'trading' | 'consistency' | 'growth' | 'milestone' | 'streak';
  icon: React.ReactNode;
  earned: boolean;
  earnedDate?: string;
  progress?: number;
  requirement?: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
}

const ACHIEVEMENTS: Achievement[] = [
  {
    id: 'first_profit',
    title: 'First Profit',
    description: 'Made your first profitable trade',
    category: 'milestone',
    icon: <DollarSign size={20} className="text-green-500" />,
    earned: true,
    earnedDate: '2024-01-15',
    rarity: 'common'
  },
  {
    id: 'win_streak_5',
    title: 'Hot Streak',
    description: 'Achieved 5 consecutive winning trades',
    category: 'streak',
    icon: <Fire size={20} className="text-orange-500" />,
    earned: true,
    earnedDate: '2024-02-03',
    rarity: 'rare'
  },
  {
    id: 'consistency_master',
    title: 'Consistency Master',
    description: 'Maintained 70%+ win rate for 30 days',
    category: 'consistency',
    icon: <Target size={20} className="text-blue-500" />,
    earned: false,
    progress: 65,
    requirement: '70% win rate for 30 days',
    rarity: 'epic'
  },
  {
    id: 'risk_manager',
    title: 'Risk Manager',
    description: 'Never exceeded 2% risk per trade for 100 trades',
    category: 'trading',
    icon: <Shield size={20} className="text-purple-500" />,
    earned: true,
    earnedDate: '2024-03-10',
    rarity: 'rare'
  },
  {
    id: 'profit_king',
    title: 'Profit King',
    description: 'Achieved $10,000+ in total profits',
    category: 'milestone',
    icon: <Crown size={20} className="text-yellow-500" />,
    earned: false,
    progress: 7500,
    requirement: '$10,000 total profit',
    rarity: 'legendary'
  },
  {
    id: 'early_bird',
    title: 'Early Bird',
    description: 'Traded during market open 20 times',
    category: 'trading',
    icon: <Clock size={20} className="text-indigo-500" />,
    earned: true,
    earnedDate: '2024-02-20',
    rarity: 'common'
  }
];

export const ProfilePage: React.FC = () => {
  const [profile, setProfile] = useState<TraderProfile>({
    id: '1',
    username: 'trader_pro',
    email: 'trader@example.com',
    displayName: 'Alex Thompson',
    bio: 'Passionate day trader focused on momentum strategies and risk management.',
    avatar: '',
    tradingExperience: '2-5 years',
    riskTolerance: 'moderate',
    tradingGoals: ['Consistent profitability', 'Risk management', 'Strategy development'],
    customization: {
      theme: 'auto',
      primaryColor: '#3B82F6',
      showPublicStats: true,
      publicDisplayName: 'Alex T.'
    }
  });

  const [stats, setStats] = useState<TradingStats>({
    totalTrades: 342,
    winRate: 68.5,
    totalPnL: 7500,
    avgWin: 85,
    avgLoss: -45,
    maxWin: 520,
    maxLoss: -180,
    profitFactor: 1.89,
    sharpeRatio: 1.45,
    maxDrawdown: -8.2,
    currentStreak: 3,
    bestStreak: 8,
    totalTradingDays: 85,
    activeDays: 78,
    avgDailyPnL: 96.15,
    consistency: 72.3
  });

  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'stats' | 'achievements' | 'settings'>('overview');

  const getRarityColor = (rarity: Achievement['rarity']) => {
    switch (rarity) {
      case 'common': return 'border-gray-300 bg-gray-50';
      case 'rare': return 'border-blue-300 bg-blue-50';
      case 'epic': return 'border-purple-300 bg-purple-50';
      case 'legendary': return 'border-yellow-300 bg-yellow-50';
    }
  };

  const getRarityBadge = (rarity: Achievement['rarity']) => {
    switch (rarity) {
      case 'common': return <span className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded">Common</span>;
      case 'rare': return <span className="text-xs px-2 py-1 bg-blue-200 text-blue-700 rounded">Rare</span>;
      case 'epic': return <span className="text-xs px-2 py-1 bg-purple-200 text-purple-700 rounded">Epic</span>;
      case 'legendary': return <span className="text-xs px-2 py-1 bg-yellow-200 text-yellow-700 rounded">Legendary</span>;
    }
  };

  const earnedAchievements = ACHIEVEMENTS.filter(a => a.earned);
  const totalAchievements = ACHIEVEMENTS.length;

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-start gap-6">
          <div className="relative">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
              {profile.avatar ? (
                <img src={profile.avatar} alt="Avatar" className="w-full h-full rounded-full object-cover" />
              ) : (
                profile.displayName.split(' ').map(n => n[0]).join('')
              )}
            </div>
            <button className="absolute -bottom-2 -right-2 w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center hover:bg-blue-600">
              <Camera size={16} />
            </button>
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-gray-900">{profile.displayName}</h1>
              <span className="text-gray-500">@{profile.username}</span>
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
              >
                {isEditing ? <X size={16} /> : <Edit3 size={16} />}
              </button>
            </div>
            
            <p className="text-gray-600 mb-4">{profile.bio}</p>
            
            <div className="flex items-center gap-6 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <BarChart3 size={16} />
                Experience: {profile.tradingExperience}
              </div>
              <div className="flex items-center gap-1">
                <Target size={16} />
                Risk: {profile.riskTolerance}
              </div>
              <div className="flex items-center gap-1">
                <Award size={16} />
                {earnedAchievements.length}/{totalAchievements} Achievements
              </div>
            </div>
          </div>

          <div className="text-right">
            <div className="text-3xl font-bold text-green-600">
              ${stats.totalPnL.toFixed(0)}
            </div>
            <div className="text-sm text-gray-600">Total P&L</div>
            <div className="text-sm text-gray-600 mt-2">
              {stats.totalTrades} trades • {stats.winRate.toFixed(1)}% win rate
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
        {[
          { id: 'overview', label: 'Overview', icon: <User size={16} /> },
          { id: 'stats', label: 'Statistics', icon: <BarChart3 size={16} /> },
          { id: 'achievements', label: 'Achievements', icon: <Award size={16} /> },
          { id: 'settings', label: 'Settings', icon: <Edit3 size={16} /> }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md transition-colors ${
              activeTab === tab.id 
                ? 'bg-white text-blue-600 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content based on active tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Quick Stats */}
          <div className="lg:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg border">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp size={16} className="text-green-500" />
                <span className="text-sm text-gray-600">Win Rate</span>
              </div>
              <div className="text-2xl font-bold">{stats.winRate.toFixed(1)}%</div>
            </div>
            
            <div className="bg-white p-4 rounded-lg border">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign size={16} className="text-blue-500" />
                <span className="text-sm text-gray-600">Avg Daily</span>
              </div>
              <div className="text-2xl font-bold">${stats.avgDailyPnL.toFixed(0)}</div>
            </div>
            
            <div className="bg-white p-4 rounded-lg border">
              <div className="flex items-center gap-2 mb-2">
                <Fire size={16} className="text-orange-500" />
                <span className="text-sm text-gray-600">Current Streak</span>
              </div>
              <div className="text-2xl font-bold">{stats.currentStreak}</div>
            </div>
            
            <div className="bg-white p-4 rounded-lg border">
              <div className="flex items-center gap-2 mb-2">
                <Percent size={16} className="text-purple-500" />
                <span className="text-sm text-gray-600">Consistency</span>
              </div>
              <div className="text-2xl font-bold">{stats.consistency.toFixed(1)}%</div>
            </div>
          </div>

          {/* Recent Achievements */}
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="text-lg font-semibold mb-4">Recent Achievements</h3>
            <div className="space-y-3">
              {earnedAchievements.slice(0, 3).map(achievement => (
                <div key={achievement.id} className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    {achievement.icon}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-sm">{achievement.title}</div>
                    <div className="text-xs text-gray-600">{achievement.earnedDate}</div>
                  </div>
                  {getRarityBadge(achievement.rarity)}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'stats' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Performance Metrics */}
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="text-lg font-semibold mb-4">Performance</h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Trades</span>
                <span className="font-medium">{stats.totalTrades}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Win Rate</span>
                <span className="font-medium text-green-600">{stats.winRate.toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Profit Factor</span>
                <span className="font-medium">{stats.profitFactor.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Sharpe Ratio</span>
                <span className="font-medium">{stats.sharpeRatio.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Max Drawdown</span>
                <span className="font-medium text-red-600">{stats.maxDrawdown.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          {/* P&L Breakdown */}
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="text-lg font-semibold mb-4">P&L Analysis</h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-600">Total P&L</span>
                <span className={`font-medium ${stats.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ${stats.totalPnL.toFixed(0)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Average Win</span>
                <span className="font-medium text-green-600">${stats.avgWin.toFixed(0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Average Loss</span>
                <span className="font-medium text-red-600">${stats.avgLoss.toFixed(0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Best Trade</span>
                <span className="font-medium text-green-600">${stats.maxWin.toFixed(0)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Worst Trade</span>
                <span className="font-medium text-red-600">${stats.maxLoss.toFixed(0)}</span>
              </div>
            </div>
          </div>

          {/* Streak Analysis */}
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="text-lg font-semibold mb-4">Streaks & Activity</h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-600">Current Streak</span>
                <span className="font-medium">{stats.currentStreak} trades</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Best Streak</span>
                <span className="font-medium text-green-600">{stats.bestStreak} trades</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Trading Days</span>
                <span className="font-medium">{stats.totalTradingDays}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Active Days</span>
                <span className="font-medium">{stats.activeDays}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Avg Daily P&L</span>
                <span className={`font-medium ${stats.avgDailyPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ${stats.avgDailyPnL.toFixed(0)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'achievements' && (
        <div className="space-y-6">
          {/* Achievement Summary */}
          <div className="bg-white p-6 rounded-lg border">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">Achievements</h3>
              <div className="text-sm text-gray-600">
                {earnedAchievements.length} of {totalAchievements} earned
              </div>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(earnedAchievements.length / totalAchievements) * 100}%` }}
              />
            </div>
          </div>

          {/* Achievement Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {ACHIEVEMENTS.map(achievement => (
              <div 
                key={achievement.id}
                className={`p-4 rounded-lg border-2 transition-all ${
                  achievement.earned 
                    ? getRarityColor(achievement.rarity)
                    : 'border-gray-200 bg-gray-50 opacity-60'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm">
                    {achievement.icon}
                  </div>
                  {getRarityBadge(achievement.rarity)}
                </div>
                
                <h4 className="font-semibold mb-1">{achievement.title}</h4>
                <p className="text-sm text-gray-600 mb-3">{achievement.description}</p>
                
                {achievement.earned ? (
                  <div className="text-xs text-green-600 font-medium">
                    Earned on {achievement.earnedDate}
                  </div>
                ) : (
                  <div>
                    {achievement.progress !== undefined && (
                      <div className="mb-2">
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span>Progress</span>
                          <span>{achievement.progress}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1">
                          <div 
                            className="bg-blue-500 h-1 rounded-full"
                            style={{ width: `${achievement.progress}%` }}
                          />
                        </div>
                      </div>
                    )}
                    {achievement.requirement && (
                      <div className="text-xs text-gray-500">
                        {achievement.requirement}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'settings' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Profile Settings */}
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="text-lg font-semibold mb-4">Profile Information</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
                <input
                  type="text"
                  value={profile.displayName}
                  onChange={(e) => setProfile(prev => ({ ...prev, displayName: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Bio</label>
                <textarea
                  value={profile.bio}
                  onChange={(e) => setProfile(prev => ({ ...prev, bio: e.target.value }))}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Trading Experience</label>
                <select
                  value={profile.tradingExperience}
                  onChange={(e) => setProfile(prev => ({ ...prev, tradingExperience: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="< 1 year">Less than 1 year</option>
                  <option value="1-2 years">1-2 years</option>
                  <option value="2-5 years">2-5 years</option>
                  <option value="5+ years">5+ years</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Risk Tolerance</label>
                <select
                  value={profile.riskTolerance}
                  onChange={(e) => setProfile(prev => ({ ...prev, riskTolerance: e.target.value as any }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="conservative">Conservative</option>
                  <option value="moderate">Moderate</option>
                  <option value="aggressive">Aggressive</option>
                </select>
              </div>
            </div>
          </div>

          {/* Customization Settings */}
          <div className="bg-white p-6 rounded-lg border">
            <h3 className="text-lg font-semibold mb-4">Customization</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Theme</label>
                <select
                  value={profile.customization.theme}
                  onChange={(e) => setProfile(prev => ({ 
                    ...prev, 
                    customization: { ...prev.customization, theme: e.target.value as any }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Primary Color</label>
                <input
                  type="color"
                  value={profile.customization.primaryColor}
                  onChange={(e) => setProfile(prev => ({ 
                    ...prev, 
                    customization: { ...prev.customization, primaryColor: e.target.value }
                  }))}
                  className="w-full h-10 border border-gray-300 rounded-lg"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Show Public Stats</span>
                <button
                  onClick={() => setProfile(prev => ({ 
                    ...prev, 
                    customization: { ...prev.customization, showPublicStats: !prev.customization.showPublicStats }
                  }))}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    profile.customization.showPublicStats ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    profile.customization.showPublicStats ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </button>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Public Display Name</label>
                <input
                  type="text"
                  value={profile.customization.publicDisplayName}
                  onChange={(e) => setProfile(prev => ({ 
                    ...prev, 
                    customization: { ...prev.customization, publicDisplayName: e.target.value }
                  }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            
            <button className="w-full mt-6 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2">
              <Save size={16} />
              Save Changes
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;
