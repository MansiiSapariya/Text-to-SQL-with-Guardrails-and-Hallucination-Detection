import React, { useState } from 'react';
import { Database } from 'lucide-react';
import { useSession } from './hooks/useSession';
import { submitQuery } from './services/api';

import QueryInput from './components/QueryInput';
import SQLDisplay from './components/SQLDisplay';
import ConfidenceScore from './components/ConfidenceScore';
import ResultsTable from './components/ResultsTable';
import HistorySidebar from './components/HistorySidebar';
import GuardrailWarning from './components/GuardrailWarning';
import ClarificationRequest from './components/ClarificationRequest';
import LoadingState from './components/LoadingState';

const SAMPLE_QUERIES = [
  "Which artist sold the most tracks?",
  "Top 5 customers by spending",
  "Revenue by genre",
  "Monthly sales trend 2013"
];

function App() {
  const { sessionId, history, addToHistory, clearHistory } = useSession();
  const [currentResult, setCurrentResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleQuery = async (question) => {
    setLoading(true);
    setError(null);
    setCurrentResult(null);
    
    try {
      const result = await submitQuery(question, sessionId);
      setCurrentResult(result);
      addToHistory(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadHistoryItem = (item) => {
    setCurrentResult(item);
    setError(null);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="app-logo">
          <Database size={24} color="var(--accent-primary)" />
          Query<span>Lens</span>
        </div>
      </header>
      
      <div className="app-main">
        <HistorySidebar 
          history={history} 
          currentQueryId={currentResult?.query_id}
          onSelect={loadHistoryItem}
          onClear={clearHistory}
        />
        
        <div className="content-area">
          <QueryInput 
            onSubmit={handleQuery} 
            isLoading={loading}
            sampleQueries={SAMPLE_QUERIES}
          />
          
          <div className="results-area">
            {error && (
              <div className="banner banner-error">
                <div className="banner-content">
                  <h4>Error Execution</h4>
                  <p>{error}</p>
                </div>
              </div>
            )}
            
            {loading && <LoadingState />}
            
            {!loading && currentResult && (
              <>
                <GuardrailWarning warnings={currentResult.guardrail_warnings} />
                
                {currentResult.hallucination_flags?.length > 0 && (
                  <div className="banner banner-error">
                    <div className="banner-content">
                      <h4>Potential Hallucination Detected</h4>
                      <ul>
                        {currentResult.hallucination_flags.map((f, i) => <li key={i}>{f}</li>)}
                      </ul>
                    </div>
                  </div>
                )}

                {currentResult.clarification_needed ? (
                  <ClarificationRequest 
                    clarification={currentResult.clarification_needed} 
                    onSelect={(interp) => handleQuery(interp)}
                  />
                ) : (
                  <>
                    <div className="results-grid">
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                        <SQLDisplay sql={currentResult.sql} />
                        <ResultsTable 
                          results={currentResult.results}
                          columns={currentResult.columns || []}
                          rowCount={currentResult.row_count || 0}
                          executionTime={currentResult.execution_time_ms || 0}
                          truncated={currentResult.truncated}
                        />
                      </div>
                      <div>
                        {currentResult.confidence && (
                          <ConfidenceScore confidence={currentResult.confidence} />
                        )}
                        {currentResult.sql_explanation && (
                          <div className="confidence-card" style={{ marginTop: '24px' }}>
                            <h3 style={{ fontSize: '1rem', marginBottom: '8px' }}>Explanation</h3>
                            <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                              {currentResult.sql_explanation}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </>
            )}
            
            {!loading && !currentResult && !error && (
              <div className="empty-state">
                <Database className="empty-icon" />
                <h3>Welcome to QueryLens</h3>
                <p>Ask a question about your data to get started.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
