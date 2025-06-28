
import React, { useState, useEffect } from 'react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';

interface TraderProfile {
  id: string;
  username: string;
  email: string;
  tradingExperience: string;
  riskTolerance: string;
  preferredStrategies: string[];
  timezone: string;
  notifications: {
    email: boolean;
    push: boolean;
    tradingAlerts: boolean;
  };
  tradingGoals: string;
  accountBalance: number;
  totalTrades: number;
  winRate: number;
  avgReturn: number;
}

export const ProfilePage: React.FC = () => {
  const [profile, setProfile] = useState<TraderProfile | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch user profile
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      // Mock data for now
      setProfile({
        id: '1',
        username: 'TraderPro',
        email: 'trader@example.com',
        tradingExperience: 'Intermediate',
        riskTolerance: 'Moderate',
        preferredStrategies: ['Swing Trading', 'Momentum'],
        timezone: 'EST',
        notifications: {
          email: true,
          push: true,
          tradingAlerts: true
        },
        tradingGoals: 'Consistent monthly returns of 5-8%',
        accountBalance: 50000,
        totalTrades: 245,
        winRate: 67.3,
        avgReturn: 2.4
      });
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      // Save profile changes
      setIsEditing(false);
    } catch (error) {
      console.error('Error saving profile:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Trader Profile</h1>
          <p className="text-gray-600 mt-2">Manage your trading preferences and account settings</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Profile Overview */}
          <div className="lg:col-span-1">
            <Card className="p-6">
              <div className="flex flex-col items-center">
                <div className="w-24 h-24 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mb-4">
                  {profile.username.charAt(0).toUpperCase()}
                </div>
                <h2 className="text-xl font-semibold text-gray-900">{profile.username}</h2>
                <p className="text-gray-600">{profile.email}</p>
                
                <div className="mt-6 w-full space-y-4">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Experience</span>
                    <span className="font-medium">{profile.tradingExperience}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Risk Tolerance</span>
                    <span className="font-medium">{profile.riskTolerance}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Trades</span>
                    <span className="font-medium">{profile.totalTrades}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Win Rate</span>
                    <span className="font-medium text-green-600">{profile.winRate}%</span>
                  </div>
                </div>
              </div>
            </Card>

            {/* Quick Stats */}
            <Card className="p-6 mt-6">
              <h3 className="text-lg font-semibold mb-4">Performance Overview</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Account Balance</span>
                    <span className="font-medium">${profile.accountBalance.toLocaleString()}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                    <div className="bg-blue-600 h-2 rounded-full" style={{ width: '75%' }}></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between text-sm">
                    <span>Avg Return</span>
                    <span className="font-medium text-green-600">+{profile.avgReturn}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                    <div className="bg-green-600 h-2 rounded-full" style={{ width: `${Math.min(profile.avgReturn * 10, 100)}%` }}></div>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Profile Settings */}
          <div className="lg:col-span-2">
            <Card className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold">Profile Settings</h3>
                <Button
                  onClick={() => isEditing ? handleSave() : setIsEditing(true)}
                  variant={isEditing ? "primary" : "secondary"}
                >
                  {isEditing ? 'Save Changes' : 'Edit Profile'}
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Username
                  </label>
                  <Input
                    value={profile.username}
                    disabled={!isEditing}
                    onChange={(e) => setProfile(prev => prev ? {...prev, username: e.target.value} : null)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <Input
                    type="email"
                    value={profile.email}
                    disabled={!isEditing}
                    onChange={(e) => setProfile(prev => prev ? {...prev, email: e.target.value} : null)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Trading Experience
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={profile.tradingExperience}
                    disabled={!isEditing}
                    onChange={(e) => setProfile(prev => prev ? {...prev, tradingExperience: e.target.value} : null)}
                  >
                    <option value="Beginner">Beginner (0-1 years)</option>
                    <option value="Intermediate">Intermediate (1-5 years)</option>
                    <option value="Advanced">Advanced (5+ years)</option>
                    <option value="Professional">Professional Trader</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Risk Tolerance
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={profile.riskTolerance}
                    disabled={!isEditing}
                    onChange={(e) => setProfile(prev => prev ? {...prev, riskTolerance: e.target.value} : null)}
                  >
                    <option value="Conservative">Conservative</option>
                    <option value="Moderate">Moderate</option>
                    <option value="Aggressive">Aggressive</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Timezone
                  </label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={profile.timezone}
                    disabled={!isEditing}
                    onChange={(e) => setProfile(prev => prev ? {...prev, timezone: e.target.value} : null)}
                  >
                    <option value="EST">Eastern Time (EST)</option>
                    <option value="CST">Central Time (CST)</option>
                    <option value="MST">Mountain Time (MST)</option>
                    <option value="PST">Pacific Time (PST)</option>
                    <option value="UTC">UTC</option>
                  </select>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Trading Goals
                  </label>
                  <textarea
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    value={profile.tradingGoals}
                    disabled={!isEditing}
                    onChange={(e) => setProfile(prev => prev ? {...prev, tradingGoals: e.target.value} : null)}
                    placeholder="Describe your trading goals and objectives..."
                  />
                </div>
              </div>
            </Card>

            {/* Notification Settings */}
            <Card className="p-6 mt-6">
              <h3 className="text-lg font-semibold mb-4">Notification Preferences</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Email Notifications</p>
                    <p className="text-sm text-gray-600">Receive updates via email</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={profile.notifications.email}
                      disabled={!isEditing}
                      onChange={(e) => setProfile(prev => prev ? {
                        ...prev,
                        notifications: { ...prev.notifications, email: e.target.checked }
                      } : null)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Trading Alerts</p>
                    <p className="text-sm text-gray-600">Get notified about trading opportunities</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={profile.notifications.tradingAlerts}
                      disabled={!isEditing}
                      onChange={(e) => setProfile(prev => prev ? {
                        ...prev,
                        notifications: { ...prev.notifications, tradingAlerts: e.target.checked }
                      } : null)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
