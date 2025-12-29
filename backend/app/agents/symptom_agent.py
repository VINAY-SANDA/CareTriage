"""
Symptom Disambiguation Agent
Converts ambiguous user descriptions into structured clinical terms via iterative clarification.
Uses Gemini LLM + Rule-based Medical Ontology.
"""
import json
from typing import List, Dict, Any, Optional
import logging

from ..utils.gemini_client import gemini_client
from ..knowledge_base.medical_ontology import medical_ontology, ICD10_SYMPTOM_CODES
from ..models.schemas import (
    SymptomInput, StructuredSymptom, DisambiguationResult, Severity
)

logger = logging.getLogger(__name__)


SYMPTOM_DISAMBIGUATION_PROMPT = """You are a medical symptom disambiguation assistant. Your role is to:
1. Extract all symptoms mentioned in the patient's description
2. Convert vague descriptions into precise medical terminology
3. Identify severity, duration, and location when mentioned
4. Flag any symptoms that need clarification

IMPORTANT RULES:
- Be thorough but do not add symptoms not mentioned
- Use standard medical terminology
- If duration is unclear, ask for clarification
- If location is ambiguous, ask for clarification
- Always be empathetic and professional

Respond in the following JSON format:
{
    "symptoms": [
        {
            "original_text": "the exact phrase from user",
            "clinical_term": "standard medical term",
            "body_system": "affected body system",
            "severity": "mild/moderate/severe/critical",
            "duration": "duration if mentioned or null",
            "location": "specific location or null",
            "modifying_factors": ["factors that make it better/worse"]
        }
    ],
    "clarification_needed": true/false,
    "clarification_questions": ["list of questions if needed"],
    "confidence": 0.0-1.0
}

Known body systems: neurological, respiratory, cardiovascular, gastrointestinal, musculoskeletal, dermatological, systemic, urological, ophthalmological, psychiatric"""


