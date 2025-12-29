"""
Red-Flag ML Engine
XGBoost/CatBoost-based risk assessment with parallel evaluation.
Triggers immediate escalation if score > 0.6
"""
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
import numpy as np

from ..config import settings
from ..models.schemas import (
    StructuredSymptom, VitalSigns, RiskAssessment, RiskLevel, Severity
)
from ..knowledge_base.medical_ontology import medical_ontology, RED_FLAG_SYMPTOMS

logger = logging.getLogger(__name__)

# Try to import ML libraries
try:
    import xgboost as xgb
    from sklearn.preprocessing import LabelEncoder
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available. Using rule-based risk assessment.")


class RedFlagEngine:
    """
    Machine Learning engine for risk assessment.
    Uses XGBoost classifier with fallback to rule-based scoring.
    """
    
    def __init__(self):
        self.model: Optional[Any] = None
        self.model_path = settings.MODELS_DIR / "red_flag_model.pkl"
        self.threshold = settings.RISK_THRESHOLD
        self.feature_names = [
            "age", "symptom_count", "max_severity", "has_red_flag",
            "duration_days", "heart_rate", "systolic_bp", "diastolic_bp",
            "temperature", "respiratory_rate", "oxygen_saturation",
            "affected_systems_count"
        ]
        
        # Try to load pre-trained model
        self._load_model()
    
    def _load_model(self) -> bool:
        """Load pre-trained model if available."""
        if not XGBOOST_AVAILABLE:
            return False
        
        try:
            if self.model_path.exists():
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info("Loaded pre-trained Red-Flag model")
                return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
        
        return False
    
    def assess_risk(
        self,
        symptoms: List[StructuredSymptom],
        vital_signs: Optional[VitalSigns] = None,
        patient_age: Optional[int] = None
    ) -> RiskAssessment:
        """
        Perform comprehensive risk assessment.
        
        Args:
            symptoms: List of structured symptoms
            vital_signs: Optional vital signs
            patient_age: Optional patient age
            
        Returns:
            Risk assessment with score and recommendations
        """
        # Extract features
        features = self._extract_features(symptoms, vital_signs, patient_age)
        
        # Get risk score
        if self.model and XGBOOST_AVAILABLE:
            risk_score = self._ml_risk_score(features)
        else:
            risk_score = self._rule_based_risk_score(symptoms, vital_signs)
        
        # Determine risk level
        risk_level = self._get_risk_level(risk_score)
        
        # Check for immediate red flags
        red_flags = self._identify_red_flags(symptoms, vital_signs)
        
        # Generate contributing factors
        contributing_factors = self._get_contributing_factors(symptoms, vital_signs, features)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_level, red_flags)
        
        # Check escalation
        escalation_required = risk_score > self.threshold or len(red_flags) > 0
        
        return RiskAssessment(
            risk_score=round(risk_score, 3),
            risk_level=risk_level,
            escalation_required=escalation_required,
            red_flags=red_flags,
            contributing_factors=contributing_factors,
            recommendations=recommendations
        )
    
    def _extract_features(
        self,
        symptoms: List[StructuredSymptom],
        vital_signs: Optional[VitalSigns],
        patient_age: Optional[int]
    ) -> np.ndarray:
        """Extract numerical features for ML model."""
        features = []
        
        # Age
        features.append(patient_age if patient_age else 35)  # Default age
        
        # Symptom count
        features.append(len(symptoms))
        
        # Max severity (0-3 scale)
        severity_map = {Severity.MILD: 0, Severity.MODERATE: 1, Severity.SEVERE: 2, Severity.CRITICAL: 3}
        max_sev = max([severity_map.get(s.severity, 1) for s in symptoms]) if symptoms else 1
        features.append(max_sev)
        
        # Has red flag symptom
        has_red_flag = any(
            medical_ontology.is_red_flag(s.clinical_term.replace(" ", "_"))
            for s in symptoms
        )
        features.append(1 if has_red_flag else 0)
        
        # Duration in days (estimated)
        duration_days = self._estimate_duration_days(symptoms)
        features.append(duration_days)
        
        # Vital signs (with defaults)
        if vital_signs:
            features.append(vital_signs.heart_rate or 75)
            features.append(vital_signs.blood_pressure_systolic or 120)
            features.append(vital_signs.blood_pressure_diastolic or 80)
            features.append(vital_signs.temperature or 37.0)
            features.append(vital_signs.respiratory_rate or 16)
            features.append(vital_signs.oxygen_saturation or 98)
        else:
            features.extend([75, 120, 80, 37.0, 16, 98])  # Normal defaults
        
        # Number of affected body systems
        systems = set(s.body_system for s in symptoms)
        features.append(len(systems))
        
        return np.array(features).reshape(1, -1)
    
    def _estimate_duration_days(self, symptoms: List[StructuredSymptom]) -> float:
        """Estimate duration in days from symptom descriptions."""
        for symptom in symptoms:
            if symptom.duration:
                duration_lower = symptom.duration.lower()
                if "hour" in duration_lower:
                    return 0.04  # ~1 hour
                elif "day" in duration_lower:
                    try:
                        num = int(''.join(filter(str.isdigit, duration_lower)) or 1)
                        return min(num, 365)
                    except:
                        return 1
                elif "week" in duration_lower:
                    try:
                        num = int(''.join(filter(str.isdigit, duration_lower)) or 1)
                        return num * 7
                    except:
                        return 7
                elif "month" in duration_lower:
                    try:
                        num = int(''.join(filter(str.isdigit, duration_lower)) or 1)
                        return num * 30
                    except:
                        return 30
        
        return 3  # Default: 3 days
    
    def _ml_risk_score(self, features: np.ndarray) -> float:
        """Get risk score from ML model."""
        try:
            proba = self.model.predict_proba(features)[0]
            return float(proba[1])  # Probability of high risk
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return self._rule_based_risk_score_from_features(features[0])
    
    def _rule_based_risk_score(
        self,
        symptoms: List[StructuredSymptom],
        vital_signs: Optional[VitalSigns]
    ) -> float:
        """Rule-based risk scoring when ML model unavailable."""
        score = 0.0
        
        # Symptom severity contribution
        for symptom in symptoms:
            if symptom.severity == Severity.CRITICAL:
                score += 0.3
            elif symptom.severity == Severity.SEVERE:
                score += 0.2
            elif symptom.severity == Severity.MODERATE:
                score += 0.1
            else:
                score += 0.05
        
        # Red flag symptoms
        for symptom in symptoms:
            if medical_ontology.is_red_flag(symptom.clinical_term.replace(" ", "_")):
                score += 0.25
        
        # Vital signs contribution
        if vital_signs:
            # Heart rate
            if vital_signs.heart_rate:
                if vital_signs.heart_rate > 120 or vital_signs.heart_rate < 50:
                    score += 0.15
                elif vital_signs.heart_rate > 100 or vital_signs.heart_rate < 60:
                    score += 0.05
            
            # Blood pressure
            if vital_signs.blood_pressure_systolic:
                if vital_signs.blood_pressure_systolic > 180 or vital_signs.blood_pressure_systolic < 90:
                    score += 0.15
            
            # Temperature
            if vital_signs.temperature:
                if vital_signs.temperature > 39.5 or vital_signs.temperature < 35.5:
                    score += 0.15
                elif vital_signs.temperature > 38.5:
                    score += 0.08
            
            # Oxygen saturation
            if vital_signs.oxygen_saturation:
                if vital_signs.oxygen_saturation < 90:
                    score += 0.3
                elif vital_signs.oxygen_saturation < 95:
                    score += 0.15
        
        # Multiple body systems affected
        systems = len(set(s.body_system for s in symptoms))
        if systems >= 3:
            score += 0.1
        
        return min(score, 1.0)
    
    def _rule_based_risk_score_from_features(self, features: np.ndarray) -> float:
        """Rule-based scoring from extracted features array."""
        score = 0.0
        
        # Age risk (very young or elderly)
        age = features[0]
        if age < 5 or age > 70:
            score += 0.1
        
        # Symptom count
        if features[1] > 5:
            score += 0.1
        
        # Severity
        score += features[2] * 0.15
        
        # Red flag
        if features[3] == 1:
            score += 0.25
        
        # Abnormal vitals
        if features[5] > 100 or features[5] < 60:  # Heart rate
            score += 0.1
        if features[8] > 38.5:  # Temperature
            score += 0.1
        if features[10] < 95:  # O2 sat
            score += 0.15
        
        return min(score, 1.0)
    
    def _get_risk_level(self, score: float) -> RiskLevel:
        """Convert numerical score to risk level."""
        if score >= 0.8:
            return RiskLevel.CRITICAL
        elif score >= 0.6:
            return RiskLevel.HIGH
        elif score >= 0.3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _identify_red_flags(
        self,
        symptoms: List[StructuredSymptom],
        vital_signs: Optional[VitalSigns]
    ) -> List[str]:
        """Identify specific red flag concerns."""
        red_flags = []
        
        # Check symptoms
        for symptom in symptoms:
            clinical_key = symptom.clinical_term.replace(" ", "_")
            if medical_ontology.is_red_flag(clinical_key):
                red_flags.append(f"Red flag symptom: {symptom.clinical_term}")
            
            if symptom.severity == Severity.CRITICAL:
                red_flags.append(f"Critical severity: {symptom.clinical_term}")
        
        # Check vital signs
        if vital_signs:
            if vital_signs.oxygen_saturation and vital_signs.oxygen_saturation < 92:
                red_flags.append(f"Low oxygen saturation: {vital_signs.oxygen_saturation}%")
            
            if vital_signs.heart_rate and vital_signs.heart_rate > 130:
                red_flags.append(f"Rapid heart rate: {vital_signs.heart_rate} bpm")
            
            if vital_signs.temperature and vital_signs.temperature > 40:
                red_flags.append(f"High fever: {vital_signs.temperature}°C")
            
            if vital_signs.blood_pressure_systolic:
                if vital_signs.blood_pressure_systolic > 180:
                    red_flags.append(f"Dangerously high blood pressure: {vital_signs.blood_pressure_systolic}/{vital_signs.blood_pressure_diastolic}")
                elif vital_signs.blood_pressure_systolic < 90:
                    red_flags.append(f"Low blood pressure: {vital_signs.blood_pressure_systolic}/{vital_signs.blood_pressure_diastolic}")
        
        return red_flags
    
    def _get_contributing_factors(
        self,
        symptoms: List[StructuredSymptom],
        vital_signs: Optional[VitalSigns],
        features: np.ndarray
    ) -> List[Dict[str, float]]:
        """Get contributing factors to risk score."""
        factors = []
        
        # Symptom severity contribution
        severity_map = {Severity.MILD: 0.1, Severity.MODERATE: 0.2, Severity.SEVERE: 0.3, Severity.CRITICAL: 0.4}
        for symptom in symptoms:
            contribution = severity_map.get(symptom.severity, 0.1)
            factors.append({
                "factor": f"Symptom: {symptom.clinical_term}",
                "contribution": contribution
            })
        
        # Vital signs
        if vital_signs and vital_signs.oxygen_saturation and vital_signs.oxygen_saturation < 95:
            factors.append({
                "factor": "Low oxygen saturation",
                "contribution": 0.2
            })
        
        if vital_signs and vital_signs.temperature and vital_signs.temperature > 38:
            factors.append({
                "factor": "Elevated temperature",
                "contribution": 0.1
            })
        
        return factors
    
    def _generate_recommendations(
        self,
        risk_level: RiskLevel,
        red_flags: List[str]
    ) -> List[str]:
        """Generate recommendations based on risk level."""
        recommendations = []
        
        if risk_level == RiskLevel.CRITICAL or red_flags:
            recommendations.extend([
                "⚠️ SEEK IMMEDIATE MEDICAL ATTENTION",
                "Call emergency services (112) or go to nearest emergency room",
                "Do not drive yourself - have someone take you or call ambulance",
                "If possible, bring a list of current medications"
            ])
        elif risk_level == RiskLevel.HIGH:
            recommendations.extend([
                "Consult a doctor within the next few hours",
                "Consider visiting an urgent care center",
                "Monitor symptoms closely for any worsening",
                "Avoid strenuous activities"
            ])
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.extend([
                "Schedule an appointment with your doctor",
                "Monitor symptoms and note any changes",
                "Rest and stay hydrated",
                "Return if symptoms worsen"
            ])
        else:
            recommendations.extend([
                "Continue monitoring your symptoms",
                "Try home remedies and rest",
                "Consult a doctor if symptoms persist beyond 3-5 days",
                "Stay hydrated and get adequate rest"
            ])
        
        return recommendations


# Singleton instance
risk_engine = RedFlagEngine()
