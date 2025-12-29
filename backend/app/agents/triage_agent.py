"""
Clinical Triage Agent
Conducts structured clinical interviews following the specific steps defined in STW.
Uses LLM + Strict Prompt Engineering.
"""
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..utils.gemini_client import gemini_client
from ..models.schemas import (
    StructuredSymptom, ClinicalAssessment, TriageQuestion, Severity
)
from .retrieval_agent import retrieval_agent

logger = logging.getLogger(__name__)


CLINICAL_TRIAGE_SYSTEM_PROMPT = """You are an experienced clinical triage specialist conducting a structured patient interview. Your role is to:

1. Gather comprehensive clinical history following the OPQRST method:
   - Onset: When did symptoms begin?
   - Provocation/Palliation: What makes it better or worse?
   - Quality: How would you describe the symptom?
   - Region/Radiation: Where is it located? Does it spread?
   - Severity: How severe on a scale of 1-10?
   - Time: Is it constant or intermittent?

2. Assess relevant medical history:
   - Past medical conditions
   - Current medications
   - Allergies
   - Family history (if relevant)
   - Recent travel or exposures

3. Generate differential diagnoses based on symptoms
4. Recommend appropriate level of care

RULES:
- Be professional and empathetic
- Ask one focused question at a time
- Prioritize life-threatening conditions
- Follow evidence-based clinical guidelines
- Do not diagnose, but suggest possible conditions to investigate
- Always err on the side of caution for serious symptoms

Respond in JSON format when generating assessments."""


DIFFERENTIAL_DIAGNOSIS_PROMPT = """Based on the following patient information, generate a clinical assessment:

Patient Information:
{patient_info}

Symptoms:
{symptoms}

Additional History:
{history}

Relevant STW Guidelines:
{stw_guidelines}

Generate a JSON response with:
{{
    "chief_complaint": "primary presenting complaint",
    "history_of_present_illness": "detailed narrative of the illness",
    "relevant_medical_history": "pertinent medical history",
    "differential_diagnoses": [
        {{
            "condition": "condition name",
            "likelihood": "high/medium/low",
            "reasoning": "clinical reasoning",
            "red_flags_present": true/false
        }}
    ],
    "recommended_actions": ["list of recommended next steps"],
    "urgency_level": "emergency/urgent/routine/self-care"
}}"""


