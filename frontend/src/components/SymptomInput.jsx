import React from 'react';

/**
 * Symptom Input Component
 * Form for detailed symptom entry
 */
export default function SymptomInput({ onSubmit, isLoading }) {
  const [formData, setFormData] = React.useState({
    symptoms: '',
    duration: '',
    severity: 'moderate',
    age: '',
    gender: '',
    medicalHistory: ''
  });
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.symptoms.trim()) {
      onSubmit(formData);
    }
  };
  
  return (
    <form className="card" onSubmit={handleSubmit}>
      <div className="card-header">
        <span style={{ fontSize: '1.5rem' }}>📋</span>
        <h3 className="card-title">Symptom Assessment</h3>
      </div>
      
      {/* Symptoms */}
      <div className="mb-lg">
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
          Describe your symptoms *
        </label>
        <textarea
          name="symptoms"
          className="chat-input"
          style={{ width: '100%', minHeight: '100px' }}
          placeholder="E.g., I have a severe headache with fever and body aches for the past 2 days..."
          value={formData.symptoms}
          onChange={handleChange}
          required
        />
      </div>
      
      {/* Duration & Severity Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }} className="mb-lg">
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
            Duration
          </label>
          <input
            type="text"
            name="duration"
            className="chat-input"
            style={{ width: '100%' }}
            placeholder="E.g., 2 days"
            value={formData.duration}
            onChange={handleChange}
          />
        </div>
        
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
            Severity
          </label>
          <select
            name="severity"
            className="chat-input"
            style={{ width: '100%' }}
            value={formData.severity}
            onChange={handleChange}
          >
            <option value="mild">Mild</option>
            <option value="moderate">Moderate</option>
            <option value="severe">Severe</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>
      
      {/* Age & Gender Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }} className="mb-lg">
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
            Age (optional)
          </label>
          <input
            type="number"
            name="age"
            className="chat-input"
            style={{ width: '100%' }}
            placeholder="Your age"
            value={formData.age}
            onChange={handleChange}
            min="0"
            max="120"
          />
        </div>
        
        <div>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
            Gender (optional)
          </label>
          <select
            name="gender"
            className="chat-input"
            style={{ width: '100%' }}
            value={formData.gender}
            onChange={handleChange}
          >
            <option value="">Select...</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>
      
      {/* Medical History */}
      <div className="mb-lg">
        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>
          Medical History (optional)
        </label>
        <textarea
          name="medicalHistory"
          className="chat-input"
          style={{ width: '100%', minHeight: '60px' }}
          placeholder="Any existing conditions, allergies, or medications..."
          value={formData.medicalHistory}
          onChange={handleChange}
        />
      </div>
      
      {/* Submit */}
      <button 
        type="submit" 
        className="btn btn-primary w-full"
        disabled={!formData.symptoms.trim() || isLoading}
      >
        {isLoading ? (
          <>
            <span className="loading-spinner" style={{ width: '20px', height: '20px' }}></span>
            Analyzing...
          </>
        ) : (
          <>Analyze Symptoms</>
        )}
      </button>
    </form>
  );
}
