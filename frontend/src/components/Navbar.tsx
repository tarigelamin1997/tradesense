import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/auth';
import { 
  LayoutDashboard, 
  TrendingUp, 
  FileText, 
  Upload, 
  BarChart3, 
  ChevronDown,
  BookOpen,
  Lightbulb,
  Target,
  Activity,
  LogOut,
  Menu,
  X
} from 'lucide-react';

interface NavbarProps {
  onLogout?: () => void;
}

function Navbar({ onLogout }: NavbarProps) {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [showAnalyticsMenu, setShowAnalyticsMenu] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);

  const handleLogout = async () => {
    if (onLogout) {
      await onLogout();
    }
    navigate('/login');
  };

  const isActive = (path: string) => location.pathname === path;
  const isAnalyticsActive = () => location.pathname.startsWith('/analytics');

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/trades', label: 'Trades', icon: TrendingUp },
    { path: '/journal', label: 'Journal', icon: BookOpen },
    { path: '/upload', label: 'Upload', icon: Upload },
  ];

  const analyticsItems = [
    { path: '/analytics', label: 'Overview', icon: BarChart3 },
    { path: '/analytics/patterns', label: 'Pattern Explorer', icon: Lightbulb },
    { path: '/analytics/playbooks', label: 'Playbooks', icon: Target },
    { path: '/analytics/execution', label: 'Execution Quality', icon: Activity },
  ];

  return (
    <nav className="bg-gray-900 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/dashboard" className="flex items-center">
              <span className="text-white text-xl font-bold">🚀 TradeSense</span>
            </Link>
            
            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center ml-10 space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive(item.path)
                        ? 'bg-gray-800 text-white'
                        : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {item.label}
                  </Link>
                );
              })}
              
              {/* Analytics Dropdown */}
              <div className="relative">
                <button
                  onClick={() => setShowAnalyticsMenu(!showAnalyticsMenu)}
                  onBlur={() => setTimeout(() => setShowAnalyticsMenu(false), 200)}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isAnalyticsActive()
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`}
                >
                  <BarChart3 className="w-4 h-4 mr-2" />
                  Analytics
                  <ChevronDown className="w-4 h-4 ml-1" />
                </button>
                
                {showAnalyticsMenu && (
                  <div className="absolute left-0 mt-2 w-56 rounded-md shadow-lg bg-gray-800 ring-1 ring-black ring-opacity-5">
                    <div className="py-1">
                      {analyticsItems.map((item) => {
                        const Icon = item.icon;
                        return (
                          <Link
                            key={item.path}
                            to={item.path}
                            className={`flex items-center px-4 py-2 text-sm transition-colors ${
                              isActive(item.path)
                                ? 'bg-gray-700 text-white'
                                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                            }`}
                          >
                            <Icon className="w-4 h-4 mr-2" />
                            {item.label}
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {user && (
              <div className="hidden md:block text-sm text-gray-300">
                {user.username || user.email || 'User'}
              </div>
            )}
            
            {/* Desktop Logout */}
            <button
              onClick={handleLogout}
              className="hidden md:flex items-center px-3 py-2 rounded-md text-sm font-medium text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </button>
            
            {/* Mobile menu button */}
            <button
              onClick={() => setShowMobileMenu(!showMobileMenu)}
              className="md:hidden text-gray-300 hover:text-white"
            >
              {showMobileMenu ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>
      
      {/* Mobile Navigation */}
      {showMobileMenu && (
        <div className="md:hidden bg-gray-800 border-t border-gray-700">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setShowMobileMenu(false)}
                  className={`flex items-center px-3 py-2 rounded-md text-base font-medium ${
                    isActive(item.path)
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  {item.label}
                </Link>
              );
            })}
            
            <div className="border-t border-gray-700 mt-2 pt-2">
              <div className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Analytics
              </div>
              {analyticsItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setShowMobileMenu(false)}
                    className={`flex items-center px-3 py-2 rounded-md text-base font-medium ${
                      isActive(item.path)
                        ? 'bg-gray-700 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    }`}
                  >
                    <Icon className="w-5 h-5 mr-3" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
            
            <div className="border-t border-gray-700 mt-2 pt-2">
              {user && (
                <div className="px-3 py-2 text-sm text-gray-300">
                  {user.username || user.email || 'User'}
                </div>
              )}
              <button
                onClick={handleLogout}
                className="flex items-center w-full px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
              >
                <LogOut className="w-5 h-5 mr-3" />
                Logout
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}

export default Navbar;