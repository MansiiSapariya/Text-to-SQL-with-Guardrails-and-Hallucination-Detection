import { useState, useEffect } from 'react';

function generateSessionId() {
  return 'sess_' + Math.random().toString(36).substring(2, 9);
}

export function useSession() {
  const [sessionId, setSessionId] = useState('');
  const [history, setHistory] = useState([]);

  useEffect(() => {
    let sid = localStorage.getItem('text2sql_session_id');
    if (!sid) {
      sid = generateSessionId();
      localStorage.setItem('text2sql_session_id', sid);
    }
    setSessionId(sid);
    
    const savedHistory = localStorage.getItem('text2sql_history');
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error('Failed to parse history', e);
      }
    }
  }, []);

  const addToHistory = (result) => {
    setHistory((prev) => {
      const newHistory = [result, ...prev.filter(item => item.query_id !== result.query_id)];
      localStorage.setItem('text2sql_history', JSON.stringify(newHistory));
      return newHistory;
    });
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('text2sql_history');
  };

  return { sessionId, history, addToHistory, clearHistory };
}
