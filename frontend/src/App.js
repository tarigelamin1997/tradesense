
import React, { StrictMode } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { store } from './store';
import { ErrorBoundary } from './components/ErrorBoundary';
import { DevTools, PerformanceMonitor } from './components/DevTools';
import { AppLayout } from './components/layout/AppLayout';
import { AuthWrapper } from './components/AuthWrapper';
import './styles/mobile.css';

// Lazy load pages for better performance
const DashboardPage = React.lazy(() => import('./features/dashboard/pages/DashboardPage'));
const AnalyticsPage = React.lazy(() => import('./features/analytics/pages/AnalyticsPage'));
const UploadPage = React.lazy(() => import('./features/upload/pages/UploadPage'));
const LoginPage = React.lazy(() => import('./features/auth/pages/LoginPage'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
      refetchOnWindowFocus: false
    }
  }
});

function App() {
  return (
    <StrictMode>
      <ErrorBoundary>
        <Provider store={store}>
          <QueryClientProvider client={queryClient}>
            <PerformanceMonitor>
              <Router>
                <AppLayout>
                  <Routes>
                    <Route path="/login" element={
                      <React.Suspense fallback={<div className="flex justify-center items-center h-64">Loading...</div>}>
                        <LoginPage />
                      </React.Suspense>
                    } />
                    <Route path="/" element={<AuthWrapper />}>
                      <Route index element={
                        <React.Suspense fallback={<div className="flex justify-center items-center h-64">Loading...</div>}>
                          <DashboardPage />
                        </React.Suspense>
                      } />
                      <Route path="analytics" element={
                        <React.Suspense fallback={<div className="flex justify-center items-center h-64">Loading...</div>}>
                          <AnalyticsPage />
                        </React.Suspense>
                      } />
                      <Route path="upload" element={
                        <React.Suspense fallback={<div className="flex justify-center items-center h-64">Loading...</div>}>
                          <UploadPage />
                        </React.Suspense>
                      } />
                    </Route>
                  </Routes>
                </AppLayout>
              </Router>
              <DevTools />
            </PerformanceMonitor>
          </QueryClientProvider>
        </Provider>
      </ErrorBoundary>
    </StrictMode>
  );
}

export default App;
