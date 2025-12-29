"""
Report Generation Module
Generates Clinician (technical) and Patient (simplified) reports.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import logging

from ..config import settings
from ..utils.gemini_client import gemini_client
from ..models.schemas import (
    StructuredSymptom, ClinicalAssessment, RiskAssessment,
    ClinicianReport, PatientReport, PersonalizedRecommendation
)

logger = logging.getLogger(__name__)


PATIENT_REPORT_PROMPT = """You are a medical communication specialist. Your task is to translate a technical clinical assessment into simple, easy-to-understand language for a patient.

RULES:
1. Use simple, everyday language - avoid medical jargon
2. Be reassuring but honest
3. Clearly explain what the symptoms might mean
4. Give clear, actionable advice
5. Include warning signs to watch for
6. Be culturally sensitive for Indian patients

Technical Assessment:
{assessment}

Risk Level: {risk_level}

Create a patient-friendly summary that includes:
1. A brief summary of their concerns (2-3 sentences)
2. What we found (simple explanation)
3. What they should do next (clear steps)
4. Warning signs that mean they should seek immediate help

Keep the language warm, supportive, and easy to understand. Use "you" and "your" to make it personal."""


class ReportGenerator:
    """
    Generates comprehensive medical reports for clinicians and simplified reports for patients.
    """
    
    def __init__(self):
        self.gemini = gemini_client
        self.reports_dir = settings.DATA_DIR / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_clinician_report(
        self,
        symptoms: List[StructuredSymptom],
        assessment: ClinicalAssessment,
        risk_assessment: RiskAssessment,
        patient_id: Optional[str] = None
    ) -> ClinicianReport:
        """
        Generate a technical report for healthcare professionals.
        
        Args:
            symptoms: Structured symptoms
            assessment: Clinical assessment
            risk_assessment: Risk assessment
            patient_id: Optional patient identifier
            
        Returns:
            Clinician-facing technical report
        """
        report_id = f"CLN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
        
        # Extract ICD-10 codes
        icd10_codes = [s.icd10_code for s in symptoms if s.icd10_code]
        
        # Compile recommendations from assessment and risk
        recommendations = assessment.recommended_actions.copy()
        recommendations.extend(risk_assessment.recommendations)
        
        # Get STW guidelines
        stw_guidelines = assessment.stw_references.copy()
        
        report = ClinicianReport(
            report_id=report_id,
            generated_at=datetime.now(),
            patient_id=patient_id,
            symptoms=symptoms,
            clinical_assessment=assessment,
            risk_assessment=risk_assessment,
            stw_guidelines=stw_guidelines,
            icd10_codes=list(set(icd10_codes)),
            recommendations=list(set(recommendations))
        )
        
        # Save report
        self._save_report(report_id, report.dict(), "clinician")
        
        logger.info(f"Generated clinician report: {report_id}")
        return report
    
    def generate_patient_report(
        self,
        symptoms: List[StructuredSymptom],
        assessment: ClinicalAssessment,
        risk_assessment: RiskAssessment,
        personalized_recommendations: Optional[List[PersonalizedRecommendation]] = None
    ) -> PatientReport:
        """
        Generate a simplified report for patients.
        
        Args:
            symptoms: Structured symptoms
            assessment: Clinical assessment
            risk_assessment: Risk assessment
            personalized_recommendations: Culturally adapted recommendations
            
        Returns:
            Patient-friendly report
        """
        report_id = f"PAT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
        
        # Prepare assessment summary for LLM
        assessment_summary = self._prepare_assessment_summary(symptoms, assessment, risk_assessment)
        
        # Generate patient-friendly content using LLM
        try:
            patient_content = self._generate_patient_content(
                assessment_summary, 
                risk_assessment.risk_level.value
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            patient_content = self._fallback_patient_content(symptoms, assessment, risk_assessment)
        
        # Get recommendations
        if personalized_recommendations:
            recommendations = [r.adapted_recommendation for r in personalized_recommendations]
        else:
            recommendations = risk_assessment.recommendations
        
        # Generate warning signs
        warning_signs = self._generate_warning_signs(symptoms, risk_assessment)
        
        # Determine when to seek help
        when_to_seek_help = self._generate_seek_help_guidance(risk_assessment)
        
        report = PatientReport(
            report_id=report_id,
            generated_at=datetime.now(),
            summary=patient_content.get("summary", "Please consult a healthcare provider for a complete assessment."),
            what_you_told_us=patient_content.get("what_you_told_us", self._summarize_symptoms(symptoms)),
            our_assessment=patient_content.get("our_assessment", assessment.chief_complaint),
            recommendations=recommendations[:5],  # Top 5 recommendations
            warning_signs=warning_signs,
            when_to_seek_help=when_to_seek_help
        )
        
        # Save report
        self._save_report(report_id, report.dict(), "patient")
        
        logger.info(f"Generated patient report: {report_id}")
        return report
    
    def _prepare_assessment_summary(
        self,
        symptoms: List[StructuredSymptom],
        assessment: ClinicalAssessment,
        risk_assessment: RiskAssessment
    ) -> str:
        """Prepare a summary of the assessment for LLM processing."""
        symptom_list = ", ".join([s.clinical_term for s in symptoms])
        
        differential_summary = ""
        for dx in assessment.differential_diagnoses[:3]:
            condition = dx.get("condition", "Unknown")
            likelihood = dx.get("likelihood", "unknown")
            differential_summary += f"- {condition} (likelihood: {likelihood})\n"
        
        summary = f"""
