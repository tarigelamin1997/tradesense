import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  CreditCard, TrendingUp, Users, Calendar, Download, 
  AlertCircle, ChevronRight, Loader2, ExternalLink 
} from 'lucide-react';
import { billingService } from '../services/billing';
import { useAuth } from '../hooks/useAuth';

export default function BillingPortal() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState<any>(null);
  const [usage, setUsage] = useState<any>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/auth/login');
      return;
    }
    
    loadBillingData();
  }, [user, navigate]);

  const loadBillingData = async () => {
    try {
      setLoading(true);
      const [sub, usg, inv] = await Promise.all([
        billingService.getSubscription(),
        billingService.getUsage(),
        billingService.getInvoices(5)
      ]);
      
      setSubscription(sub);
      setUsage(usg);
      setInvoices(inv);
    } catch (err: any) {
      setError(err.message || 'Failed to load billing information');
    } finally {
      setLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    try {
      const { portal_url } = await billingService.createPortalSession(window.location.href);
      window.location.href = portal_url;
    } catch (err: any) {
      setError(err.message || 'Failed to open billing portal');
    }
  };

  const handleUpgrade = () => {
    navigate('/pricing');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const isFreePlan = subscription?.plan === 'free';
  const nextBillDate = subscription?.current_period_end 
    ? new Date(subscription.current_period_end).toLocaleDateString()
    : null;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Billing & Subscription</h1>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-start">
          <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Current Plan */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Current Plan</h2>
          {!isFreePlan && (
            <button
              onClick={handleManageSubscription}
              className="text-blue-600 hover:text-blue-700 font-medium flex items-center"
            >
              Manage Subscription
              <ExternalLink className="w-4 h-4 ml-1" />
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-600 mb-1">Plan</p>
            <p className="text-2xl font-bold text-gray-900">
              {billingService.formatPlanName(subscription?.plan || 'free')}
            </p>
            {subscription?.status === 'trialing' && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mt-2">
                Trial ends {new Date(subscription.trial_end).toLocaleDateString()}
              </span>
            )}
          </div>

          <div>
            <p className="text-sm text-gray-600 mb-1">Billing Cycle</p>
            <p className="text-lg font-medium text-gray-900">
              {billingService.formatBillingCycle(subscription?.billing_cycle || 'none')}
            </p>
            {nextBillDate && !subscription?.cancel_at_period_end && (
              <p className="text-sm text-gray-500">Next bill: {nextBillDate}</p>
            )}
          </div>

          <div>
            <p className="text-sm text-gray-600 mb-1">Status</p>
            <div className="flex items-center">
              <div className={`w-2 h-2 rounded-full mr-2 ${
                subscription?.status === 'active' || subscription?.status === 'trialing' 
                  ? 'bg-green-500' 
                  : 'bg-red-500'
              }`} />
              <p className="text-lg font-medium text-gray-900 capitalize">
                {subscription?.status || 'Free'}
              </p>
            </div>
            {subscription?.cancel_at_period_end && (
              <p className="text-sm text-red-600 mt-1">
                Cancels on {nextBillDate}
              </p>
            )}
          </div>
        </div>

        {isFreePlan && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-900 mb-3">
              Upgrade to unlock advanced features and unlimited trades
            </p>
            <button
              onClick={handleUpgrade}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Upgrade Now
            </button>
          </div>
        )}
      </div>

      {/* Usage Statistics */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Current Usage</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Trades Usage */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <TrendingUp className="w-5 h-5 text-gray-400 mr-2" />
                <span className="text-sm font-medium text-gray-700">Trades</span>
              </div>
              <span className="text-sm text-gray-500">
                {usage?.usage.trades || 0} / {usage?.limits.max_trades_per_month || '∞'}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${Math.min(usage?.percentage_used.trades || 0, 100)}%` }}
              />
            </div>
          </div>

          {/* Portfolios Usage */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <Users className="w-5 h-5 text-gray-400 mr-2" />
                <span className="text-sm font-medium text-gray-700">Portfolios</span>
              </div>
              <span className="text-sm text-gray-500">
                {usage?.usage.portfolios || 0} / {usage?.limits.max_portfolios || '∞'}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${Math.min(usage?.percentage_used.portfolios || 0, 100)}%` }}
              />
            </div>
          </div>

          {/* API Calls Usage */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <CreditCard className="w-5 h-5 text-gray-400 mr-2" />
                <span className="text-sm font-medium text-gray-700">API Calls</span>
              </div>
              <span className="text-sm text-gray-500">
                {usage?.usage.api_calls || 0} / {usage?.limits.max_api_calls_per_day || '0'}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${Math.min(usage?.percentage_used.api_calls || 0, 100)}%` }}
              />
            </div>
          </div>

          {/* Team Members Usage */}
          {usage?.limits.has_team_features && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <Users className="w-5 h-5 text-gray-400 mr-2" />
                  <span className="text-sm font-medium text-gray-700">Team Members</span>
                </div>
                <span className="text-sm text-gray-500">
                  {usage?.usage.team_members || 1} / {usage?.limits.max_team_members || 1}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${Math.min(usage?.percentage_used.team_members || 0, 100)}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Feature Access */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Feature Access</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { name: 'Advanced Analytics', key: 'has_advanced_analytics' },
            { name: 'API Access', key: 'has_api_access' },
            { name: 'Export Features', key: 'has_export_features' },
            { name: 'Team Features', key: 'has_team_features' },
            { name: 'Priority Support', key: 'has_priority_support' },
            { name: 'White Label Options', key: 'has_white_label' },
          ].map((feature) => (
            <div key={feature.key} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
              <span className="font-medium text-gray-700">{feature.name}</span>
              {usage?.limits[feature.key] ? (
                <span className="text-green-600 font-medium">✓ Enabled</span>
              ) : (
                <span className="text-gray-400">Upgrade required</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recent Invoices */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Recent Invoices</h2>
          {invoices.length > 0 && (
            <button className="text-blue-600 hover:text-blue-700 font-medium">
              View All
            </button>
          )}
        </div>
        
        {invoices.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No invoices yet</p>
        ) : (
          <div className="space-y-3">
            {invoices.map((invoice) => (
              <div key={invoice.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                <div className="flex items-center">
                  <Calendar className="w-5 h-5 text-gray-400 mr-3" />
                  <div>
                    <p className="font-medium text-gray-900">{invoice.period}</p>
                    <p className="text-sm text-gray-500">
                      {invoice.status === 'paid' ? 'Paid' : invoice.status}
                      {invoice.paid_at && ` on ${new Date(invoice.paid_at).toLocaleDateString()}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center">
                  <span className="font-medium text-gray-900 mr-4">
                    ${invoice.amount.toFixed(2)}
                  </span>
                  {invoice.invoice_pdf && (
                    <a
                      href={invoice.invoice_pdf}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-700"
                    >
                      <Download className="w-5 h-5" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}