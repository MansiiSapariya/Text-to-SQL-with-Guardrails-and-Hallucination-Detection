import React, { useState } from 'react';
import { Copy, Check, ChevronDown, ChevronUp } from 'lucide-react';

const SQL_KEYWORDS = [
  'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'FULL',
  'GROUP BY', 'ORDER BY', 'LIMIT', 'OFFSET', 'HAVING', 'AND', 'OR', 'NOT',
  'AS', 'ON', 'IN', 'IS', 'NULL', 'DESC', 'ASC', 'BETWEEN', 'LIKE', 'CAST',
  'COUNT', 'SUM', 'AVG', 'MIN', 'MAX'
];

function tokenizeSQL(sql) {
  // Very basic regex tokenizer for styling
  if (!sql) return [];
  const tokens = [];
  const regex = /(--.*$|'[^']*'|"[^"]*"|\b\d+(?:\.\d+)?\b|\b(?:[A-Z_][A-Z0-9_]*)\b|[ \t\n\r]+|.)/gm;
  
  let match;
  while ((match = regex.exec(sql)) !== null) {
    const val = match[0];
    if (val.startsWith('--')) {
      tokens.push({ type: 'comment', value: val });
    } else if (val.startsWith("'") || val.startsWith('"')) {
      tokens.push({ type: 'string', value: val });
    } else if (/^\d+(?:\.\d+)?$/.test(val)) {
      tokens.push({ type: 'number', value: val });
    } else if (/^[ \t\n\r]+$/.test(val)) {
      tokens.push({ type: 'whitespace', value: val });
    } else {
      const upper = val.toUpperCase();
      if (SQL_KEYWORDS.includes(upper)) {
        tokens.push({ type: 'keyword', value: val });
      } else {
        tokens.push({ type: 'text', value: val });
      }
    }
  }
  return tokens;
}

export default function SQLDisplay({ sql, title = "Generated SQL" }) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(true);

  const handleCopy = () => {
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const tokens = tokenizeSQL(sql);

  return (
    <div className="sql-container">
      <div className="sql-header">
        <span className="sql-title">{title}</span>
        <div className="sql-actions">
          <button className="icon-btn" onClick={() => setExpanded(!expanded)}>
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          <button className="icon-btn" onClick={handleCopy} title="Copy SQL">
            {copied ? <Check size={16} color="var(--accent-success)" /> : <Copy size={16} />}
          </button>
        </div>
      </div>
      {expanded && (
        <div className="sql-body">
          <pre>
            {tokens.map((token, i) => {
              if (token.type === 'whitespace') return <span key={i}>{token.value}</span>;
              return <span key={i} className={`sql-${token.type}`}>{token.value}</span>;
            })}
          </pre>
        </div>
      )}
    </div>
  );
}
