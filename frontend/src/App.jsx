
import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import TradeLog from './components/TradeLog';
import Journal from './components/Journal';
import UploadCenter from './components/UploadCenter';

function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
        <Navbar />
        
        {/* Navigation Menu */}
        <nav style={{ 
          backgroundColor: '#fff', 
          padding: '10px 20px', 
          borderBottom: '1px solid #e9ecef',
          marginBottom: '20px'
        }}>
          <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', gap: '20px' }}>
            <Link to="/" style={{ 
              textDecoration: 'none', 
              color: '#007bff', 
              padding: '8px 16px',
              borderRadius: '4px',
              backgroundColor: '#f8f9fa'
            }}>
              📊 Dashboard
            </Link>
            <Link to="/journal" style={{ 
              textDecoration: 'none', 
              color: '#007bff', 
              padding: '8px 16px',
              borderRadius: '4px',
              backgroundColor: '#f8f9fa'
            }}>
              📘 Journal
            </Link>
            <Link to="/upload" style={{ 
              textDecoration: 'none', 
              color: '#007bff', 
              padding: '8px 16px',
              borderRadius: '4px',
              backgroundColor: '#f8f9fa'
            }}>
              📤 Upload
            </Link>
            <Link to="/trades" style={{ 
              textDecoration: 'none', 
              color: '#007bff', 
              padding: '8px 16px',
              borderRadius: '4px',
              backgroundColor: '#f8f9fa'
            }}>
              📋 Trade Log
            </Link>
          </div>
        </nav>

        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/journal" element={<Journal />} />
            <Route path="/upload" element={<UploadCenter />} />
            <Route path="/trades" element={<TradeLog />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
