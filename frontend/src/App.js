import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import ErrorBoundary from './components/ErrorBoundary';
import AppLayout from './components/layout/AppLayout';
import AuthWrapper from './components/AuthWrapper';

// Lazy load pages for better performance
const DashboardPage = React.lazy(() => import('./features/dashboard/pages/DashboardPage'));
const AnalyticsPage = React.lazy(() => import('./features/analytics/pages/AnalyticsPage'));
const LoginPage = React.lazy(() => import('./features/auth/pages/LoginPage'));
const RegisterPage = React.lazy(() => import('./features/auth/pages/RegisterPage'));
const UploadPage = React.lazy(() => import('./features/upload/pages/UploadPage'));

// Loading fallback component
const LoadingFallback = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading TradeSense...</p>
    </div>
  </div>
);

function App() {
  return (
    <React.StrictMode>
      <ErrorBoundary>
        <Provider store={store}>
          <Router>
            <div className="App">
              <Suspense fallback={<LoadingFallback />}>
                <Routes>
                  {/* Public routes */}
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/register" element={<RegisterPage />} />

                  {/* Protected routes */}
                  <Route path="/*" element={
                    <AuthWrapper>
                      <AppLayout>
                        <Routes>
                          <Route path="/" element={<DashboardPage />} />
                          <Route path="/dashboard" element={<DashboardPage />} />
                          <Route path="/analytics" element={<AnalyticsPage />} />
                          <Route path="/upload" element={<UploadPage />} />
                        </Routes>
                      </AppLayout>
                    </AuthWrapper>
                  } />
                </Routes>
              </Suspense>
            </div>
          </Router>
        </Provider>
      </ErrorBoundary>
    </React.StrictMode>
  );
}

export default App;