Symptoms: {symptom_list}

Chief Complaint: {assessment.chief_complaint}

History: {assessment.history_of_present_illness}

Possible Conditions:
{differential_summary}

Risk Level: {risk_assessment.risk_level.value}
Risk Score: {risk_assessment.risk_score}

Red Flags: {', '.join(risk_assessment.red_flags) if risk_assessment.red_flags else 'None identified'}

Recommended Actions: {', '.join(assessment.recommended_actions[:3])}

Urgency: {assessment.urgency_level}
"""
        return summary
    
    def _generate_patient_content(self, assessment_summary: str, risk_level: str) -> Dict[str, str]:
        """Use LLM to generate patient-friendly content."""
        prompt = PATIENT_REPORT_PROMPT.format(
            assessment=assessment_summary,
            risk_level=risk_level
        )
        
        response = self.gemini.generate(
            prompt=prompt,
            temperature=0.5,
            max_tokens=1024
        )
        
        # Parse the response into sections
        content = {
            "summary": "",
            "what_you_told_us": "",
            "our_assessment": ""
        }
        
        # Simple parsing based on content
        lines = response.strip().split('\n')
        current_section = "summary"
        current_text = []
        
        for line in lines:
            line_lower = line.lower().strip()
            if "what you told" in line_lower or "your concerns" in line_lower:
                if current_text:
                    content[current_section] = " ".join(current_text).strip()
                current_section = "what_you_told_us"
                current_text = []
            elif "what we found" in line_lower or "our assessment" in line_lower or "findings" in line_lower:
                if current_text:
                    content[current_section] = " ".join(current_text).strip()
                current_section = "our_assessment"
                current_text = []
            elif "what you should do" in line_lower or "next steps" in line_lower:
                if current_text:
                    content[current_section] = " ".join(current_text).strip()
                break
            else:
                if line.strip():
                    current_text.append(line.strip())
        
        if current_text:
            content[current_section] = " ".join(current_text).strip()
        
        # Ensure we have content
        if not content["summary"]:
            content["summary"] = response[:500] if response else "Assessment complete."
        
        return content
    
    def _fallback_patient_content(
        self,
        symptoms: List[StructuredSymptom],
        assessment: ClinicalAssessment,
        risk_assessment: RiskAssessment
    ) -> Dict[str, str]:
        """Fallback content generation without LLM."""
        symptom_names = [s.clinical_term for s in symptoms]
        
        return {
            "summary": f"You came to us with concerns about {', '.join(symptom_names)}. Based on our assessment, we recommend following the guidance provided below.",
            "what_you_told_us": f"You described experiencing: {', '.join(symptom_names)}.",
            "our_assessment": assessment.chief_complaint or "Please consult with a healthcare provider for a complete assessment."
        }
    
    def _summarize_symptoms(self, symptoms: List[StructuredSymptom]) -> str:
        """Create a simple symptom summary."""
        parts = []
        for s in symptoms:
            part = s.clinical_term
            if s.duration:
                part += f" (for {s.duration})"
            if s.severity:
                part += f" - {s.severity.value}"
            parts.append(part)
        return "; ".join(parts)
    
    def _generate_warning_signs(
        self,
        symptoms: List[StructuredSymptom],
        risk_assessment: RiskAssessment
    ) -> List[str]:
        """Generate warning signs specific to the symptoms."""
        warning_signs = [
            "Sudden worsening of any symptom",
            "New symptoms appearing",
            "Difficulty breathing or shortness of breath",
            "Chest pain or pressure",
            "Confusion or difficulty staying awake",
            "High fever (above 103°F/39.5°C)",
            "Inability to keep fluids down"
        ]
        
        # Add specific warnings based on symptoms
        for symptom in symptoms:
            if "headache" in symptom.clinical_term.lower():
                warning_signs.insert(0, "Sudden, severe headache unlike any before")
            if "chest" in symptom.clinical_term.lower():
                warning_signs.insert(0, "Pain spreading to arm, jaw, or back")
            if "abdominal" in symptom.clinical_term.lower():
                warning_signs.insert(0, "Severe abdominal pain with inability to move")
        
        return warning_signs[:7]  # Return top 7
    
    def _generate_seek_help_guidance(self, risk_assessment: RiskAssessment) -> str:
        """Generate guidance on when to seek help."""
        if risk_assessment.risk_level.value == "critical":
            return "⚠️ SEEK IMMEDIATE MEDICAL ATTENTION. Call 112 or go to the nearest emergency room NOW."
        elif risk_assessment.risk_level.value == "high":
            return "Please consult a doctor within the next few hours. If you notice any warning signs, seek emergency care immediately."
        elif risk_assessment.risk_level.value == "medium":
            return "Schedule an appointment with your doctor within 24-48 hours. Seek emergency care if warning signs develop."
        else:
            return "Monitor your symptoms. If they persist beyond 3-5 days or worsen, consult a healthcare provider."
    
    def _save_report(self, report_id: str, report_data: Dict[str, Any], report_type: str):
        """Save report to file."""
        try:
            filename = f"{report_id}.json"
            filepath = self.reports_dir / report_type / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert datetime objects to strings
            def serialize(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            with open(filepath, 'w') as f:
                json.dump(report_data, f, indent=2, default=serialize)
            
            logger.info(f"Saved report to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a saved report by ID."""
        # Try clinician reports first
        for report_type in ["clinician", "patient"]:
            filepath = self.reports_dir / report_type / f"{report_id}.json"
            if filepath.exists():
                with open(filepath, 'r') as f:
                    return json.load(f)
        
        return None
    
    def format_report_as_text(self, report: PatientReport) -> str:
        """Format patient report as readable text."""
        text = f"""
╔══════════════════════════════════════════════════════════╗
                    HEALTH ASSESSMENT REPORT
╚══════════════════════════════════════════════════════════╝

Report ID: {report.report_id}
Date: {report.generated_at.strftime('%B %d, %Y at %I:%M %p')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 SUMMARY
{report.summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 WHAT YOU TOLD US
{report.what_you_told_us}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 OUR ASSESSMENT
{report.our_assessment}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ RECOMMENDATIONS
"""
        for i, rec in enumerate(report.recommendations, 1):
            text += f"  {i}. {rec}\n"
        
        text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ WARNING SIGNS - Seek immediate help if you experience:
"""
        for sign in report.warning_signs:
            text += f"  • {sign}\n"
        
        text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏥 WHEN TO SEEK HELP
{report.when_to_seek_help}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DISCLAIMER: This report is for informational purposes only and 
does not constitute medical advice. Please consult a qualified 
healthcare professional for proper diagnosis and treatment.

"""
        return text


# Singleton instance
report_generator = ReportGenerator()
