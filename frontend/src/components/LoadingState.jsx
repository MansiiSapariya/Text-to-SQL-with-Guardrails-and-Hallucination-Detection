import React, { useState, useEffect } from 'react';

const STEPS = [
  "Parsing natural language...",
  "Generating SQL...",
  "Validating syntax...",
  "Executing query...",
  "Analyzing results..."
];

export default function LoadingState() {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setStepIndex((prev) => Math.min(prev + 1, STEPS.length - 1));
    }, 800);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="loading-state">
      <div className="skeleton skeleton-header"></div>
      <div className="skeleton skeleton-row"></div>
      <div className="skeleton skeleton-row"></div>
      <div className="skeleton skeleton-row"></div>
      <div className="skeleton skeleton-row"></div>
      
      <div className="loading-steps">
        <div className="spinner"></div>
        <div className="step-text">{STEPS[stepIndex]}</div>
      </div>
    </div>
  );
}
