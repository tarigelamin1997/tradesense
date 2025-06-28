
import React from 'react';
import Navbar from './components/Navbar';
import Dashboard from './components/Dashboard';
import TradeLog from './components/TradeLog';

function App() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
      <Navbar />
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <Dashboard />
        <TradeLog />
      </div>
    </div>
  );
}

export default App;
