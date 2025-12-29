import React from 'react';

/**
 * Risk Alert Component
 * Displays risk assessment with visual indicators
 */
export default function RiskAlert({ risk }) {
  if (!risk) return null;
  
  const { risk_score, risk_level, red_flags, recommendations, escalation_required } = risk;
  
  const getIcon = () => {
    switch (risk_level) {
      case 'critical':
      case 'high':
        return '⚠️';
      case 'medium':
        return '⚡';
      default:
        return '✓';
    }
  };
  
  const getTitle = () => {
    switch (risk_level) {
      case 'critical':
        return 'CRITICAL - Immediate Attention Required';
      case 'high':
        return 'High Risk Detected';
      case 'medium':
        return 'Moderate Risk';
      default:
        return 'Low Risk';
    }
  };
  
  return (
    <div className={`risk-alert ${risk_level}`}>
      <div className="risk-alert-header">
        <span className="risk-alert-icon">{getIcon()}</span>
        <span className="risk-alert-title">{getTitle()}</span>
      </div>
      
      <div className="risk-score">
        <span>Risk Score:</span>
        <div className="risk-score-bar">
          <div 
            className={`risk-score-fill ${risk_level}`}
            style={{ width: `${risk_score * 100}%` }}
          />
        </div>
        <span>{(risk_score * 100).toFixed(0)}%</span>
      </div>
      
      {red_flags && red_flags.length > 0 && (
        <div className="mt-md">
          <strong>Red Flags:</strong>
          <ul style={{ marginLeft: '1rem', marginTop: '0.5rem' }}>
            {red_flags.map((flag, idx) => (
              <li key={idx} style={{ color: '#ef4444' }}>{flag}</li>
            ))}
          </ul>
        </div>
      )}
      
      {escalation_required && (
        <div className="mt-md" style={{ 
          padding: '0.75rem', 
          background: 'rgba(239, 68, 68, 0.2)', 
          borderRadius: '0.5rem',
          fontWeight: 500
        }}>
          🚨 Please seek medical attention immediately or call emergency services (112)
        </div>
      )}
    </div>
  );
}
