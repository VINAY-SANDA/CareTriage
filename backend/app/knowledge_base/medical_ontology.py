"""
Medical Ontology
Contains ICD-10, SNOMED-CT mappings, and medical terminology rules.
"""
from typing import Dict, List, Optional, Tuple


# ICD-10 Code Mappings for Common Symptoms
ICD10_SYMPTOM_CODES: Dict[str, Dict[str, str]] = {
    # Head & Neurological
    "headache": {"code": "R51", "description": "Headache"},
    "migraine": {"code": "G43.9", "description": "Migraine, unspecified"},
    "dizziness": {"code": "R42", "description": "Dizziness and giddiness"},
    "vertigo": {"code": "R42", "description": "Dizziness and giddiness"},
    "confusion": {"code": "R41.0", "description": "Disorientation, unspecified"},
    "memory_loss": {"code": "R41.3", "description": "Other amnesia"},
    "seizure": {"code": "R56.9", "description": "Unspecified convulsions"},
    "fainting": {"code": "R55", "description": "Syncope and collapse"},
    
    # Respiratory
    "cough": {"code": "R05", "description": "Cough"},
    "shortness_of_breath": {"code": "R06.0", "description": "Dyspnea"},
    "difficulty_breathing": {"code": "R06.0", "description": "Dyspnea"},
    "wheezing": {"code": "R06.2", "description": "Wheezing"},
    "chest_congestion": {"code": "R09.89", "description": "Other specified symptoms involving respiratory system"},
    "sore_throat": {"code": "J02.9", "description": "Acute pharyngitis, unspecified"},
    "runny_nose": {"code": "J00", "description": "Acute nasopharyngitis"},
    
    # Cardiovascular
    "chest_pain": {"code": "R07.9", "description": "Chest pain, unspecified"},
    "palpitations": {"code": "R00.2", "description": "Palpitations"},
    "rapid_heartbeat": {"code": "R00.0", "description": "Tachycardia, unspecified"},
    "slow_heartbeat": {"code": "R00.1", "description": "Bradycardia, unspecified"},
    "swelling_legs": {"code": "R60.0", "description": "Localized edema"},
    "high_blood_pressure": {"code": "R03.0", "description": "Elevated blood pressure"},
    
    # Gastrointestinal
    "abdominal_pain": {"code": "R10.9", "description": "Unspecified abdominal pain"},
    "stomach_ache": {"code": "R10.9", "description": "Unspecified abdominal pain"},
    "nausea": {"code": "R11.0", "description": "Nausea"},
    "vomiting": {"code": "R11.1", "description": "Vomiting"},
    "diarrhea": {"code": "R19.7", "description": "Diarrhea, unspecified"},
    "constipation": {"code": "K59.0", "description": "Constipation"},
    "bloating": {"code": "R14.0", "description": "Abdominal distension"},
    "heartburn": {"code": "R12", "description": "Heartburn"},
    "loss_of_appetite": {"code": "R63.0", "description": "Anorexia"},
    "blood_in_stool": {"code": "K92.1", "description": "Melena"},
    
    # Musculoskeletal
    "back_pain": {"code": "M54.9", "description": "Dorsalgia, unspecified"},
    "joint_pain": {"code": "M25.50", "description": "Pain in unspecified joint"},
    "muscle_pain": {"code": "M79.1", "description": "Myalgia"},
    "neck_pain": {"code": "M54.2", "description": "Cervicalgia"},
    "weakness": {"code": "R53.1", "description": "Weakness"},
    "fatigue": {"code": "R53.83", "description": "Other fatigue"},
    
    # Skin
    "rash": {"code": "R21", "description": "Rash and other nonspecific skin eruption"},
    "itching": {"code": "L29.9", "description": "Pruritus, unspecified"},
    "skin_swelling": {"code": "R22.9", "description": "Localized swelling, unspecified"},
    "bruising": {"code": "R23.3", "description": "Spontaneous ecchymoses"},
    
    # General/Systemic
    "fever": {"code": "R50.9", "description": "Fever, unspecified"},
    "chills": {"code": "R68.83", "description": "Chills"},
    "night_sweats": {"code": "R61", "description": "Generalized hyperhidrosis"},
    "weight_loss": {"code": "R63.4", "description": "Abnormal weight loss"},
    "weight_gain": {"code": "R63.5", "description": "Abnormal weight gain"},
    "malaise": {"code": "R53.81", "description": "Other malaise"},
    
    # Urological
    "painful_urination": {"code": "R30.0", "description": "Dysuria"},
    "frequent_urination": {"code": "R35.0", "description": "Frequency of micturition"},
    "blood_in_urine": {"code": "R31.9", "description": "Hematuria, unspecified"},
    
    # Eyes
    "eye_pain": {"code": "H57.1", "description": "Ocular pain"},
    "blurred_vision": {"code": "H53.8", "description": "Other visual disturbances"},
    "eye_redness": {"code": "H57.8", "description": "Other specified disorders of eye"},
    
    # Mental Health
    "anxiety": {"code": "F41.9", "description": "Anxiety disorder, unspecified"},
    "depression": {"code": "F32.9", "description": "Major depressive disorder, single episode"},
    "insomnia": {"code": "G47.0", "description": "Insomnia"},
    "stress": {"code": "F43.9", "description": "Reaction to severe stress, unspecified"},
}


