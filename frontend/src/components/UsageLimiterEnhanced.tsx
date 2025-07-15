import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, TrendingUp, Info, X } from 'lucide-react';
import { billingServiceEnhanced } from '../services/billingEnhanced';

interface UsageLimiterEnhancedProps {
  metric: 'trades' | 'portfolios' | 'api_calls';
  onLimitReached?: () => void;
  showInlineWarning?: boolean;
  children: (state: {
    canProceed: boolean;
    usage: number;
    limit: number | null;
    percentageUsed: number;
    warning?: string;
    loading: boolean;
  }) => React.ReactNode;
}

export default function UsageLimiterEnhanced({ 
  metric, 
  onLimitReached,
  showInlineWarning = true,
  children 
}: UsageLimiterEnhancedProps) {
  const navigate = useNavigate();
  const [state, setState] = useState({
    canProceed: true,
    usage: 0,
    limit: null as number | null,
    percentageUsed: 0,
    warning: undefined as string | undefined,
    loading: true,
    error: null as string | null,
    showWarningBanner: false
  });

  useEffect(() => {
    checkUsage();
    
    // Set up periodic check for usage
    const interval = setInterval(checkUsage, 60000); // Check every minute
    
    return () => clearInterval(interval);
  }, [metric]);

  const checkUsage = async () => {
    try {
      const result = await billingServiceEnhanced.checkUsageWithWarnings(metric);
      
      setState(prev => ({
        ...prev,
        canProceed: result.allowed,
        usage: result.usage,
        limit: result.limit,
        percentageUsed: result.percentageUsed,
        warning: result.warning,
        loading: false,
        error: null,
        showWarningBanner: !!result.warning && result.critical
      }));
      
      if (!result.allowed && onLimitReached) {
        onLimitReached();
      }

      // Track usage milestones
      if (window.gtag && result.percentageUsed >= 80) {
        window.gtag('event', 'usage_milestone', {
          metric,
          percentage: Math.round(result.percentageUsed),
          plan: 'current'
        });
      }
    } catch (error: any) {
      console.error('Failed to check usage:', error);
      setState(prev => ({
        ...prev,
        loading: false,
        error: 'Unable to verify usage limits',
        canProceed: true // Allow action if we can't verify
      }));
    }
  };

  const handleUpgrade = () => {
    // Track upgrade intent
    if (window.gtag) {
      window.gtag('event', 'upgrade_clicked', {
        trigger: 'usage_limit',
        metric,
        usage_percentage: state.percentageUsed
      });
    }
    
    navigate('/pricing', { 
      state: { 
        reason: `You've reached ${Math.round(state.percentageUsed)}% of your ${metric} limit` 
      } 
    });
  };

  const dismissWarning = () => {
    setState(prev => ({ ...prev, showWarningBanner: false }));
    
    // Remember dismissal for this session
    sessionStorage.setItem(`usage_warning_dismissed_${metric}`, 'true');
  };

  const getProgressBarColor = () => {
    if (state.percentageUsed >= 90) return 'bg-red-500';
    if (state.percentageUsed >= 80) return 'bg-yellow-500';
    return 'bg-blue-500';
  };

  const renderWarningBanner = () => {
    if (!state.showWarningBanner || !state.warning) return null;

    const isAtLimit = state.percentageUsed >= 100;
    const bannerColor = isAtLimit ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200';
    const iconColor = isAtLimit ? 'text-red-500' : 'text-yellow-500';
    const textColor = isAtLimit ? 'text-red-700' : 'text-yellow-700';

    return (
      <div className={`fixed top-20 left-1/2 transform -translate-x-1/2 z-50 max-w-lg w-full mx-4 ${bannerColor} border rounded-lg shadow-lg p-4 animate-slide-down`}>
        <div className="flex items-start">
          <AlertTriangle className={`w-5 h-5 ${iconColor} flex-shrink-0 mt-0.5`} />
          <div className="ml-3 flex-1">
            <p className={`font-medium ${textColor}`}>{state.warning}</p>
            {isAtLimit && (
              <button
                onClick={handleUpgrade}
                className="mt-2 text-sm font-semibold text-blue-600 hover:text-blue-700"
              >
                Upgrade now to continue →
              </button>
            )}
          </div>
          <button
            onClick={dismissWarning}
            className={`ml-3 ${textColor} hover:opacity-70`}
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>
    );
  };

  const renderInlineUsage = () => {
    if (!showInlineWarning || state.limit === null) return null;

    return (
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">
            {metric.charAt(0).toUpperCase() + metric.slice(1)} Usage
          </span>
          <span className="text-sm text-gray-600">
            {state.usage} / {state.limit === null ? 'Unlimited' : state.limit}
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${getProgressBarColor()}`}
            style={{ width: `${Math.min(state.percentageUsed, 100)}%` }}
          />
        </div>
        {state.warning && state.percentageUsed >= 80 && (
          <div className="mt-2 flex items-center text-sm">
            <Info className="w-4 h-4 mr-1 text-yellow-500" />
            <span className="text-yellow-700">{state.warning}</span>
          </div>
        )}
      </div>
    );
  };

  if (state.loading) {
    return (
      <div className="animate-pulse">
        <div className="h-20 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="w-5 h-5 text-yellow-500 mr-2" />
          <span className="text-yellow-700">{state.error}</span>
        </div>
      </div>
    );
  }

  return (
    <>
      {renderWarningBanner()}
      <div>
        {renderInlineUsage()}
        {children({
          canProceed: state.canProceed,
          usage: state.usage,
          limit: state.limit,
          percentageUsed: state.percentageUsed,
          warning: state.warning,
          loading: state.loading
        })}
      </div>
    </>
  );
}

// Usage example component
export function UsageLimiterExample() {
  return (
    <UsageLimiterEnhanced metric="trades">
      {({ canProceed, usage, limit, percentageUsed }) => (
        <div>
          {canProceed ? (
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Add Trade
            </button>
          ) : (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700 font-medium mb-2">
                Trade limit reached ({usage}/{limit})
              </p>
              <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
                Upgrade to Continue
              </button>
            </div>
          )}
        </div>
      )}
    </UsageLimiterEnhanced>
  );
}