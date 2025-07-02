
import React from 'react';

function Dashboard() {
  return (
    <div style={{ padding: '20px' }}>
      <h2>📊 TradeSense Dashboard</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginTop: '20px' }}>
        <div style={{ padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '1px solid #e9ecef' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#495057' }}>Total P&L</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745', margin: 0 }}>$12,450</p>
        </div>
        <div style={{ padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '1px solid #e9ecef' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#495057' }}>Win Rate</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#007bff', margin: 0 }}>68.5%</p>
        </div>
        <div style={{ padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '1px solid #e9ecef' }}>
          <h3 style={{ margin: '0 0 10px 0', color: '#495057' }}>Total Trades</h3>
          <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#6c757d', margin: 0 }}>147</p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