# Body System Categories
BODY_SYSTEMS: Dict[str, List[str]] = {
    "neurological": ["headache", "migraine", "dizziness", "vertigo", "confusion", "memory_loss", "seizure", "fainting"],
    "respiratory": ["cough", "shortness_of_breath", "difficulty_breathing", "wheezing", "chest_congestion", "sore_throat", "runny_nose"],
    "cardiovascular": ["chest_pain", "palpitations", "rapid_heartbeat", "slow_heartbeat", "swelling_legs", "high_blood_pressure"],
    "gastrointestinal": ["abdominal_pain", "stomach_ache", "nausea", "vomiting", "diarrhea", "constipation", "bloating", "heartburn", "loss_of_appetite", "blood_in_stool"],
    "musculoskeletal": ["back_pain", "joint_pain", "muscle_pain", "neck_pain", "weakness", "fatigue"],
    "dermatological": ["rash", "itching", "skin_swelling", "bruising"],
    "systemic": ["fever", "chills", "night_sweats", "weight_loss", "weight_gain", "malaise"],
    "urological": ["painful_urination", "frequent_urination", "blood_in_urine"],
    "ophthalmological": ["eye_pain", "blurred_vision", "eye_redness"],
    "psychiatric": ["anxiety", "depression", "insomnia", "stress"],
}


# Symptom Severity Indicators
SEVERITY_INDICATORS: Dict[str, List[str]] = {
    "mild": ["slight", "minor", "little", "somewhat", "occasional", "mild", "light"],
    "moderate": ["moderate", "noticeable", "persistent", "recurring", "regular"],
    "severe": ["severe", "intense", "extreme", "unbearable", "excruciating", "worst", "terrible", "awful"],
    "critical": ["sudden onset", "cannot breathe", "crushing", "radiating", "losing consciousness", "unresponsive"],
}


# Duration Keywords
DURATION_PATTERNS: Dict[str, str] = {
    "acute": "less than 1 week",
    "subacute": "1-4 weeks",
    "chronic": "more than 4 weeks",
}


# Red Flag Symptoms (require immediate attention)
RED_FLAG_SYMPTOMS: List[str] = [
    "chest_pain",
    "difficulty_breathing",
    "shortness_of_breath",
    "seizure",
    "fainting",
    "blood_in_stool",
    "blood_in_urine",
    "confusion",
    "severe_headache",
    "high_fever",
    "rapid_heartbeat",
    "unresponsive",
]


