import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import { AuthWrapper } from './components/AuthWrapper';
import { ErrorBoundary } from './components/ErrorBoundary';
import { DevToolsToggle } from './components/DevTools';
import { performanceMonitor } from './utils/performance';
import PerformanceMonitor from './components/PerformanceMonitor';

// Lazy load pages for better performance
const DashboardPage = React.lazy(() => import('./features/dashboard/pages/DashboardPage'));
const LoginPage = React.lazy(() => import('./features/auth/pages/LoginPage'));
const RegisterPage = React.lazy(() => import('./features/auth/pages/RegisterPage'));
const AnalyticsPage = React.lazy(() => import('./features/analytics/pages/AnalyticsPage'));
const UploadPage = React.lazy(() => import('./features/upload/pages/UploadPage'));
const FeatureVotingPage = React.lazy(() => import('./features/voting/pages/FeatureVotingPage'));
const PortfolioSimulatorPage = React.lazy(() => import('./features/portfolio/pages/PortfolioSimulatorPage'));

function App() {
  // Initialize performance monitoring
  React.useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('🚀 TradeSense Performance Monitoring Active');
    }
  }, []);

  return (
    <React.StrictMode>
      <ErrorBoundary>
        <Provider store={store}>
          <Router>
            <React.Suspense fallback={<div className="flex items-center justify-center min-h-screen">
              <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
            </div>}>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/*" element={
                  <AuthWrapper>
                    <AppLayout>
                      <Routes>
                        <Route path="/" element={<DashboardPage />} />
                        <Route path="/dashboard" element={<DashboardPage />} />
                        <Route path="/analytics" element={<AnalyticsPage />} />
                        <Route path="/upload" element={<UploadPage />} />
                        <Route path="/features" element={<FeatureVotingPage />} />
                        <Route path="/portfolio" element={<PortfolioSimulatorPage />} />
                      </Routes>
                    </AppLayout>
                  </AuthWrapper>
                } />
              </Routes>
            </React.Suspense>
            <DevToolsToggle />
          </Router>
          <PerformanceMonitor />
      </ErrorBoundary>
    </React.StrictMode>
  );
}

export default App;