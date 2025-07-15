import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/auth';

// Import components
import AuthWrapper from './components/AuthWrapper';
import ProtectedRoute from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import TradeLog from './components/TradeLog';
import Journal from './components/Journal';
import UploadCenter from './components/UploadCenter';
import ErrorBoundary from './components/ErrorBoundary';

// Import auth pages
import LoginPage from './features/auth/pages/LoginPage';
import RegisterPage from './features/auth/pages/RegisterPage';


// Import analytics pages
import AnalyticsPage from './features/analytics/pages/AnalyticsPage';
import PlaybookManagerPage from './features/analytics/pages/PlaybookManagerPage';
import PatternExplorerPage from './features/analytics/pages/PatternExplorerPage';
import ExecutionQualityPage from './features/analytics/pages/ExecutionQualityPage';
import TradeDetail from './pages/TradeDetail';
import { MobileIntelligencePage } from './pages/MobileIntelligencePage';

// Import billing pages
import Pricing from './pages/Pricing';
import Checkout from './pages/Checkout';
import PaymentSuccess from './pages/PaymentSuccess';
import BillingPortal from './pages/BillingPortal';

function App() {
  const { isAuthenticated, logout } = useAuthStore();

  return (
    <div className="min-h-screen bg-gray-50">
      <AuthWrapper>
        <BrowserRouter>
          <div className="flex flex-col">
            {isAuthenticated && <Navbar onLogout={logout} />}
            <main className="flex-1">
              <Routes>
                <Route path="/login" element={
                  !isAuthenticated ? <LoginPage /> : <Navigate to="/dashboard" replace />
                } />
                <Route path="/register" element={
                  !isAuthenticated ? <RegisterPage /> : <Navigate to="/dashboard" replace />
                } />
                <Route path="/dashboard" element={
                  <ProtectedRoute>
                    <ErrorBoundary>
                      <Dashboard />
                    </ErrorBoundary>
                  </ProtectedRoute>
                } />
                <Route path="/journal" element={
                  <ProtectedRoute>
                    <Journal />
                  </ProtectedRoute>
                } />
                <Route path="/upload" element={
                  <ProtectedRoute>
                    <UploadCenter />
                  </ProtectedRoute>
                } />
                <Route path="/trades" element={
                  <ProtectedRoute>
                    <TradeLog />
                  </ProtectedRoute>
                } />
                <Route path="/trades/:id" element={
                  <ProtectedRoute>
                    <TradeDetail />
                  </ProtectedRoute>
                } />
                <Route path="/analytics" element={
                  <ProtectedRoute>
                    <AnalyticsPage />
                  </ProtectedRoute>
                } />
                <Route path="/analytics/playbooks" element={
                  <ProtectedRoute>
                    <PlaybookManagerPage />
                  </ProtectedRoute>
                } />
                <Route path="/analytics/patterns" element={
                  <ProtectedRoute>
                    <PatternExplorerPage />
                  </ProtectedRoute>
                } />
                <Route path="/analytics/execution" element={
                  <ProtectedRoute>
                    <ExecutionQualityPage />
                  </ProtectedRoute>
                } />
                <Route path="/intelligence" element={
                  <ProtectedRoute>
                    <MobileIntelligencePage />
                  </ProtectedRoute>
                } />
                <Route path="/pricing" element={<Pricing />} />
                <Route path="/checkout" element={
                  <ProtectedRoute>
                    <Checkout />
                  </ProtectedRoute>
                } />
                <Route path="/payment-success" element={
                  <ProtectedRoute>
                    <PaymentSuccess />
                  </ProtectedRoute>
                } />
                <Route path="/billing" element={
                  <ProtectedRoute>
                    <BillingPortal />
                  </ProtectedRoute>
                } />
                <Route path="/" element={
                  !isAuthenticated ? <Navigate to="/login" replace /> : <Navigate to="/dashboard" replace />
                } />
                <Route path="*" element={
                  !isAuthenticated ? <Navigate to="/login" replace /> : <Navigate to="/dashboard" replace />
                } />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </AuthWrapper>
    </div>
  );
}

export default App;
