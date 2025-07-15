import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, TrendingUp } from 'lucide-react';
import { billingService } from '../services/billing';

interface FeatureGateProps {
  feature: 'advanced_analytics' | 'api_access' | 'export' | 'team';
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showUpgradePrompt?: boolean;
}

export default function FeatureGate({ 
  feature, 
  children, 
  fallback,
  showUpgradePrompt = true 
}: FeatureGateProps) {
  const navigate = useNavigate();
  const [hasAccess, setHasAccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState<any>(null);

  useEffect(() => {
    checkAccess();
  }, [feature]);

  const checkAccess = async () => {
    try {
      const sub = await billingService.getSubscription();
      setSubscription(sub);
      setHasAccess(billingService.isPremiumFeature(feature, sub));
    } catch (error) {
      console.error('Failed to check feature access:', error);
      setHasAccess(false);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="animate-pulse bg-gray-200 rounded h-32"></div>;
  }

  if (!hasAccess) {
    if (fallback) {
      return <>{fallback}</>;
    }

    if (!showUpgradePrompt) {
      return null;
    }

    const featureNames = {
      advanced_analytics: 'Advanced Analytics',
      api_access: 'API Access',
      export: 'Export Features',
      team: 'Team Features'
    };

    const requiredPlans = {
      advanced_analytics: 'Professional',
      api_access: 'Professional',
      export: 'Professional',
      team: 'Team'
    };

    return (
      <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <Lock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          {featureNames[feature]} Required
        </h3>
        <p className="text-gray-600 mb-4">
          Upgrade to {requiredPlans[feature]} plan to unlock this feature
        </p>
        <div className="flex justify-center space-x-3">
          <button
            onClick={() => navigate('/pricing')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center"
          >
            <TrendingUp className="w-4 h-4 mr-2" />
            View Plans
          </button>
          <button
            onClick={() => navigate('/billing')}
            className="px-4 py-2 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors"
          >
            Current Plan: {billingService.formatPlanName(subscription?.plan || 'free')}
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

// Hook for checking feature access
export function useFeatureAccess(feature: string): boolean {
  const [hasAccess, setHasAccess] = useState(false);

  useEffect(() => {
    billingService.getSubscription()
      .then(sub => {
        setHasAccess(billingService.isPremiumFeature(feature, sub));
      })
      .catch(() => {
        setHasAccess(false);
      });
  }, [feature]);

  return hasAccess;
}