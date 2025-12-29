import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatInterface from './components/ChatInterface';
import SymptomInput from './components/SymptomInput';
import ReportViewer from './components/ReportViewer';
import RiskAlert from './components/RiskAlert';
import { analyzeSymptoms, healthCheck } from './services/api';

/**
 * AI Clinical Pipeline - Main Application
 */
export default function App() {
  const [view, setView] = useState('chat'); // 'chat' | 'form' | 'report'
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState('checking');
  
  // Check backend on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        await healthCheck();
        setBackendStatus('connected');
      } catch (err) {
        setBackendStatus('disconnected');
      }
    };
    checkBackend();
  }, []);
  
  // Handle form submission
  const handleFormSubmit = async (formData) => {
    setIsLoading(true);
    try {
      const result = await analyzeSymptoms({
        symptoms: formData.symptoms,
        patient_age: formData.age ? parseInt(formData.age) : null,
        patient_gender: formData.gender || null,
        medical_history: formData.medicalHistory || null
      });
      setAnalysisResult(result);
      setView('report');
    } catch (err) {
      console.error('Analysis failed:', err);
      alert('Analysis failed. Please make sure the backend server is running.');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="app">
      <Header />
      
      <main className="main-content">
        <div className="container">
          {/* Hero Section */}
          <div className="hero">
            <h1>🏥 AI Clinical Assistant</h1>
            <p>
              Describe your symptoms and get intelligent health guidance powered by 
              advanced AI and ICMR Standard Treatment Workflows.
            </p>
            
            {/* Backend Status */}
            <div style={{ 
              display: 'inline-flex', 
              alignItems: 'center', 
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              background: backendStatus === 'connected' 
                ? 'rgba(16, 185, 129, 0.1)' 
                : 'rgba(239, 68, 68, 0.1)',
              border: `1px solid ${backendStatus === 'connected' ? '#10b981' : '#ef4444'}`,
              borderRadius: '999px',
              fontSize: '0.8125rem',
              marginBottom: '1rem'
            }}>
              <span style={{ 
                width: '8px', 
                height: '8px', 
                borderRadius: '50%',
                background: backendStatus === 'connected' ? '#10b981' : '#ef4444'
              }}></span>
              {backendStatus === 'checking' && 'Connecting to server...'}
              {backendStatus === 'connected' && 'Backend connected'}
              {backendStatus === 'disconnected' && 'Backend offline - Please start the server'}
            </div>
            
            {/* View Toggle */}
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center' }}>
              <button 
                className={`btn ${view === 'chat' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setView('chat')}
              >
                💬 Chat Mode
              </button>
              <button 
                className={`btn ${view === 'form' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setView('form')}
              >
                📋 Detailed Form
              </button>
              {analysisResult && (
                <button 
                  className={`btn ${view === 'report' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setView('report')}
                >
                  📄 View Report
                </button>
              )}
            </div>
          </div>
          
          {/* Main Content Area */}
          {view === 'chat' && (
            <ChatInterface />
          )}
          
          {view === 'form' && (
            <div style={{ maxWidth: '700px', margin: '0 auto' }}>
              <SymptomInput onSubmit={handleFormSubmit} isLoading={isLoading} />
            </div>
          )}
          
          {view === 'report' && analysisResult && (
            <div style={{ maxWidth: '800px', margin: '0 auto' }}>
              {/* Risk Alert */}
              {analysisResult.risk_assessment && (
                <RiskAlert risk={analysisResult.risk_assessment} />
              )}
              
              {/* Patient Report */}
              {analysisResult.patient_report && (
                <ReportViewer report={analysisResult.patient_report} type="patient" />
              )}
              
              {/* Actions */}
              <div style={{ 
                display: 'flex', 
                gap: '1rem', 
                justifyContent: 'center',
                marginTop: '1.5rem'
              }}>
                <button 
                  className="btn btn-secondary"
                  onClick={() => {
                    setAnalysisResult(null);
                    setView('chat');
                  }}
                >
                  Start New Assessment
                </button>
                <button 
                  className="btn btn-primary"
                  onClick={() => {
                    const report = analysisResult.patient_report;
                    const text = `
Health Assessment Report
Report ID: ${report.report_id}
Generated: ${new Date(report.generated_at).toLocaleString()}

Summary:
${report.summary}

Recommendations:
${report.recommendations?.map((r, i) => `${i+1}. ${r}`).join('\n') || 'None'}

Warning Signs:
${report.warning_signs?.map(s => `• ${s}`).join('\n') || 'None'}
                    `.trim();
                    navigator.clipboard.writeText(text);
                    alert('Report copied to clipboard!');
                  }}
                >
                  📋 Copy Report
                </button>
              </div>
            </div>
          )}
          
          {/* Features */}
          {view === 'chat' && (
            <div className="features-grid" style={{ marginTop: '3rem' }}>
              <div className="card feature-card">
                <div className="feature-icon">🧠</div>
                <h4 className="feature-title">Symptom Analysis</h4>
                <p className="feature-description">
                  Advanced AI converts your symptoms into structured clinical terms with ICD-10 coding.
                </p>
              </div>
              
              <div className="card feature-card">
                <div className="feature-icon">📚</div>
                <h4 className="feature-title">ICMR Guidelines</h4>
                <p className="feature-description">
                  Powered by Indian Council of Medical Research Standard Treatment Workflows.
                </p>
              </div>
              
              <div className="card feature-card">
                <div className="feature-icon">⚠️</div>
                <h4 className="feature-title">Risk Assessment</h4>
                <p className="feature-description">
                  ML-powered red-flag detection identifies urgent symptoms requiring immediate care.
                </p>
              </div>
              
              <div className="card feature-card">
                <div className="feature-icon">🇮🇳</div>
                <h4 className="feature-title">Cultural Adaptation</h4>
                <p className="feature-description">
                  Recommendations personalized for Indian dietary preferences and lifestyle.
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
      
      {/* Footer */}
      <footer style={{ 
        textAlign: 'center', 
        padding: '1.5rem',
        borderTop: '1px solid rgba(255,255,255,0.05)',
        color: '#6b7280',
        fontSize: '0.8125rem'
      }}>
        <p>⚠️ Disclaimer: This is a prototype for educational purposes. Not for actual medical diagnosis.</p>
        <p style={{ marginTop: '0.5rem' }}>Powered by Gemini AI • Built with ❤️ for better healthcare</p>
      </footer>
    </div>
  );
}
