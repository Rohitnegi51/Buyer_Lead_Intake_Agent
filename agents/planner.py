from typing import Tuple, List
from models.schemas import BuyerRequirements, ValidationResult, LeadStrategy, StrategyType, LeadType, ReasoningStep

class LeadPlanner:
    """
    Determines the overall strategy for handling the lead based on their classification
    and validation results. Uses a deterministic, rule-based approach.
    Generates follow-up questions and reasoning logs explaining the decision.
    """
    def determine_strategy(
        self, 
        reqs: BuyerRequirements, 
        val_res: ValidationResult, 
        lead_type: LeadType, 
        inquiry_text: str = ""
    ) -> Tuple[LeadStrategy, List[ReasoningStep]]:
        
        reasoning_steps = []
        text_lower = inquiry_text.lower()
        
        # 1. Negotiation Advice Check (Special case for leads like 005)
        if "motivation" in text_lower or "lowest price" in text_lower or "desperate" in text_lower or "negotiat" in text_lower:
            reasoning_steps.append(ReasoningStep(step="Planning", decision="Detected negotiation or seller motivation queries. Assigned Negotiation Advice."))
            strategy = LeadStrategy(
                strategy_type=StrategyType.NEGOTIATION_ADVICE,
                recommended_approach="Present matching properties but explicitly state that seller motivation cannot be determined from available MLS data.",
                follow_up_questions=["Would you like me to contact listing agents directly to gauge seller motivation or flexibility?"]
            )
            return strategy, reasoning_steps

        # 2. Expectation Alignment Check
        if val_res.unrealistic_budget:
            reasoning_steps.append(ReasoningStep(step="Planning", decision="Unrealistic budget flagged by Validator. Assigned Expectation Alignment."))
            strategy = LeadStrategy(
                strategy_type=StrategyType.EXPECTATION_ALIGNMENT,
                recommended_approach="Gently educate the buyer on current market prices in their desired neighborhoods before starting the search.",
                follow_up_questions=[
                    f"Given your budget, would you consider slightly smaller properties or exploring nearby neighborhoods?",
                    "Are you flexible on your maximum budget if we find the perfect match?"
                ]
            )
            return strategy, reasoning_steps
        
        # 3. Clarification First Check
        if val_res.missing_information:
            reasoning_steps.append(ReasoningStep(step="Planning", decision="Missing essential requirements flagged by Validator. Assigned Clarification First."))
            
            questions = []
            if not reqs.budget:
                questions.append("What is your maximum budget for this purchase?")
            if not reqs.locations and not reqs.property_types:
                questions.append("Are there any specific neighborhoods, cities, or property types (like Condo or Single Family) you prefer?")
                
            if not questions:
                questions.append("Can you clarify your exact requirements before we begin the search?")
                
            strategy = LeadStrategy(
                strategy_type=StrategyType.CLARIFICATION_FIRST,
                recommended_approach="Ask for the missing key requirements before spending extensive time on property research.",
                follow_up_questions=questions
            )
            return strategy, reasoning_steps

        # 4. Lead Type Based Strategies
        if lead_type == LeadType.INVESTOR:
            reasoning_steps.append(ReasoningStep(step="Planning", decision="Lead type is Investor. Assigned Investment Search."))
            strategy = LeadStrategy(
                strategy_type=StrategyType.INVESTMENT_SEARCH,
                recommended_approach="Focus on ROI, cap rates, and rental potential. Exclude properties with strict HOA rental restrictions.",
                follow_up_questions=["Are you looking for short-term vacation rentals or long-term annual tenants?", "What is your target capitalization rate?"]
            )
            return strategy, reasoning_steps
            
        elif lead_type == LeadType.RELOCATION:
            reasoning_steps.append(ReasoningStep(step="Planning", decision="Lead type is Relocation. Assigned Relocation Assistance."))
            strategy = LeadStrategy(
                strategy_type=StrategyType.RELOCATION_ASSISTANCE,
                recommended_approach="Provide comprehensive neighborhood guides alongside property listings to help them understand the area.",
                follow_up_questions=["Will you be commuting? How far are you willing to travel for work?", "What kind of lifestyle are you looking for in your new neighborhood?"]
            )
            return strategy, reasoning_steps
            
        elif lead_type == LeadType.FAMILY:
            reasoning_steps.append(ReasoningStep(step="Planning", decision="Lead type is Family. Assigned Family Home Search."))
            strategy = LeadStrategy(
                strategy_type=StrategyType.FAMILY_HOME_SEARCH,
                recommended_approach="Prioritize properties in top-rated school districts with family-friendly amenities like parks and large yards.",
                follow_up_questions=["Do you have any specific school districts in mind?", "Is a large backyard or pool a priority for your family?"]
            )
            return strategy, reasoning_steps
            
        elif lead_type == LeadType.LUXURY:
            reasoning_steps.append(ReasoningStep(step="Planning", decision="Lead type is Luxury. Assigned Luxury Search."))
            strategy = LeadStrategy(
                strategy_type=StrategyType.LUXURY_SEARCH,
                recommended_approach="Focus on premium properties, exclusive neighborhoods, and high-end amenities like private docks, wine cellars, and concierge services.",
                follow_up_questions=["Are you interested in exclusive gated communities or high-rise luxury penthouses?", "Do you require waterfront access or private dockage?"]
            )
            return strategy, reasoning_steps
            
        elif lead_type == LeadType.ACCESSIBILITY:
            reasoning_steps.append(ReasoningStep(step="Planning", decision="Lead type is Accessibility. Assigned Accessibility-Oriented Search."))
            strategy = LeadStrategy(
                strategy_type=StrategyType.ACCESSIBILITY_SEARCH,
                recommended_approach="Strictly filter for single-story homes or buildings with elevators. Verify wheelchair accessibility where applicable.",
                follow_up_questions=["Do you need zero-step entries or roll-in showers?", "Are there any specific medical facility proximity requirements?"]
            )
            return strategy, reasoning_steps
            
        elif lead_type == LeadType.FIRST_TIME_BUYER:
            reasoning_steps.append(ReasoningStep(step="Planning", decision="Lead type is First-Time Buyer. Assigned First-Time Buyer Guidance."))
            strategy = LeadStrategy(
                strategy_type=StrategyType.FIRST_TIME_BUYER_GUIDANCE,
                recommended_approach="Provide additional educational resources on the buying process, closing costs, and inspections alongside listings.",
                follow_up_questions=["Have you been pre-approved for a mortgage yet?", "Would you like a step-by-step guide on what to expect during the closing process?"]
            )
            return strategy, reasoning_steps

        # 5. Standard Fallback
        reasoning_steps.append(ReasoningStep(step="Planning", decision="No specific special strategy matched. Assigned Standard Search."))
        strategy = LeadStrategy(
            strategy_type=StrategyType.STANDARD_SEARCH,
            recommended_approach="Conduct a standard MLS search prioritizing exact matches first based on the provided requirements.",
            follow_up_questions=["Are there any absolute dealbreakers I should know about before creating your property list?"]
        )
        return strategy, reasoning_steps
