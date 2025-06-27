
import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store';
import ErrorBoundary from './components/ErrorBoundary';
import AuthWrapper from './components/AuthWrapper';
import AppLayout from './components/layout/AppLayout';

// Lazy load pages for better performance
const DashboardPage = React.lazy(() => import('./features/dashboard/pages/DashboardPage'));
const LoginPage = React.lazy(() => import('./features/auth/pages/LoginPage'));
const RegisterPage = React.lazy(() => import('./features/auth/pages/RegisterPage'));
const AnalyticsPage = React.lazy(() => import('./features/analytics/pages/AnalyticsPage'));
const UploadPage = React.lazy(() => import('./features/upload/pages/UploadPage'));

const LoadingSpinner = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
  </div>
);

function App() {
  return (
    <React.StrictMode>
      <Provider store={store}>
        <ErrorBoundary>
          <Router>
            <div className="App">
              <Suspense fallback={<LoadingSpinner />}>
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
                        </Routes>
                      </AppLayout>
                    </AuthWrapper>
                  } />
                </Routes>
              </Suspense>
            </div>
          </Router>
        </ErrorBoundary>
      </Provider>
    </React.StrictMode>
  );
}

export default App;
