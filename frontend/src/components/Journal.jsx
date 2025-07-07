
import React from 'react';

const Journal = () => {
  return (
    <div style={{ padding: '20px' }}>
      <h2>📘 Trade Journal</h2>
      <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <p>This will list all trade entries pulled from /api/trades.</p>
        <div style={{ marginTop: '15px' }}>
          <h4>Recent Journal Entries:</h4>
          <ul style={{ marginTop: '10px', paddingLeft: '20px' }}>
            <li>Trade #1 - AAPL Long - Need to work on patience</li>
            <li>Trade #2 - TSLA Short - Good entry timing</li>
            <li>Trade #3 - MSFT Long - Should have held longer</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Journal;
