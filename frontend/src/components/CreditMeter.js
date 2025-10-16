import React from 'react';
import { DollarSign } from 'lucide-react';

const CreditMeter = ({ cost }) => {
  return (
    <div
      data-testid="credit-meter"
      className="glass"
      style={{
        padding: '16px 24px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}
    >
      <div
        style={{
          width: '40px',
          height: '40px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'rgba(72, 187, 120, 0.2)',
          borderRadius: '50%',
        }}
      >
        <DollarSign size={20} style={{ color: '#68d391' }} />
      </div>
      <div>
        <div style={{ fontSize: '12px', color: '#a0aec0', marginBottom: '2px' }}>Task Cost</div>
        <div style={{ fontSize: '20px', fontWeight: '700', color: '#68d391' }}>${cost.toFixed(2)}</div>
      </div>
    </div>
  );
};

export default CreditMeter;