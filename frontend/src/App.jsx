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

// Import auth pages
import LoginPage from './features/auth/pages/LoginPage';
import RegisterPage from './features/auth/pages/RegisterPage';

function App() {
  const { isAuthenticated, logout } = useAuthStore();

  return (
    <div className="min-h-screen bg-gray-50">
      <AuthWrapper>
        <BrowserRouter>
          <div className="flex">
            {isAuthenticated && <Navbar onLogout={logout} />}
            <main className={`flex-1 ${isAuthenticated ? 'ml-64' : ''}`}>
              <Routes>
                <Route path="/login" element={
                  !isAuthenticated ? <LoginPage /> : <Navigate to="/dashboard" replace />
                } />
                <Route path="/register" element={
                  !isAuthenticated ? <RegisterPage /> : <Navigate to="/dashboard" replace />
                } />
                <Route path="/dashboard" element={
                  <ProtectedRoute>
                    <Dashboard />
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