class TriageSession:
    """Manages state for a clinical triage session."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.symptoms: List[StructuredSymptom] = []
        self.questions_asked: List[Dict[str, Any]] = []
        self.responses: List[Dict[str, Any]] = []
        self.patient_info: Dict[str, Any] = {}
        self.assessment: Optional[ClinicalAssessment] = None
        self.current_step = "initial"
        
    def add_symptom(self, symptom: StructuredSymptom):
        self.symptoms.append(symptom)
    
    def add_response(self, question: str, response: str):
        self.responses.append({
            "question": question,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "symptoms": [s.dict() for s in self.symptoms],
            "responses": self.responses,
            "patient_info": self.patient_info,
            "current_step": self.current_step
        }


class ClinicalTriageAgent:
    """
    Agent for conducting structured clinical interviews and generating assessments.
    """
    
    def __init__(self):
        self.gemini = gemini_client
        self.retrieval = retrieval_agent
        self.sessions: Dict[str, TriageSession] = {}
        
        # Define triage question categories
        self.question_categories = [
            "onset",
            "quality",
            "severity",
            "location",
            "timing",
            "modifying_factors",
            "associated_symptoms",
            "medical_history",
            "medications",
            "allergies"
        ]
    
    def start_session(
        self,
        symptoms: List[StructuredSymptom],
        patient_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new triage session.
        
        Args:
            symptoms: Initial structured symptoms
            patient_info: Optional patient demographics
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        session = TriageSession(session_id)
        
        for symptom in symptoms:
            session.add_symptom(symptom)
        
        if patient_info:
            session.patient_info = patient_info
        
        self.sessions[session_id] = session
        logger.info(f"Started triage session: {session_id}")
        
        return session_id
    
    def get_next_question(self, session_id: str) -> Optional[TriageQuestion]:
        """
        Get the next clinical question for the session.
        
        Args:
            session_id: Active session ID
            
        Returns:
            Next question to ask, or None if assessment is ready
        """
        session = self.sessions.get(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return None
        
        # Determine what information is missing
        missing_info = self._identify_missing_info(session)
        
        if not missing_info:
            session.current_step = "ready_for_assessment"
            return None
        
        # Generate next question based on priority
        question = self._generate_question(session, missing_info[0])
        session.questions_asked.append(question.dict())
        
        return question
    
    def _identify_missing_info(self, session: TriageSession) -> List[str]:
        """Identify what clinical information is still needed."""
        missing = []
        
        # Check each symptom for missing details
        for symptom in session.symptoms:
            if not symptom.duration:
                if "duration" not in [r.get("category") for r in session.responses]:
                    missing.append("onset")
            
            if symptom.severity == Severity.MODERATE:
                if "severity" not in [r.get("category") for r in session.responses]:
                    missing.append("severity")
        
        # Check for medical history
        if not session.patient_info.get("medical_history"):
            if "medical_history" not in [r.get("category") for r in session.responses]:
                missing.append("medical_history")
        
        # Check for medications
        if "medications" not in [r.get("category") for r in session.responses]:
            missing.append("medications")
        
        # Check for allergies
        if "allergies" not in [r.get("category") for r in session.responses]:
            missing.append("allergies")
        
        return missing[:3]  # Return top 3 priorities
    
    def _generate_question(self, session: TriageSession, category: str) -> TriageQuestion:
        """Generate a clinical question for a category."""
        primary_symptom = session.symptoms[0].clinical_term if session.symptoms else "your symptoms"
        
        question_templates = {
            "onset": f"When did you first notice {primary_symptom}? Please describe how it started.",
            "quality": f"How would you describe the {primary_symptom}? (e.g., sharp, dull, throbbing, burning)",
            "severity": f"On a scale of 1 to 10, where 10 is the worst, how severe is your {primary_symptom}?",
            "location": f"Can you point to exactly where you feel the {primary_symptom}? Does it spread anywhere?",
            "timing": f"Is the {primary_symptom} constant, or does it come and go?",
            "modifying_factors": f"Is there anything that makes your {primary_symptom} better or worse?",
            "associated_symptoms": "Are you experiencing any other symptoms along with this?",
            "medical_history": "Do you have any medical conditions I should know about?",
            "medications": "Are you currently taking any medications, supplements, or herbal remedies?",
            "allergies": "Do you have any known allergies, especially to medications?"
        }
        
        return TriageQuestion(
            question=question_templates.get(category, f"Please tell me more about your {category}."),
            category=category,
            required=category in ["onset", "severity", "allergies"]
        )
    
    def process_response(
        self,
        session_id: str,
        response: str,
        question_category: str
    ) -> Dict[str, Any]:
        """
        Process patient's response to a triage question.
        
        Args:
            session_id: Active session ID
            response: Patient's response
            question_category: Category of the question answered
            
        Returns:
            Status and next steps
        """
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        session.add_response(question_category, response)
        session.responses[-1]["category"] = question_category
        
        # Check if we have enough information for assessment
        next_question = self.get_next_question(session_id)
        
        if next_question:
            return {
                "status": "continue",
                "next_question": next_question.dict(),
                "progress": len(session.responses) / 6  # Approximate progress
            }
        else:
            return {
                "status": "ready",
                "message": "Sufficient information gathered for clinical assessment"
            }
    
    def generate_assessment(self, session_id: str) -> ClinicalAssessment:
        """
        Generate clinical assessment based on gathered information.
        
        Args:
            session_id: Session ID
            
        Returns:
            Clinical assessment
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Gather all symptom terms for STW lookup
        symptom_terms = [s.clinical_term for s in session.symptoms]
        
        # Retrieve relevant STW guidelines
        stw_results = self.retrieval.search_guidelines(symptom_terms)
        stw_text = "\n".join([r["text"] for r in stw_results[:3]]) if stw_results else "No specific guidelines found."
        
        # Prepare prompt
        symptoms_text = "\n".join([
            f"- {s.clinical_term} (Severity: {s.severity.value}, Duration: {s.duration or 'unspecified'})"
            for s in session.symptoms
        ])
        
        history_text = "\n".join([
            f"Q: {r.get('question', r.get('category', 'Unknown'))}\nA: {r['response']}"
            for r in session.responses
        ])
        
        patient_text = json.dumps(session.patient_info) if session.patient_info else "Not provided"
        
        prompt = DIFFERENTIAL_DIAGNOSIS_PROMPT.format(
            patient_info=patient_text,
            symptoms=symptoms_text,
            history=history_text,
            stw_guidelines=stw_text
        )
        
        try:
            response = self.gemini.generate(
                prompt=prompt,
                system_instruction=CLINICAL_TRIAGE_SYSTEM_PROMPT,
                temperature=0.3
            )
            
            # Parse JSON response
            json_str = self._extract_json(response)
            assessment_data = json.loads(json_str)
            
            assessment = ClinicalAssessment(
                chief_complaint=assessment_data.get("chief_complaint", "Not specified"),
                history_of_present_illness=assessment_data.get("history_of_present_illness", ""),
                relevant_medical_history=assessment_data.get("relevant_medical_history"),
                differential_diagnoses=assessment_data.get("differential_diagnoses", []),
                recommended_actions=assessment_data.get("recommended_actions", []),
                urgency_level=assessment_data.get("urgency_level", "routine"),
                stw_references=[r["source"] for r in stw_results if r.get("source")]
            )
            
            session.assessment = assessment
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to generate assessment: {e}")
            # Return basic assessment
            return ClinicalAssessment(
                chief_complaint=symptom_terms[0] if symptom_terms else "Unspecified complaint",
                history_of_present_illness="Assessment generation failed. Please consult a healthcare provider.",
                differential_diagnoses=[],
                recommended_actions=["Consult a healthcare provider for proper evaluation"],
                urgency_level="routine",
                stw_references=[]
            )
    
    def _extract_json(self, response: str) -> str:
        """Extract JSON from LLM response."""
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            return response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            return response[start:end].strip()
        
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return response[start:end]
        
        return response
    
    def quick_assess(
        self,
        symptoms: List[StructuredSymptom],
        patient_info: Optional[Dict[str, Any]] = None
    ) -> ClinicalAssessment:
        """
        Perform quick assessment without interactive questioning.
        
        Args:
            symptoms: Structured symptoms
            patient_info: Optional patient info
            
        Returns:
            Clinical assessment
        """
        session_id = self.start_session(symptoms, patient_info)
        return self.generate_assessment(session_id)
    
    def end_session(self, session_id: str):
        """End and cleanup a triage session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Ended triage session: {session_id}")


# Singleton instance
triage_agent = ClinicalTriageAgent()
