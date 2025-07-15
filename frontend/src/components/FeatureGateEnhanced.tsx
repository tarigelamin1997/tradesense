import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, TrendingUp, Loader2, AlertCircle, Zap } from 'lucide-react';
import { billingServiceEnhanced } from '../services/billingEnhanced';

interface FeatureGateEnhancedProps {
  feature: 'advanced_analytics' | 'api_access' | 'export' | 'team';
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showUpgradePrompt?: boolean;
  onAccessDenied?: () => void;
  loadingComponent?: React.ReactNode;
}

const featureInfo = {
  advanced_analytics: {
    title: 'Advanced Analytics',
    description: 'Unlock powerful insights with advanced charts, patterns, and AI-driven analysis.',
    icon: TrendingUp
  },
  api_access: {
    title: 'API Access',
    description: 'Integrate TradeSense with your own tools and automate your workflow.',
    icon: Zap
  },
  export: {
    title: 'Export Features',
    description: 'Export your data to Excel, PDF, or CSV for offline analysis.',
    icon: TrendingUp
  },
  team: {
    title: 'Team Collaboration',
    description: 'Share strategies and collaborate with your trading team.',
    icon: TrendingUp
  }
};

export default function FeatureGateEnhanced({ 
  feature, 
  children, 
  fallback,
  showUpgradePrompt = true,
  onAccessDenied,
  loadingComponent
}: FeatureGateEnhancedProps) {
  const navigate = useNavigate();
  const [state, setState] = useState<{
    loading: boolean;
    hasAccess: boolean;
    error: string | null;
    requiredPlan?: string;
    currentPlan?: string;
  }>({
    loading: true,
    hasAccess: false,
    error: null
  });

  useEffect(() => {
    checkAccess();
  }, [feature]);

  const checkAccess = async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const result = await billingServiceEnhanced.checkFeatureAccess(feature);
      const subscription = await billingServiceEnhanced.getSubscription();
      
      setState({
        loading: false,
        hasAccess: result.allowed,
        error: null,
        requiredPlan: result.message?.match(/requires a (\w+) plan/)?.[1],
        currentPlan: subscription.plan
      });

      if (!result.allowed && onAccessDenied) {
        onAccessDenied();
      }
    } catch (error: any) {
      console.error('Failed to check feature access:', error);
      setState({
        loading: false,
        hasAccess: false,
        error: 'Unable to verify feature access. Please try again.',
        currentPlan: 'unknown'
      });
    }
  };

  const handleUpgrade = () => {
    // Track analytics event
    if ('gtag' in window) {
      (window as any).gtag('event', 'upgrade_clicked', {
        feature,
        current_plan: state.currentPlan,
        required_plan: state.requiredPlan
      });
    }
    
    navigate('/pricing', { 
      state: { 
        feature, 
        message: `Upgrade to access ${featureInfo[feature].title}` 
      } 
    });
  };

  const handleRetry = () => {
    checkAccess();
  };

  // Loading state
  if (state.loading) {
    if (loadingComponent) {
      return <>{loadingComponent}</>;
    }
    
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  // Error state
  if (state.error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-red-700 mb-4">{state.error}</p>
        <button
          onClick={handleRetry}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  // Access granted
  if (state.hasAccess) {
    return <>{children}</>;
  }

  // Access denied - show fallback or upgrade prompt
  if (!showUpgradePrompt && fallback) {
    return <>{fallback}</>;
  }

  const info = featureInfo[feature];
  const Icon = info.icon;

  return (
    <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl border border-gray-200 p-8">
      <div className="max-w-md mx-auto text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-200 rounded-full mb-4">
          <Lock className="w-8 h-8 text-gray-500" />
        </div>
        
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          {info.title} is a Premium Feature
        </h3>
        
        <p className="text-gray-600 mb-6">
          {info.description}
        </p>

        {state.currentPlan && state.currentPlan !== 'unknown' && (
          <div className="mb-6 px-4 py-2 bg-gray-100 rounded-lg inline-block">
            <p className="text-sm text-gray-600">
              Your current plan: <span className="font-semibold capitalize">{state.currentPlan}</span>
            </p>
          </div>
        )}

        <div className="space-y-3">
          <button
            onClick={handleUpgrade}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center group"
          >
            <Zap className="w-5 h-5 mr-2 group-hover:animate-pulse" />
            Upgrade to {state.requiredPlan || 'Premium'}
          </button>
          
          <button
            onClick={() => navigate(-1)}
            className="w-full px-6 py-3 text-gray-600 hover:text-gray-900 transition-colors"
          >
            Go Back
          </button>
        </div>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-500 mb-2">
            All premium plans include:
          </p>
          <div className="flex flex-wrap justify-center gap-4 text-xs text-gray-600">
            <span className="flex items-center">
              <Icon className="w-3 h-3 mr-1" /> 14-day free trial
            </span>
            <span className="flex items-center">
              <Icon className="w-3 h-3 mr-1" /> Cancel anytime
            </span>
            <span className="flex items-center">
              <Icon className="w-3 h-3 mr-1" /> No hidden fees
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}