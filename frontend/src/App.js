
import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthWrapper } from './components/AuthWrapper.tsx';
import { ErrorBoundary } from './components/ErrorBoundary.tsx';
import { AppLayout } from './components/layout/AppLayout.tsx';

// Lazy load pages
const DashboardPage = React.lazy(() => import('./features/dashboard/pages/DashboardPage.tsx'));
const LoginPage = React.lazy(() => import('./features/auth/pages/LoginPage.tsx'));
const RegisterPage = React.lazy(() => import('./features/auth/pages/RegisterPage.tsx'));
const UploadPage = React.lazy(() => import('./features/upload/pages/UploadPage.tsx'));
const AnalyticsPage = React.lazy(() => import('./features/analytics/pages/AnalyticsPage.tsx'));
const HeatmapPage = React.lazy(() => import('./features/analytics/pages/HeatmapPage.tsx'));
const StreakAnalysisPage = React.lazy(() => import('./features/analytics/pages/StreakAnalysisPage.tsx'));
const EdgeStrengthPage = React.lazy(() => import('./features/analytics/pages/EdgeStrengthPage.tsx'));
const PlaybookAnalyticsPage = React.lazy(() => import('./features/analytics/pages/PlaybookAnalyticsPage.tsx'));
const PlaybookComparisonPage = React.lazy(() => import('./features/analytics/pages/PlaybookComparisonPage.tsx'));
const PlaybookManagerPage = React.lazy(() => import('./features/analytics/pages/PlaybookManagerPage.tsx'));
const StrategyLabPage = React.lazy(() => import('./features/analytics/pages/StrategyLabPage.tsx'));
const PortfolioSimulatorPage = React.lazy(() => import('./features/portfolio/pages/PortfolioSimulatorPage.tsx'));
const ConfidenceCalibrationPage = React.lazy(() => import('./features/analytics/pages/ConfidenceCalibrationPage.tsx'));
const ExecutionQualityPage = React.lazy(() => import('./features/analytics/pages/ExecutionQualityPage.tsx'));
const TradeSearchPage = React.lazy(() => import('./features/analytics/pages/TradeSearchPage.tsx'));
const MentalMapPage = React.lazy(() => import('./features/analytics/pages/MentalMapPage.tsx'));
const MilestonePage = React.lazy(() => import('./features/analytics/pages/MilestonePage.tsx'));
const ReviewAnalyticsPage = React.lazy(() => import('./features/analytics/pages/ReviewAnalyticsPage.tsx'));
const PatternExplorerPage = React.lazy(() => import('./features/analytics/pages/PatternExplorerPage.tsx'));
const TimelinePage = React.lazy(() => import('./features/analytics/pages/TimelinePage.tsx'));
const CrossAccountPage = React.lazy(() => import('./features/analytics/pages/CrossAccountPage.tsx'));

const queryClient = new QueryClient();

const LoadingFallback = () => (
  <div className="flex items-center justify-center h-64">
    <div className="text-lg">Loading...</div>
  </div>
);

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <Router>
          <div className="App">
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={
                <Suspense fallback={<LoadingFallback />}>
                  <LoginPage />
                </Suspense>
              } />
              <Route path="/register" element={
                <Suspense fallback={<LoadingFallback />}>
                  <RegisterPage />
                </Suspense>
              } />
              
              {/* Protected routes */}
              <Route path="/*" element={
                <AuthWrapper>
                  <AppLayout>
                    <Suspense fallback={<LoadingFallback />}>
                      <Routes>
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<DashboardPage />} />
                        <Route path="/upload" element={<UploadPage />} />
                        <Route path="/analytics" element={<AnalyticsPage />} />
                        <Route path="/analytics/heatmap" element={<HeatmapPage />} />
                        <Route path="/analytics/streaks" element={<StreakAnalysisPage />} />
                        <Route path="/analytics/edge-strength" element={<EdgeStrengthPage />} />
                        <Route path="/analytics/playbook-analytics" element={<PlaybookAnalyticsPage />} />
                        <Route path="/analytics/playbook-comparison" element={<PlaybookComparisonPage />} />
                        <Route path="/analytics/playbook-manager" element={<PlaybookManagerPage />} />
                        <Route path="/analytics/strategy-lab" element={<StrategyLabPage />} />
                        <Route path="/analytics/confidence-calibration" element={<ConfidenceCalibrationPage />} />
                        <Route path="/analytics/execution-quality" element={<ExecutionQualityPage />} />
                        <Route path="/analytics/trade-search" element={<TradeSearchPage />} />
                        <Route path="/analytics/mental-map" element={<MentalMapPage />} />
                        <Route path="/analytics/milestones" element={<MilestonePage />} />
                        <Route path="/analytics/reviews" element={<ReviewAnalyticsPage />} />
                        <Route path="/analytics/patterns" element={<PatternExplorerPage />} />
                        <Route path="/analytics/timeline" element={<TimelinePage />} />
                        <Route path="/analytics/cross-account" element={<CrossAccountPage />} />
                        <Route path="/portfolio" element={<PortfolioSimulatorPage />} />
                        <Route path="*" element={<Navigate to="/dashboard" replace />} />
                      </Routes>
                    </Suspense>
                  </AppLayout>
                </AuthWrapper>
              } />
            </Routes>
          </div>
        </Router>
      </ErrorBoundary>
    </QueryClientProvider>
  );
}

export default App;
