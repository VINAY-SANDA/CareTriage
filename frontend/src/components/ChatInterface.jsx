import React, { useState, useRef, useEffect } from 'react';
import RiskAlert from './RiskAlert';
import ReportViewer from './ReportViewer';
import { sendChatMessage } from '../services/api';

/**
 * Chat Interface Component
 * Main conversational UI for symptom collection
 */
export default function ChatInterface() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! I\'m your AI Clinical Assistant. I\'m here to help you understand your symptoms and provide guidance. Please describe what you\'re experiencing, and I\'ll do my best to help. 🏥\n\nFor example, you can say: "I have a headache and fever for 2 days"'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [currentRisk, setCurrentRisk] = useState(null);
  const [currentReport, setCurrentReport] = useState(null);
  const [error, setError] = useState(null);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);
  
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    
    const userMessage = input.trim();
    setInput('');
    setError(null);
    
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);
    
    try {
      const response = await sendChatMessage(userMessage, sessionId);
      
      // Save session ID
      if (response.session_id) {
        setSessionId(response.session_id);
      }
      
      // Add assistant response
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.message,
        riskAlert: response.risk_alert,
        reportReady: response.report_ready
      }]);
      
      // Update risk if present
      if (response.risk_alert) {
        setCurrentRisk(response.risk_alert);
      }
      
    } catch (err) {
      console.error('Chat error:', err);
      setError('Failed to send message. Please check if the backend server is running.');
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'I apologize, but I\'m having trouble connecting to the server. Please make sure the backend is running on http://localhost:8000'
      }]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };
  
  const handleQuickAction = (text) => {
    setInput(text);
    inputRef.current?.focus();
  };
  
  return (
    <div className="chat-container card">
      {/* Chat Messages */}
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'assistant' ? '🤖' : '👤'}
            </div>
            <div className="message-content">
              {msg.content.split('\n').map((line, i) => (
                <React.Fragment key={i}>
                  {line}
                  {i < msg.content.split('\n').length - 1 && <br />}
                </React.Fragment>
              ))}
            </div>
          </div>
        ))}
        
        {/* Risk Alert */}
        {currentRisk && (
          <RiskAlert risk={currentRisk} />
        )}
        
        {/* Report */}
        {currentReport && (
          <ReportViewer report={currentReport} type="patient" />
        )}
        
        {/* Typing Indicator */}
        {isLoading && (
          <div className="message assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="typing-indicator">
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Error Message */}
      {error && (
        <div style={{ 
          padding: '0.75rem 1rem', 
          background: 'rgba(239, 68, 68, 0.1)', 
          borderTop: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#f87171',
          fontSize: '0.875rem'
        }}>
          {error}
        </div>
      )}
      
      {/* Quick Actions */}
      <div style={{ 
        padding: '0.75rem 1rem', 
        borderTop: '1px solid rgba(255,255,255,0.05)',
        display: 'flex',
        gap: '0.5rem',
        flexWrap: 'wrap'
      }}>
        <button 
          className="btn btn-secondary" 
          style={{ fontSize: '0.8125rem', padding: '0.5rem 0.75rem' }}
          onClick={() => handleQuickAction("I have a headache and feel dizzy")}
        >
          Headache & Dizziness
        </button>
        <button 
          className="btn btn-secondary" 
          style={{ fontSize: '0.8125rem', padding: '0.5rem 0.75rem' }}
          onClick={() => handleQuickAction("I have stomach pain with nausea")}
        >
          Stomach Issues
        </button>
        <button 
          className="btn btn-secondary" 
          style={{ fontSize: '0.8125rem', padding: '0.5rem 0.75rem' }}
          onClick={() => handleQuickAction("I have fever and cough for 3 days")}
        >
          Fever & Cough
        </button>
      </div>
      
      {/* Input Area */}
      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <textarea
            ref={inputRef}
            className="chat-input"
            placeholder="Describe your symptoms..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            rows={1}
            disabled={isLoading}
          />
          <button 
            className="btn btn-primary btn-send"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
          >
            {isLoading ? '...' : '→'}
          </button>
        </div>
      </div>
    </div>
  );
}
