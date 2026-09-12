import React, { useState } from 'react';
import { AlertTriangle, ShieldAlert, X } from 'lucide-react';

export default function GuardrailWarning({ warnings }) {
  const [dismissed, setDismissed] = useState([]);

  if (!warnings || warnings.length === 0) return null;

  const activeWarnings = warnings.filter(w => !dismissed.includes(w.rule_name));
  if (activeWarnings.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {activeWarnings.map((w, i) => {
        const isError = w.severity === 'BLOCK';
        const Icon = isError ? ShieldAlert : AlertTriangle;
        const bannerClass = isError ? 'banner-error' : 'banner-warning';

        return (
          <div key={`${w.rule_name}-${i}`} className={`banner ${bannerClass}`}>
            <Icon className="banner-icon" size={20} />
            <div className="banner-content" style={{ flex: 1 }}>
              <h4>{w.rule_name}</h4>
              <p>{w.message}</p>
            </div>
            <button 
              className="icon-btn" 
              onClick={() => setDismissed([...dismissed, w.rule_name])}
            >
              <X size={16} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
