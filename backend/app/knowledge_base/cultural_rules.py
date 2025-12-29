"""
Cultural Rules for Indian Context
Provides cultural alignment and personalization rules for lifestyle recommendations.
"""
from typing import Dict, List, Optional


# Regional Dietary Preferences in India
REGIONAL_DIETS: Dict[str, Dict[str, any]] = {
    "north_india": {
        "typical_foods": ["roti", "dal", "sabzi", "paneer", "curd", "lassi"],
        "vegetarian_common": True,
        "fasting_days": ["Tuesday", "Thursday", "Ekadashi"],
        "avoid_suggestions": ["beef"],
        "preferred_cooking": ["tandoor", "pressure cooking", "tadka"],
    },
    "south_india": {
        "typical_foods": ["rice", "sambar", "rasam", "idli", "dosa", "coconut chutney"],
        "vegetarian_common": True,
        "fasting_days": ["Pournami", "Amavasya"],
        "avoid_suggestions": ["beef"],
        "preferred_cooking": ["steaming", "tempering", "coconut oil"],
    },
    "east_india": {
        "typical_foods": ["rice", "fish", "mustard oil dishes", "mishti doi"],
        "vegetarian_common": False,
        "fasting_days": ["Ekadashi", "Puja days"],
        "avoid_suggestions": [],
        "preferred_cooking": ["steaming", "mustard oil"],
    },
    "west_india": {
        "typical_foods": ["roti", "dal", "dhokla", "thepla", "khichdi"],
        "vegetarian_common": True,
        "fasting_days": ["Monday", "Ekadashi"],
        "avoid_suggestions": ["beef", "non-veg for many"],
        "preferred_cooking": ["steaming", "baking", "minimal oil"],
    },
    "central_india": {
        "typical_foods": ["roti", "dal", "bafla", "poha"],
        "vegetarian_common": True,
        "fasting_days": ["Tuesday", "Navratri"],
        "avoid_suggestions": ["beef"],
        "preferred_cooking": ["traditional cooking"],
    },
}


# Festival Dietary Considerations
FESTIVAL_CONSIDERATIONS: Dict[str, Dict[str, any]] = {
    "navratri": {
        "duration_days": 9,
        "dietary_restrictions": ["no grains", "no onion", "no garlic", "fasting common"],
        "allowed_foods": ["fruits", "milk", "kuttu flour", "sabudana", "potatoes"],
        "health_note": "May need iron supplements during long fasting",
    },
    "ramadan": {
        "duration_days": 30,
        "dietary_restrictions": ["no food/water during daylight"],
        "allowed_foods": ["dates for iftar", "light meals"],
        "health_note": "Stay hydrated during suhoor, avoid heavy meals",
    },
    "ekadashi": {
        "duration_days": 1,
        "dietary_restrictions": ["no grains", "no beans"],
        "allowed_foods": ["fruits", "milk", "nuts"],
        "health_note": "Monthly occurrence, plan medications accordingly",
    },
    "shravan": {
        "duration_days": 30,
        "dietary_restrictions": ["no non-veg for many"],
        "allowed_foods": ["vegetarian only"],
        "health_note": "Good for digestive health during monsoon",
    },
}


# Traditional Remedy Acknowledgments
TRADITIONAL_REMEDIES: Dict[str, Dict[str, any]] = {
    "cold_cough": {
        "common_remedies": ["turmeric milk (haldi doodh)", "ginger tea", "tulsi (basil) tea", "honey with warm water"],
        "scientific_backing": "Some evidence for anti-inflammatory properties",
        "safety_note": "Safe as complementary, but seek medical care if symptoms persist >7 days",
    },
    "digestive_issues": {
        "common_remedies": ["ajwain water", "jeera water", "hing (asafoetida)", "buttermilk"],
        "scientific_backing": "Carminative properties recognized",
        "safety_note": "Avoid if specific allergies; consult doctor for persistent issues",
    },
    "fever": {
        "common_remedies": ["tulsi decoction", "giloy", "neem water"],
        "scientific_backing": "Immunomodulatory properties studied",
        "safety_note": "Monitor temperature; seek care if >103°F or lasting >3 days",
    },
    "skin_issues": {
        "common_remedies": ["neem paste", "turmeric paste", "aloe vera"],
        "scientific_backing": "Antimicrobial and anti-inflammatory properties",
        "safety_note": "Patch test first; avoid on open wounds",
    },
    "stress_anxiety": {
        "common_remedies": ["ashwagandha", "brahmi", "meditation", "pranayama"],
        "scientific_backing": "Adaptogenic properties studied",
        "safety_note": "May interact with certain medications; consult doctor",
    },
}


# Language-specific Communication Styles
COMMUNICATION_STYLES: Dict[str, Dict[str, any]] = {
    "formal": {
        "greeting": "Namaste, I am here to assist you with your health concerns.",
        "tone": "professional",
        "use_medical_terms": True,
        "explanation_level": "detailed",
    },
    "friendly": {
        "greeting": "Hello! Let me help you understand your health better.",
        "tone": "warm",
        "use_medical_terms": False,
        "explanation_level": "simplified",
    },
    "elder_respectful": {
        "greeting": "Pranam, I am here to help with your health questions.",
        "tone": "respectful",
        "use_medical_terms": False,
        "explanation_level": "patient",
        "use_ji_suffix": True,
    },
}


