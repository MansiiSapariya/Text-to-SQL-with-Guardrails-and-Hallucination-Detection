import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

export default function ConfidenceScore({ confidence }) {
  const [expanded, setExpanded] = useState(false);
  const [animatedScore, setAnimatedScore] = useState(0);

  const { overall, label, grade, breakdown } = confidence;
  const scorePercent = Math.round(overall * 100);

  useEffect(() => {
    // Animate score on mount
    const timer = setTimeout(() => {
      setAnimatedScore(scorePercent);
    }, 100);
    return () => clearTimeout(timer);
  }, [scorePercent]);

  let color = 'var(--accent-success)';
  if (grade === 'medium') color = 'var(--accent-warning)';
  if (grade === 'low') color = 'var(--accent-danger)';

  const circumference = 2 * Math.PI * 28;
  const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

  return (
    <div className="confidence-card">
      <div className="score-header">
        <div className="score-circle">
          <svg className="score-svg" viewBox="0 0 64 64">
            <circle className="score-bg" cx="32" cy="32" r="28" />
            <circle 
              className="score-progress" 
              cx="32" cy="32" r="28" 
              stroke={color}
              strokeDasharray={circumference}
              style={{ strokeDashoffset }}
            />
          </svg>
          <div className="score-text" style={{ color }}>
            {scorePercent}%
          </div>
        </div>
        <div className="score-info">
          <h3>Confidence Score</h3>
          <p>{label}</p>
        </div>
      </div>

      {breakdown && Object.keys(breakdown).length > 0 && (
        <>
          <button className="breakdown-toggle" onClick={() => setExpanded(!expanded)}>
            {expanded ? 'Hide Details' : 'View Breakdown'}
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>

          {expanded && (
            <div className="breakdown-list">
              {Object.entries(breakdown).map(([key, val], idx) => {
                const perc = Math.round(val * 100);
                const formatName = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                return (
                  <div className="breakdown-item" key={key} style={{ animationDelay: `${idx * 0.05}s` }}>
                    <div className="breakdown-label">
                      <span>{formatName}</span>
                      <span>{perc}%</span>
                    </div>
                    <div className="breakdown-bar-bg">
                      <div 
                        className="breakdown-bar-fill" 
                        style={{ width: `${perc}%`, backgroundColor: perc > 80 ? 'var(--accent-success)' : perc > 50 ? 'var(--accent-warning)' : 'var(--accent-danger)' }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
