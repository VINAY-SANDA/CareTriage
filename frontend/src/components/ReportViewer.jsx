import React from 'react';

/**
 * Report Viewer Component
 * Displays patient-friendly reports
 */
export default function ReportViewer({ report, type = 'patient' }) {
  if (!report) return null;
  
  if (type === 'patient') {
    return (
      <div className="report">
        <div className="report-header">
          <h3>📋 Health Assessment Report</h3>
          <p style={{ opacity: 0.9, fontSize: '0.875rem', marginTop: '0.5rem' }}>
            Report ID: {report.report_id}
          </p>
        </div>
        
        <div className="report-body">
          {/* Summary */}
          <div className="report-section">
            <div className="report-section-title">
              <span>📝</span> Summary
            </div>
            <div className="report-section-content">
              {report.summary}
            </div>
          </div>
          
          {/* What You Told Us */}
          <div className="report-section">
            <div className="report-section-title">
              <span>🗣️</span> What You Told Us
            </div>
            <div className="report-section-content">
              {report.what_you_told_us}
            </div>
          </div>
          
          {/* Our Assessment */}
          <div className="report-section">
            <div className="report-section-title">
              <span>🔍</span> Our Assessment
            </div>
            <div className="report-section-content">
              {report.our_assessment}
            </div>
          </div>
          
          {/* Recommendations */}
          {report.recommendations && report.recommendations.length > 0 && (
            <div className="report-section">
              <div className="report-section-title">
                <span>✅</span> Recommendations
              </div>
              <ul className="recommendation-list">
                {report.recommendations.map((rec, idx) => (
                  <li key={idx} className="recommendation-item">
                    <span className="recommendation-number">{idx + 1}.</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* Warning Signs */}
          {report.warning_signs && report.warning_signs.length > 0 && (
            <div className="report-section">
              <div className="report-section-title" style={{ color: '#ef4444' }}>
                <span>⚠️</span> Warning Signs to Watch
              </div>
              <ul style={{ listStyle: 'none' }}>
                {report.warning_signs.map((sign, idx) => (
                  <li key={idx} style={{ 
                    padding: '0.5rem 0', 
                    borderBottom: '1px solid rgba(255,255,255,0.05)',
                    color: '#f87171'
                  }}>
                    • {sign}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {/* When to Seek Help */}
          {report.when_to_seek_help && (
            <div className="report-section">
              <div className="report-section-title">
                <span>🏥</span> When to Seek Help
              </div>
              <div className="report-section-content" style={{ 
                padding: '1rem', 
                background: 'rgba(0, 212, 170, 0.1)', 
                borderRadius: '0.5rem',
                borderLeft: '3px solid #00d4aa'
              }}>
                {report.when_to_seek_help}
              </div>
            </div>
          )}
          
          {/* Disclaimer */}
          <div style={{ 
            marginTop: '2rem',
            padding: '1rem',
            background: 'rgba(255,255,255,0.03)',
            borderRadius: '0.5rem',
            fontSize: '0.8125rem',
            color: '#6b7280'
          }}>
            <strong>Disclaimer:</strong> This report is for informational purposes only and does not 
            constitute medical advice. Please consult a qualified healthcare professional for proper 
            diagnosis and treatment.
          </div>
        </div>
      </div>
    );
  }
  
  // Clinician report view
  return (
    <div className="report">
      <div className="report-header">
        <h3>📊 Clinical Assessment Report</h3>
        <p style={{ opacity: 0.9, fontSize: '0.875rem', marginTop: '0.5rem' }}>
          Report ID: {report.report_id} | Type: Clinician
        </p>
      </div>
      
      <div className="report-body">
        <pre style={{ 
          background: 'rgba(0,0,0,0.3)', 
          padding: '1rem', 
          borderRadius: '0.5rem',
          overflow: 'auto',
          fontSize: '0.8125rem'
        }}>
          {JSON.stringify(report, null, 2)}
        </pre>
      </div>
    </div>
  );
}
