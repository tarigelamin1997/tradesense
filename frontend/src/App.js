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
import { TimelinePage } from './features/analytics/pages/TimelinePage';

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
          <Route path="/calendar" element={<TimelinePage />} />

            {/* Default redirect */}
            <Route 
              path="/" 
              element={
                <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />
              } 
            />

            {/* Catch all */}
            <Route 
              path="*" 
              element={
                <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />
              } 
            />
          </Routes>
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;