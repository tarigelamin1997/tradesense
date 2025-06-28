
import React from 'react';

function Navbar() {
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
        <div style={{ display: 'flex', gap: '20px' }}>
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
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
