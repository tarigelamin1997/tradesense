import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ErrorBoundary } from './components/ErrorBoundary';
import AuthWrapper from './components/AuthWrapper';
import LoginPage from './features/auth/pages/LoginPage';
import RegisterPage from './features/auth/pages/RegisterPage';
import DashboardPage from './features/dashboard/pages/DashboardPage';
import UploadPage from './features/upload/pages/UploadPage';
import { useAuthStore } from './store/auth';
import './styles/mobile.css';
import AnalyticsPage from './features/analytics/pages/AnalyticsPage';
import TimelinePage from './features/analytics/pages/TimelinePage';
import EdgeStrengthPage from './features/analytics/pages/EdgeStrengthPage';
import { HeatmapPage } from './features/analytics/pages/HeatmapPage';
import { StreakAnalysisPage } from './features/analytics/pages/StreakAnalysisPage';
import { TradeSearchPage } from './features/analytics/pages/TradeSearchPage';
import MilestonePage from './features/analytics/pages/MilestonePage';
import CrossAccountPage from './features/analytics/pages/CrossAccountPage';
import { MentalMapPage } from './features/analytics/pages/MentalMapPage';
import { PatternExplorerPage } from './features/analytics/pages/PatternExplorerPage';
import { PlaybookManagerPage } from './features/analytics/pages/PlaybookManagerPage';
import { PlaybookAnalyticsPage } from './features/analytics/pages/PlaybookAnalyticsPage';

function App() {
  const { isAuthenticated } = useAuthStore();

  return (
    <ErrorBoundary>
      <Router>
        <div className="App">
          <Routes>
            {/* Public routes */}
            <Route 
              path="/login" 
              element={
                isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
              } 
            />
            <Route 
              path="/register" 
              element={
                isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />
              } 
            />

            {/* Protected routes */}
            <Route
              path="/dashboard"
              element={
                <AuthWrapper fallback={<Navigate to="/login" replace />}>
                  <DashboardPage />
                </AuthWrapper>
              }
            />
            <Route
              path="/upload"
              element={
                <AuthWrapper fallback={<Navigate to="/login" replace />}>
                  <UploadPage />
                </AuthWrapper>
              }
            />
            <Route
              path="/analytics"
              element={
                <AuthWrapper fallback={<Navigate to="/login" replace />}>
                  <AnalyticsPage />
                </AuthWrapper>
              }
            />
          <Route path="/timeline" element={<TimelinePage />} />
          <Route path="/edge-strength" element={<EdgeStrengthPage />} />
            <Route path="/heatmap" element={<HeatmapPage />} />
        <Route path="/analytics/streaks" element={<StreakAnalysisPage />} />
        <Route path="/trade-search" element={<TradeSearchPage />} />
            <Route path="/analytics/milestones" element={<MilestonePage />} />
        <Route path="/cross-account" element={<CrossAccountPage />} />
          <Route path="/mental-map" element={<MentalMapPage />} />
          <Route path="/pattern-explorer" element={<PatternExplorerPage />} />
          <Route path="/playbook-manager" element={<PlaybookManagerPage />} />
          <Route path="/analytics/playbooks" element={<PlaybookAnalyticsPage />} />
        </Routes>
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;