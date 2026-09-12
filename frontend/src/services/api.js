const API_BASE = 'http://localhost:8000';

export async function submitQuery(question, sessionId) {
  const res = await fetch(`${API_BASE}/v1/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, session_id: sessionId })
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Failed to execute query');
  }
  return res.json();
}

export async function getSchema() {
  const res = await fetch(`${API_BASE}/v1/schema`);
  if (!res.ok) throw new Error('Failed to fetch schema');
  return res.json();
}

export async function getHistory(sessionId) {
  const res = await fetch(`${API_BASE}/v1/history?session_id=${encodeURIComponent(sessionId)}`);
  if (!res.ok) throw new Error('Failed to fetch history');
  return res.json();
}

export async function submitFeedback(queryId, correct, correctedSql) {
  const res = await fetch(`${API_BASE}/v1/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query_id: queryId, correct, corrected_sql: correctedSql })
  });
  if (!res.ok) throw new Error('Failed to submit feedback');
  return res.json();
}
