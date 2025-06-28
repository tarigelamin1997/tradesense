
import React, { StrictMode, Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AppLayout } from './components/layout/AppLayout';
import './styles/mobile.css';

// Lazy load pages for better performance
const DashboardPage = lazy(() => import('./features/dashboard/pages/DashboardPage'));
const AnalyticsPage = lazy(() => import('./features/analytics/pages/AnalyticsPage'));
const UploadPage = lazy(() => import('./features/upload/pages/UploadPage'));
const LoginPage = lazy(() => import('./features/auth/pages/LoginPage'));
const ProfilePage = lazy(() => import('./features/auth/pages/ProfilePage'));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 2,
      refetchOnWindowFocus: false
    }
  }
});

// Loading component
const LoadingSpinner = () => (
  <div className="flex justify-center items-center h-64">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
    <span className="ml-3 text-gray-600">Loading...</span>
  </div>
);

function App() {
  return (
    <StrictMode>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <Router>
            <AppLayout>
              <Suspense fallback={<LoadingSpinner />}>
                <Routes>
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="/" element={<DashboardPage />} />
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/analytics" element={<AnalyticsPage />} />
                  <Route path="/upload" element={<UploadPage />} />
                  <Route path="*" element={
                    <div className="flex justify-center items-center h-64">
                      <div className="text-center">
                        <h2 className="text-2xl font-bold text-gray-800 mb-4">Page Not Found</h2>
                        <p className="text-gray-600">The page you're looking for doesn't exist.</p>
                      </div>
                    </div>
                  } />
                </Routes>
              </Suspense>
            </AppLayout>
          </Router>
          {process.env.NODE_ENV === 'development' && <ReactQueryDevtools />}
        </QueryClientProvider>
      </ErrorBoundary>
    </StrictMode>
  );
}

export default App;
