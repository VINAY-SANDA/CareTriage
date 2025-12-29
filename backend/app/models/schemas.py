"""
Pydantic Schemas for API Request/Response Validation
Defines all data models used across the application.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============== Enums ==============

class Severity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportType(str, Enum):
    CLINICIAN = "clinician"
    PATIENT = "patient"


# ============== Symptom Models ==============

class SymptomInput(BaseModel):
    """Raw symptom input from user."""
    description: str = Field(..., description="Natural language symptom description")
    user_id: Optional[str] = Field(None, description="User identifier for personalization")


class StructuredSymptom(BaseModel):
    """Structured clinical representation of a symptom."""
    original_text: str
    clinical_term: str
    icd10_code: Optional[str] = None
    snomed_code: Optional[str] = None
    body_system: str
    severity: Severity
    duration: Optional[str] = None
    location: Optional[str] = None
    modifying_factors: Optional[List[str]] = None


class DisambiguationResult(BaseModel):
    """Result from Symptom Disambiguation Agent."""
    symptoms: List[StructuredSymptom]
    clarification_needed: bool = False
    clarification_questions: Optional[List[str]] = None
    confidence: float = Field(..., ge=0.0, le=1.0)


# ============== Triage Models ==============

class TriageQuestion(BaseModel):
    """A clinical triage question."""
    question: str
    category: str
    required: bool = True


class TriageResponse(BaseModel):
    """User's response to a triage question."""
    question_id: str
    response: str


class ClinicalAssessment(BaseModel):
    """Clinical assessment from Triage Agent."""
    chief_complaint: str
    history_of_present_illness: str
    relevant_medical_history: Optional[str] = None
    differential_diagnoses: List[Dict[str, Any]]
    recommended_actions: List[str]
    urgency_level: str
    stw_references: List[str] = []


# ============== Risk Assessment Models ==============

class VitalSigns(BaseModel):
    """Patient vital signs for risk assessment."""
    heart_rate: Optional[int] = Field(None, ge=30, le=250)
    blood_pressure_systolic: Optional[int] = Field(None, ge=50, le=250)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=30, le=150)
    temperature: Optional[float] = Field(None, ge=35.0, le=42.0)
    respiratory_rate: Optional[int] = Field(None, ge=5, le=60)
    oxygen_saturation: Optional[int] = Field(None, ge=50, le=100)


class RiskAssessment(BaseModel):
    """Risk assessment from Red-Flag ML Engine."""
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    escalation_required: bool
    red_flags: List[str]
    contributing_factors: List[Dict[str, Any]]  # Contains 'factor' (str) and 'contribution' (float)
    recommendations: List[str]


# ============== Personalization Models ==============

class UserPreferences(BaseModel):
    """User preferences for personalization."""
    language: str = "en"
    region: str = "India"
    dietary_preferences: List[str] = []
    cultural_considerations: List[str] = []
    communication_style: str = "formal"


class PersonalizedRecommendation(BaseModel):
    """Culturally adapted recommendation."""
    original_recommendation: str
    adapted_recommendation: str
    cultural_notes: Optional[str] = None


# ============== Report Models ==============

class ClinicianReport(BaseModel):
    """Technical report for healthcare professionals."""
    report_id: str
    generated_at: datetime
    patient_id: Optional[str] = None
    symptoms: List[StructuredSymptom]
    clinical_assessment: ClinicalAssessment
    risk_assessment: RiskAssessment
    stw_guidelines: List[str]
    icd10_codes: List[str]
    recommendations: List[str]


class PatientReport(BaseModel):
    """Simplified report for patients."""
    report_id: str
    generated_at: datetime
    summary: str
    what_you_told_us: str
    our_assessment: str
    recommendations: List[str]
    warning_signs: List[str]
    when_to_seek_help: str


# ============== Chat Models ==============

class ChatMessage(BaseModel):
    """A single chat message."""
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """Chat request from frontend."""
    message: str
    session_id: Optional[str] = None
    user_preferences: Optional[UserPreferences] = None


class ChatResponse(BaseModel):
    """Chat response to frontend."""
    message: str
    session_id: str
    requires_clarification: bool = False
    clarification_options: Optional[List[str]] = None
    risk_alert: Optional[RiskAssessment] = None
    report_ready: bool = False


# ============== API Models ==============

class AnalysisRequest(BaseModel):
    """Full analysis request."""
    symptoms: str
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    vital_signs: Optional[VitalSigns] = None
    medical_history: Optional[str] = None
    user_preferences: Optional[UserPreferences] = None


class AnalysisResponse(BaseModel):
    """Full analysis response."""
    session_id: str
    disambiguation_result: DisambiguationResult
    clinical_assessment: ClinicalAssessment
    risk_assessment: RiskAssessment
    clinician_report: Optional[ClinicianReport] = None
    patient_report: Optional[PatientReport] = None


class DocumentUploadResponse(BaseModel):
    """Response after uploading ICMR documents."""
    success: bool
    documents_processed: int
    chunks_created: int
    message: str
