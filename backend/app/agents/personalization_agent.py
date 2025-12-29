"""
Personalization Agent
Adapts actionable lifestyle recommendations based on cultural context and user preferences.
Implements Cultural Alignment Rules for the Indian context.
"""
from typing import List, Dict, Any, Optional
import logging

from ..knowledge_base.cultural_rules import cultural_rules, LIFESTYLE_ADAPTATIONS
from ..models.schemas import UserPreferences, PersonalizedRecommendation

logger = logging.getLogger(__name__)


class PersonalizationAgent:
    """
    Agent for adapting health recommendations to cultural context and user preferences.
    """
    
    def __init__(self):
        self.cultural_rules = cultural_rules
        self.default_preferences = UserPreferences(
            language="en",
            region="India",
            dietary_preferences=["vegetarian_options"],
            cultural_considerations=[],
            communication_style="friendly"
        )
    
    def personalize_recommendations(
        self,
        recommendations: List[str],
        user_preferences: Optional[UserPreferences] = None
    ) -> List[PersonalizedRecommendation]:
        """
        Personalize a list of recommendations for the user.
        
        Args:
            recommendations: Original recommendations
            user_preferences: User's preferences
            
        Returns:
            List of personalized recommendations
        """
        preferences = user_preferences or self.default_preferences
        personalized = []
        
        for recommendation in recommendations:
            adapted = self._adapt_recommendation(recommendation, preferences)
            personalized.append(adapted)
        
        return personalized
    
    def _adapt_recommendation(
        self,
        recommendation: str,
        preferences: UserPreferences
    ) -> PersonalizedRecommendation:
        """Adapt a single recommendation to user preferences."""
        original = recommendation
        adapted = recommendation
        cultural_notes = None
        
        # Check for dietary adaptations
        if any(diet in recommendation.lower() for diet in ["meat", "chicken", "fish", "egg", "beef", "pork"]):
            if "vegetarian" in preferences.dietary_preferences or "veg" in preferences.dietary_preferences:
                adapted = self._make_vegetarian(recommendation)
                cultural_notes = "Adapted for vegetarian diet preference"
        
        # Check for exercise recommendations
        if any(word in recommendation.lower() for word in ["exercise", "workout", "gym", "fitness"]):
            adapted = self._adapt_exercise(recommendation, preferences.region)
            cultural_notes = "Adapted to include traditional Indian exercise options"
        
        # Check for stress/mental health recommendations
        if any(word in recommendation.lower() for word in ["stress", "anxiety", "relax", "mental"]):
            adapted = self._adapt_stress_relief(recommendation, preferences.region)
            cultural_notes = "Adapted with culturally relevant stress management techniques"
        
        # Check for dietary/nutrition advice
        if any(word in recommendation.lower() for word in ["diet", "eat", "food", "nutrition"]):
            adapted = self._adapt_diet(recommendation, preferences.region)
        
        return PersonalizedRecommendation(
            original_recommendation=original,
            adapted_recommendation=adapted,
            cultural_notes=cultural_notes
        )
    
    def _make_vegetarian(self, recommendation: str) -> str:
        """Convert recommendation to vegetarian-friendly."""
        replacements = {
            "chicken": "paneer or soy chunks",
            "fish": "omega-3 rich seeds (flax, chia) or walnuts",
            "meat": "legumes and pulses",
            "eggs": "paneer, tofu, or sprouted lentils",
            "beef": "mushrooms or jackfruit",
            "pork": "textured vegetable protein"
        }
        
        result = recommendation
        for original, replacement in replacements.items():
            if original in result.lower():
                result = result.replace(original, replacement)
                result = result.replace(original.capitalize(), replacement)
        
        return result
    
    def _adapt_exercise(self, recommendation: str, region: str) -> str:
        """Adapt exercise recommendations to include Indian options."""
        indian_options = self.cultural_rules.adapt_lifestyle_recommendation(
            "exercise", 
            use_indian_context=True
        )
        
        additions = f" Consider Indian alternatives like {', '.join(indian_options[:3])}."
        return recommendation + additions
    
    def _adapt_stress_relief(self, recommendation: str, region: str) -> str:
        """Adapt stress relief recommendations."""
        indian_options = self.cultural_rules.adapt_lifestyle_recommendation(
            "stress_relief",
            use_indian_context=True
        )
        
        additions = f" You might also try {', '.join(indian_options[:3])}."
        return recommendation + additions
    
    def _adapt_diet(self, recommendation: str, region: str) -> str:
        """Adapt dietary recommendations to regional preferences."""
        regional_diet = self.cultural_rules.get_regional_diet(region)
        typical_foods = regional_diet.get("typical_foods", [])[:3]
        
        if typical_foods:
            additions = f" Regional options include: {', '.join(typical_foods)}."
            return recommendation + additions
        
        return recommendation
    
    def get_traditional_remedy_info(self, condition: str) -> Dict[str, Any]:
        """
        Get traditional remedy information for a condition with safety notes.
        
        Args:
            condition: Medical condition
            
        Returns:
            Traditional remedy information with safety guidance
        """
        remedy_info = self.cultural_rules.get_traditional_remedy(condition)
        
        if remedy_info:
            return {
                "found": True,
                "condition": condition,
                "traditional_remedies": remedy_info.get("common_remedies", []),
                "scientific_backing": remedy_info.get("scientific_backing", "Limited evidence"),
                "safety_note": remedy_info.get("safety_note", "Consult healthcare provider before use"),
                "disclaimer": "Traditional remedies should complement, not replace, professional medical advice."
            }
        
        return {
            "found": False,
            "condition": condition,
            "message": "No specific traditional remedy information available.",
            "disclaimer": "Please consult a healthcare provider for medical advice."
        }
    
    def adapt_for_elderly(
        self,
        recommendations: List[str],
        user_preferences: Optional[UserPreferences] = None
    ) -> List[PersonalizedRecommendation]:
        """
        Specially adapt recommendations for elderly patients.
        
        Args:
            recommendations: Original recommendations
            user_preferences: User preferences
            
        Returns:
            Adapted recommendations for elderly
        """
        preferences = user_preferences or self.default_preferences
        personalized = []
        
        for recommendation in recommendations:
            adapted = recommendation
            
            # Adapt exercise for elderly
            if any(word in recommendation.lower() for word in ["exercise", "physical activity", "workout"]):
                elderly_exercises = self.cultural_rules.adapt_lifestyle_recommendation(
                    "exercise", 
                    age_group="elderly"
                )
                adapted = f"Gentle activity recommended: {', '.join(elderly_exercises[:2])}. {recommendation}"
            
            # Adapt diet for elderly
            if any(word in recommendation.lower() for word in ["diet", "food", "eat"]):
                elderly_diet = self.cultural_rules.adapt_lifestyle_recommendation(
                    "diet",
                    age_group="elderly"
                )
                adapted = f"{recommendation} Consider easily digestible options like {', '.join(elderly_diet[:2])}."
            
            # Adapt sleep recommendations
            if "sleep" in recommendation.lower():
                elderly_sleep = self.cultural_rules.adapt_lifestyle_recommendation(
                    "sleep",
                    age_group="elderly"
                )
                adapted = f"{recommendation} {' '.join(elderly_sleep[:2])}."
            
            personalized.append(PersonalizedRecommendation(
                original_recommendation=recommendation,
                adapted_recommendation=adapted,
                cultural_notes="Adapted for elderly patient"
            ))
        
        return personalized
    
    def get_communication_greeting(self, style: str = "friendly") -> str:
        """Get appropriate greeting based on communication style."""
        comm_style = self.cultural_rules.get_communication_style(style)
        return comm_style.get("greeting", "Hello! How can I help you today?")
    
    def check_fasting_considerations(
        self,
        day: str,
        region: str,
        recommendations: List[str]
    ) -> Dict[str, Any]:
        """
        Check if it's a common fasting day and adjust recommendations.
        
        Args:
            day: Day of the week
            region: User's region
            recommendations: Current recommendations
            
        Returns:
            Fasting-aware recommendations
        """
        is_fasting = self.cultural_rules.is_fasting_day(day, region)
        
        if is_fasting:
            adjusted = []
            for rec in recommendations:
                if any(word in rec.lower() for word in ["eat", "food", "diet", "meal"]):
                    adjusted.append(f"Note: Today may be a traditional fasting day in your region. {rec}")
                else:
                    adjusted.append(rec)
            
            return {
                "is_fasting_day": True,
                "adjusted_recommendations": adjusted,
                "note": "Traditional fasting day detected. Dietary recommendations may need adjustment."
            }
        
        return {
            "is_fasting_day": False,
            "recommendations": recommendations
        }
    
    def get_regional_health_tips(self, region: str) -> List[str]:
        """Get region-specific health tips."""
        regional_diet = self.cultural_rules.get_regional_diet(region)
        
        tips = [
            f"Include traditional healthy foods like {', '.join(regional_diet.get('typical_foods', [])[:3])} in your diet.",
            "Stay hydrated with water, buttermilk, or coconut water.",
            "Practice traditional exercises like yoga and walking.",
        ]
        
        if regional_diet.get("vegetarian_common"):
            tips.append("Ensure adequate protein intake through dal, paneer, and legumes.")
        
        return tips


# Singleton instance
personalization_agent = PersonalizationAgent()
