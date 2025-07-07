
import React from 'react';

const UploadCenter = () => {
  return (
    <div style={{ padding: '20px' }}>
      <h2>📤 Upload Center</h2>
      <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '2px dashed #dee2e6' }}>
        <p>File uploads will go here and be sent to /api/upload.</p>
        <div style={{ marginTop: '15px' }}>
          <button style={{
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '14px'
          }}>
            Choose File
          </button>
          <p style={{ marginTop: '10px', color: '#6c757d', fontSize: '14px' }}>
            Supported formats: CSV, Excel, JSON
          </p>
        </div>
      </div>
    </div>
  );
};

export default UploadCenter;