class SymptomDisambiguationAgent:
    """
    Agent for converting user symptom descriptions into structured clinical terms.
    Combines LLM understanding with rule-based medical ontology.
    """
    
    def __init__(self):
        self.gemini = gemini_client
        self.ontology = medical_ontology
    
    def disambiguate(self, input_data: SymptomInput) -> DisambiguationResult:
        """
        Main method to disambiguate symptoms from natural language.
        
        Args:
            input_data: Raw symptom input from user
            
        Returns:
            DisambiguationResult with structured symptoms
        """
        logger.info(f"Disambiguating symptoms: {input_data.description[:100]}...")
        
        # Step 1: Use Gemini to parse and structure the symptoms
        llm_result = self._llm_parse_symptoms(input_data.description)
        
        # Step 2: Enhance with ontology mappings (ICD-10, SNOMED codes)
        structured_symptoms = self._enhance_with_ontology(llm_result.get("symptoms", []))
        
        # Step 3: Check for red flags
        has_red_flags = self._check_red_flags(structured_symptoms)
        
        # Step 4: Build final result
        result = DisambiguationResult(
            symptoms=structured_symptoms,
            clarification_needed=llm_result.get("clarification_needed", False),
            clarification_questions=llm_result.get("clarification_questions"),
            confidence=llm_result.get("confidence", 0.8)
        )
        
        if has_red_flags:
            logger.warning("Red flag symptoms detected!")
        
        return result
    
    def _llm_parse_symptoms(self, description: str) -> Dict[str, Any]:
        """Use Gemini to parse symptoms from natural language."""
        try:
            prompt = f"""Patient's description: "{description}"

Based on the above description, extract and structure the symptoms."""
            
            response = self.gemini.generate(
                prompt=prompt,
                system_instruction=SYMPTOM_DISAMBIGUATION_PROMPT,
                temperature=0.3  # Lower temperature for more consistent parsing
            )
            
            # Parse JSON from response
            json_str = self._extract_json(response)
            result = json.loads(json_str)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            # Fallback: Basic extraction
            return self._fallback_parse(description)
        except Exception as e:
            logger.error(f"LLM symptom parsing failed: {e}")
            return self._fallback_parse(description)
    
    def _extract_json(self, response: str) -> str:
        """Extract JSON from LLM response that might include markdown."""
        # Remove markdown code blocks if present
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            return response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            return response[start:end].strip()
        
        # Try to find JSON object directly
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return response[start:end]
        
        return response
    
    def _fallback_parse(self, description: str) -> Dict[str, Any]:
        """Fallback method using ontology when LLM fails."""
        symptoms = []
        
        # Use ontology to find symptoms
        for symptom_key in ICD10_SYMPTOM_CODES.keys():
            symptom_phrase = symptom_key.replace("_", " ")
            if symptom_phrase in description.lower():
                symptoms.append({
                    "original_text": symptom_phrase,
                    "clinical_term": symptom_phrase,
                    "body_system": self.ontology.get_body_system(symptom_key) or "general",
                    "severity": self.ontology.classify_severity(description),
                    "duration": None,
                    "location": None,
                    "modifying_factors": []
                })
        
        # If no symptoms found, create a generic entry
        if not symptoms:
            symptoms.append({
                "original_text": description,
                "clinical_term": "general_discomfort",
                "body_system": "systemic",
                "severity": "moderate",
                "duration": None,
                "location": None,
                "modifying_factors": []
            })
        
        return {
            "symptoms": symptoms,
            "clarification_needed": True,
            "clarification_questions": [
                "Could you describe your symptoms in more detail?",
                "How long have you been experiencing these symptoms?",
                "On a scale of 1-10, how would you rate the severity?"
            ],
            "confidence": 0.5
        }
    
    def _enhance_with_ontology(self, symptoms: List[Dict]) -> List[StructuredSymptom]:
        """Add ICD-10 and SNOMED codes using ontology."""
        structured = []
        
        for symptom_data in symptoms:
            clinical_term = symptom_data.get("clinical_term", "").lower().replace(" ", "_")
            
            # Get ICD-10 code
            icd10_info = self.ontology.get_icd10_code(clinical_term)
            icd10_code = icd10_info.get("code") if icd10_info else None
            
            # Get body system
            body_system = symptom_data.get("body_system") or self.ontology.get_body_system(clinical_term) or "general"
            
            # Parse severity
            severity_str = symptom_data.get("severity", "moderate").lower()
            try:
                severity = Severity(severity_str)
            except ValueError:
                severity = Severity.MODERATE
            
            structured.append(StructuredSymptom(
                original_text=symptom_data.get("original_text", ""),
                clinical_term=clinical_term.replace("_", " "),
                icd10_code=icd10_code,
                snomed_code=None,  # Can be extended
                body_system=body_system,
                severity=severity,
                duration=symptom_data.get("duration"),
                location=symptom_data.get("location"),
                modifying_factors=symptom_data.get("modifying_factors", [])
            ))
        
        return structured
    
    def _check_red_flags(self, symptoms: List[StructuredSymptom]) -> bool:
        """Check if any symptoms are red flags."""
        for symptom in symptoms:
            clinical_key = symptom.clinical_term.replace(" ", "_")
            if self.ontology.is_red_flag(clinical_key):
                return True
            if symptom.severity in [Severity.SEVERE, Severity.CRITICAL]:
                return True
        return False
    
    def get_clarification_for_symptom(self, symptom: StructuredSymptom) -> List[str]:
        """Generate clarification questions for a specific symptom."""
        questions = []
        
        if not symptom.duration:
            questions.append(f"How long have you been experiencing {symptom.clinical_term}?")
        
        if not symptom.location and symptom.body_system in ["musculoskeletal", "gastrointestinal"]:
            questions.append(f"Can you point to the exact location of the {symptom.clinical_term}?")
        
        if symptom.severity == Severity.MODERATE:
            questions.append(f"Is the {symptom.clinical_term} getting worse, staying the same, or improving?")
        
        if not symptom.modifying_factors:
            questions.append(f"Is there anything that makes the {symptom.clinical_term} better or worse?")
        
        return questions


# Singleton instance
symptom_agent = SymptomDisambiguationAgent()
