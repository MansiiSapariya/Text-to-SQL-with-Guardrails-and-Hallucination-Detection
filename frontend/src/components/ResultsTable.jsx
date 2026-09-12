import React, { useState, useMemo } from 'react';
import { ArrowUp, ArrowDown, Database } from 'lucide-react';

function formatValue(val) {
  if (val === null || val === undefined) return <span className="sql-comment">NULL</span>;
  if (typeof val === 'number') {
    if (!Number.isInteger(val)) return val.toFixed(2);
    return val.toLocaleString();
  }
  if (typeof val === 'string') {
    // Simple date check
    if (/^\d{4}-\d{2}-\d{2}T/.test(val)) {
      return new Date(val).toLocaleString();
    }
    return val;
  }
  return String(val);
}

export default function ResultsTable({ results, columns, rowCount, executionTime, truncated }) {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  const sortedResults = useMemo(() => {
    let sortableItems = [...(results || [])];
    if (sortConfig.key !== null) {
      sortableItems.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [results, sortConfig]);

  const requestSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  if (!results || results.length === 0) {
    return (
      <div className="table-container" style={{ minHeight: '300px' }}>
        <div className="empty-state">
          <Database className="empty-icon" />
          <h3>No results found</h3>
          <p>The query executed successfully but returned 0 rows.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="table-container">
      {truncated && (
        <div className="truncation-banner">
          Showing limited results. The full dataset is larger.
        </div>
      )}
      <div className="table-wrapper">
        <table className="results-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col} onClick={() => requestSort(col)}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    {col}
                    {sortConfig.key === col ? (
                      sortConfig.direction === 'asc' ? <ArrowUp size={12} /> : <ArrowDown size={12} />
                    ) : null}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sortedResults.map((row, i) => (
              <tr key={i}>
                {columns.map((col) => (
                  <td key={`${i}-${col}`}>{formatValue(row[col])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="table-footer">
        <div>{rowCount} {rowCount === 1 ? 'row' : 'rows'}</div>
        <div>{executionTime}ms execution time</div>
      </div>
    </div>
  );
}
