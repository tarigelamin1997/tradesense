
import React from 'react';

function TradeLog() {
  const sampleTrades = [
    { id: 1, symbol: 'AAPL', type: 'Long', pnl: '+$450', time: '2 hours ago', status: 'Closed' },
    { id: 2, symbol: 'TSLA', type: 'Short', pnl: '-$120', time: '4 hours ago', status: 'Closed' },
    { id: 3, symbol: 'MSFT', type: 'Long', pnl: '+$280', time: '6 hours ago', status: 'Closed' }
  ];

  return (
    <div style={{ padding: '20px' }}>
      <h2>📋 Recent Trades</h2>
      <div style={{ marginTop: '20px' }}>
        <table style={{ 
          width: '100%', 
          borderCollapse: 'collapse',
          backgroundColor: '#fff',
          border: '1px solid #e9ecef',
          borderRadius: '8px',
          overflow: 'hidden'
        }}>
          <thead>
            <tr style={{ backgroundColor: '#f8f9fa' }}>
              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e9ecef' }}>Symbol</th>
              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e9ecef' }}>Type</th>
              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e9ecef' }}>P&L</th>
              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e9ecef' }}>Time</th>
              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #e9ecef' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {sampleTrades.map((trade) => (
              <tr key={trade.id}>
                <td style={{ padding: '12px', borderBottom: '1px solid #e9ecef' }}>{trade.symbol}</td>
                <td style={{ padding: '12px', borderBottom: '1px solid #e9ecef' }}>{trade.type}</td>
                <td style={{ 
                  padding: '12px', 
                  borderBottom: '1px solid #e9ecef',
                  color: trade.pnl.startsWith('+') ? '#28a745' : '#dc3545',
                  fontWeight: 'bold'
                }}>
                  {trade.pnl}
                </td>
                <td style={{ padding: '12px', borderBottom: '1px solid #e9ecef' }}>{trade.time}</td>
                <td style={{ padding: '12px', borderBottom: '1px solid #e9ecef' }}>{trade.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TradeLog;
