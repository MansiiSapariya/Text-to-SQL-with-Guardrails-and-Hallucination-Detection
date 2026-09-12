import React, { useState, useRef, useEffect } from 'react';
import { Send, CornerDownLeft } from 'lucide-react';

export default function QueryInput({ onSubmit, isLoading, sampleQueries }) {
  const [query, setQuery] = useState('');
  const textareaRef = useRef(null);

  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      if (query.trim() && !isLoading) {
        onSubmit(query.trim());
      }
    }
  };

  const handleInput = (e) => {
    setQuery(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = '56px';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = Math.min(scrollHeight, 120) + 'px';
    }
  };

  const handleSubmit = () => {
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  return (
    <div className="query-section">
      {sampleQueries && sampleQueries.length > 0 && (
        <div className="chips-container">
          {sampleQueries.map((q, i) => (
            <button 
              key={i} 
              className="chip"
              onClick={() => {
                setQuery(q);
                onSubmit(q);
              }}
              disabled={isLoading}
            >
              {q}
            </button>
          ))}
        </div>
      )}
      
      <div className="input-container">
        <textarea
          ref={textareaRef}
          className="query-textarea"
          placeholder="Ask anything about your music store data..."
          value={query}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />
        <div className="input-footer">
          <div className="shortcut-hint">
            <span className="kbd">Cmd</span> / <span className="kbd">Ctrl</span> + <span className="kbd">Enter</span> to submit
          </div>
          <button 
            className="submit-btn" 
            onClick={handleSubmit}
            disabled={!query.trim() || isLoading}
          >
            {isLoading ? 'Processing...' : (
              <>
                <span>Run Query</span>
                <Send size={16} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
