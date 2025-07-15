import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, TrendingUp } from 'lucide-react';
import { billingService } from '../services/billing';

interface UsageLimiterProps {
  metric: 'trades' | 'portfolios' | 'api_calls';
  onLimitReached?: () => void;
  children: (canProceed: boolean, usage: any) => React.ReactNode;
}

export default function UsageLimiter({ 
  metric, 
  onLimitReached,
  children 
}: UsageLimiterProps) {
  const navigate = useNavigate();
  const [usage, setUsage] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [canProceed, setCanProceed] = useState(true);

  useEffect(() => {
    checkUsage();
  }, [metric]);

  const checkUsage = async () => {
    try {
      const usageData = await billingService.getUsage();
      setUsage(usageData);
      
      let allowed = true;
      if (metric === 'trades') {
        allowed = billingService.canAddMoreTrades(usageData);
      } else if (metric === 'portfolios') {
        allowed = billingService.canAddMorePortfolios(usageData);
      }
      
      setCanProceed(allowed);
      
      if (!allowed && onLimitReached) {
        onLimitReached();
      }
    } catch (error) {
      console.error('Failed to check usage:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="animate-pulse bg-gray-200 rounded h-32"></div>;
  }

  return <>{children(canProceed, usage)}</>;
}

// Usage warning banner component
export function UsageWarningBanner({ usage }: { usage: any }) {
  const navigate = useNavigate();
  
  if (!usage) return null;
  
  const warnings = [];
  
  // Check trades usage
  if (usage.percentage_used.trades >= 80) {
    warnings.push({
      metric: 'trades',
      message: `You've used ${usage.usage.trades} of ${usage.limits.max_trades_per_month} trades this month`,
      percentage: usage.percentage_used.trades
    });
  }
  
  // Check portfolios usage
  if (usage.percentage_used.portfolios >= 80) {
    warnings.push({
      metric: 'portfolios',
      message: `You've created ${usage.usage.portfolios} of ${usage.limits.max_portfolios} portfolios`,
      percentage: usage.percentage_used.portfolios
    });
  }
  
  if (warnings.length === 0) return null;
  
  return (
    <div className="mb-4">
      {warnings.map((warning, idx) => (
        <div key={idx} className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex items-start mb-2">
          <AlertTriangle className="w-5 h-5 text-yellow-600 mr-3 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-yellow-800">
              {warning.message} ({Math.round(warning.percentage)}% of limit)
            </p>
          </div>
          <button
            onClick={() => navigate('/pricing')}
            className="ml-4 text-sm font-medium text-yellow-800 hover:text-yellow-900 flex items-center"
          >
            <TrendingUp className="w-4 h-4 mr-1" />
            Upgrade
          </button>
        </div>
      ))}
    </div>
  );
}

// Hook for checking if user can perform action
export function useCanPerformAction(metric: string): [boolean, () => Promise<void>] {
  const [canPerform, setCanPerform] = useState(true);
  
  const checkAction = async () => {
    try {
      const usage = await billingService.getUsage();
      
      if (metric === 'trades') {
        setCanPerform(billingService.canAddMoreTrades(usage));
      } else if (metric === 'portfolios') {
        setCanPerform(billingService.canAddMorePortfolios(usage));
      }
    } catch (error) {
      console.error('Failed to check action permission:', error);
      setCanPerform(false);
    }
  };
  
  useEffect(() => {
    checkAction();
  }, [metric]);
  
  return [canPerform, checkAction];
}