# Lifestyle Recommendation Adaptations
LIFESTYLE_ADAPTATIONS: Dict[str, Dict[str, List[str]]] = {
    "exercise": {
        "standard": ["30 minutes of moderate exercise daily", "walking", "jogging"],
        "indian_alternatives": ["yoga asanas", "morning walk in park", "surya namaskar", "pranayama", "evening walk after dinner"],
        "elderly": ["gentle stretching", "chair yoga", "slow walking", "breathing exercises"],
    },
    "stress_relief": {
        "standard": ["meditation", "deep breathing", "regular breaks"],
        "indian_alternatives": ["pranayama", "Om chanting", "temple/spiritual visits", "devotional music", "early morning walks"],
        "elderly": ["bhajans", "prayer", "family time", "gardening"],
    },
    "diet": {
        "standard": ["balanced diet", "more vegetables", "less processed food"],
        "indian_alternatives": ["include seasonal vegetables", "dal-chawal-sabzi combination", "fresh curd/buttermilk", "home-cooked meals"],
        "elderly": ["easily digestible foods", "warm meals", "khichdi", "daliya"],
    },
    "sleep": {
        "standard": ["7-8 hours sleep", "regular schedule"],
        "indian_alternatives": ["early to bed (by 10 PM)", "light dinner", "avoid TV before sleep", "chamomile/chameli tea"],
        "elderly": ["afternoon rest (30 min)", "warm milk before bed", "minimal screen time"],
    },
}


class CulturalRules:
    """Cultural adaptation rules for personalized health recommendations."""
    
    @staticmethod
    def get_regional_diet(region: str) -> Dict[str, any]:
        """Get dietary preferences for a region."""
        # Normalize region name
        region_key = region.lower().replace(" ", "_").replace("-", "_")
        
        # Map common region names
        region_mapping = {
            "delhi": "north_india",
            "punjab": "north_india",
            "uttar_pradesh": "north_india",
            "up": "north_india",
            "haryana": "north_india",
            "rajasthan": "north_india",
            "tamil_nadu": "south_india",
            "tn": "south_india",
            "karnataka": "south_india",
            "kerala": "south_india",
            "andhra_pradesh": "south_india",
            "ap": "south_india",
            "telangana": "south_india",
            "west_bengal": "east_india",
            "wb": "east_india",
            "odisha": "east_india",
            "assam": "east_india",
            "maharashtra": "west_india",
            "gujarat": "west_india",
            "goa": "west_india",
            "madhya_pradesh": "central_india",
            "mp": "central_india",
            "chhattisgarh": "central_india",
        }
        
        mapped_region = region_mapping.get(region_key, region_key)
        return REGIONAL_DIETS.get(mapped_region, REGIONAL_DIETS["north_india"])
    
    @staticmethod
    def get_festival_considerations(festival: str) -> Optional[Dict[str, any]]:
        """Get health considerations for a festival period."""
        festival_key = festival.lower().replace(" ", "_")
        return FESTIVAL_CONSIDERATIONS.get(festival_key)
    
    @staticmethod
    def get_traditional_remedy(condition: str) -> Optional[Dict[str, any]]:
        """Get traditional remedy information for a condition."""
        condition_key = condition.lower().replace(" ", "_")
        
        # Map common conditions
        condition_mapping = {
            "cold": "cold_cough",
            "cough": "cold_cough",
            "flu": "cold_cough",
            "indigestion": "digestive_issues",
            "acidity": "digestive_issues",
            "gas": "digestive_issues",
            "bloating": "digestive_issues",
            "rash": "skin_issues",
            "itching": "skin_issues",
            "anxiety": "stress_anxiety",
            "stress": "stress_anxiety",
            "tension": "stress_anxiety",
        }
        
        mapped_condition = condition_mapping.get(condition_key, condition_key)
        return TRADITIONAL_REMEDIES.get(mapped_condition)
    
    @staticmethod
    def get_communication_style(style: str) -> Dict[str, any]:
        """Get communication style settings."""
        return COMMUNICATION_STYLES.get(style.lower(), COMMUNICATION_STYLES["friendly"])
    
    @staticmethod
    def adapt_lifestyle_recommendation(
        recommendation_type: str,
        age_group: str = "adult",
        use_indian_context: bool = True
    ) -> List[str]:
        """Get culturally adapted lifestyle recommendations."""
        recommendations = LIFESTYLE_ADAPTATIONS.get(recommendation_type.lower(), {})
        
        if age_group == "elderly" or age_group == "senior":
            return recommendations.get("elderly", recommendations.get("standard", []))
        elif use_indian_context:
            return recommendations.get("indian_alternatives", recommendations.get("standard", []))
        else:
            return recommendations.get("standard", [])
    
    @staticmethod
    def is_fasting_day(day: str, region: str = "north_india") -> bool:
        """Check if a day is typically a fasting day in a region."""
        regional_diet = CulturalRules.get_regional_diet(region)
        fasting_days = regional_diet.get("fasting_days", [])
        return day.capitalize() in fasting_days
    
    @staticmethod
    def get_vegetarian_alternatives(foods: List[str]) -> List[str]:
        """Get vegetarian alternatives for food recommendations."""
        alternatives = {
            "chicken": "paneer or tofu",
            "fish": "nuts and seeds",
            "eggs": "paneer or soy chunks",
            "meat": "legumes and dal",
            "beef": "mushrooms or jackfruit",
            "pork": "soy products",
        }
        
        result = []
        for food in foods:
            food_lower = food.lower()
            if food_lower in alternatives:
                result.append(alternatives[food_lower])
            else:
                result.append(food)
        
        return result


# Export singleton
cultural_rules = CulturalRules()
