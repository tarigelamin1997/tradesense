import React from 'react';
import { useAuthStore } from '../store/auth';

function Navbar({ onLogout }) {
  const { user } = useAuthStore();

  const handleLogout = async () => {
    if (onLogout) {
      await onLogout();
    }
  };

  return (
    <nav style={{ 
      backgroundColor: '#343a40', 
      padding: '15px 20px', 
      borderBottom: '2px solid #495057' 
    }}>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center' 
      }}>
        <h1 style={{ 
          color: '#fff', 
          margin: 0, 
          fontSize: '24px',
          fontWeight: 'bold'
        }}>
          🚀 TradeSense
        </h1>
        
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
          {/* User info */}
          {user && (
            <div style={{ color: '#fff', fontSize: '14px' }}>
              Welcome, {user.username || user.email || 'User'}
            </div>
          )}
          
          {/* Navigation buttons */}
          <button style={{
            backgroundColor: 'transparent',
            color: '#fff',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}>
            📊 Dashboard
          </button>
          <button style={{
            backgroundColor: 'transparent',
            color: '#fff',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}>
            📈 Analytics
          </button>
          <button style={{
            backgroundColor: 'transparent',
            color: '#fff',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}>
            📋 Trades
          </button>
          
          {/* Logout button */}
          <button 
            onClick={handleLogout}
            style={{
              backgroundColor: '#dc3545',
              color: '#fff',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
              marginLeft: '10px'
            }}
          >
            🚪 Logout
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
