import React from 'react';
import { HelpCircle, ChevronRight } from 'lucide-react';

export default function ClarificationRequest({ clarification, onSelect }) {
  if (!clarification) return null;

  return (
    <div className="clarification-card">
      <div className="clarification-header">
        <HelpCircle size={24} />
        <span>Ambiguous Query Detected</span>
      </div>
      <p style={{ color: 'var(--text-secondary)' }}>{clarification.message}</p>
      
      <div className="clarification-options">
        {clarification.options.map((opt, i) => (
          <button 
            key={i}
            className="clarification-btn"
            onClick={() => onSelect(opt.interpretation)}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
              <span className="clarification-interp">{opt.interpretation}</span>
              <ChevronRight size={18} color="var(--accent-primary)" />
            </div>
            {opt.example_sql && (
              <span className="clarification-sql">e.g. {opt.example_sql}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
