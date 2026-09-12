import React from 'react';
import { Clock, Trash2, MessageSquare } from 'lucide-react';

function formatTime(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  const now = new Date();
  const diff = now - date;
  
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff/60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff/3600000)}h ago`;
  return date.toLocaleDateString();
}

export default function HistorySidebar({ history, currentQueryId, onSelect, onClear }) {
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">Query History</div>
        {history.length > 0 && (
          <button className="clear-btn" onClick={() => {
            if(window.confirm('Clear all history?')) onClear();
          }}>
            Clear
          </button>
        )}
      </div>
      <div className="history-list">
        {history.length === 0 ? (
          <div className="empty-state" style={{ padding: '24px 12px' }}>
            <MessageSquare className="empty-icon" style={{ width: 32, height: 32, marginBottom: 8 }} />
            <p style={{ fontSize: '0.8125rem' }}>No past queries yet.</p>
          </div>
        ) : (
          history.map((item) => {
            const isCurrent = item.query_id === currentQueryId;
            const grade = item.confidence?.grade || 'low';
            
            return (
              <button 
                key={item.query_id}
                className={`history-item ${isCurrent ? 'active' : ''}`}
                onClick={() => onSelect(item)}
              >
                <div className="history-question">{item.question}</div>
                <div className="history-meta">
                  <div className={`badge badge-${grade}`}>
                    {grade === 'high' ? '🟢' : grade === 'medium' ? '🟡' : '🔴'} {Math.round(item.confidence?.overall * 100 || 0)}%
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={12} />
                    {formatTime(item.timestamp)}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