# Symptom Synonyms for Natural Language Understanding
SYMPTOM_SYNONYMS: Dict[str, List[str]] = {
    "headache": ["head hurts", "head pain", "head ache", "throbbing head", "splitting headache"],
    "stomach_ache": ["stomach hurts", "tummy ache", "belly pain", "abdominal discomfort", "stomach cramps"],
    "fever": ["temperature", "feeling hot", "burning up", "feverish", "high temperature"],
    "cough": ["coughing", "dry cough", "wet cough", "hacking cough", "persistent cough"],
    "shortness_of_breath": ["breathless", "can't breathe", "hard to breathe", "gasping", "out of breath", "breathing difficulty"],
    "chest_pain": ["chest hurts", "chest discomfort", "chest pressure", "chest tightness", "pain in chest"],
    "nausea": ["feeling sick", "queasy", "want to vomit", "upset stomach", "nauseated"],
    "vomiting": ["throwing up", "being sick", "puking", "regurgitating"],
    "diarrhea": ["loose stools", "watery stools", "running stomach", "loose motions"],
    "fatigue": ["tired", "exhausted", "no energy", "worn out", "drained", "lethargic"],
    "dizziness": ["dizzy", "light-headed", "unsteady", "room spinning", "woozy"],
    "back_pain": ["back hurts", "backache", "lower back pain", "upper back pain", "spine pain"],
    "sore_throat": ["throat pain", "throat hurts", "scratchy throat", "burning throat"],
}


class MedicalOntology:
    """Medical ontology helper class for symptom mapping and classification."""
    
    @staticmethod
    def get_icd10_code(symptom: str) -> Optional[Dict[str, str]]:
        """Get ICD-10 code for a symptom."""
        symptom_key = symptom.lower().replace(" ", "_").replace("-", "_")
        return ICD10_SYMPTOM_CODES.get(symptom_key)
    
    @staticmethod
    def get_body_system(symptom: str) -> Optional[str]:
        """Determine which body system a symptom belongs to."""
        symptom_key = symptom.lower().replace(" ", "_").replace("-", "_")
        for system, symptoms in BODY_SYSTEMS.items():
            if symptom_key in symptoms:
                return system
        return "general"
    
    @staticmethod
    def classify_severity(description: str) -> str:
        """Classify symptom severity based on description."""
        description_lower = description.lower()
        
        for severity, indicators in SEVERITY_INDICATORS.items():
            for indicator in indicators:
                if indicator in description_lower:
                    return severity
        
        return "moderate"  # Default
    
    @staticmethod
    def is_red_flag(symptom: str) -> bool:
        """Check if a symptom is a red flag requiring urgent attention."""
        symptom_key = symptom.lower().replace(" ", "_").replace("-", "_")
        return symptom_key in RED_FLAG_SYMPTOMS
    
    @staticmethod
    def normalize_symptom(text: str) -> Optional[str]:
        """Normalize a symptom description to a standard term."""
        text_lower = text.lower().strip()
        
        # Check direct match
        for symptom in ICD10_SYMPTOM_CODES.keys():
            if symptom.replace("_", " ") in text_lower:
                return symptom
        
        # Check synonyms
        for standard_symptom, synonyms in SYMPTOM_SYNONYMS.items():
            for synonym in synonyms:
                if synonym in text_lower:
                    return standard_symptom
        
        return None
    
    @staticmethod
    def get_all_symptoms() -> List[str]:
        """Get list of all known symptoms."""
        return list(ICD10_SYMPTOM_CODES.keys())
    
    @staticmethod
    def get_symptom_info(symptom: str) -> Dict[str, any]:
        """Get comprehensive information about a symptom."""
        symptom_key = symptom.lower().replace(" ", "_").replace("-", "_")
        
        icd10 = ICD10_SYMPTOM_CODES.get(symptom_key, {})
        body_system = MedicalOntology.get_body_system(symptom_key)
        is_urgent = MedicalOntology.is_red_flag(symptom_key)
        
        return {
            "symptom": symptom_key,
            "icd10_code": icd10.get("code"),
            "description": icd10.get("description"),
            "body_system": body_system,
            "is_red_flag": is_urgent,
        }


# Export singleton
medical_ontology = MedicalOntology()
