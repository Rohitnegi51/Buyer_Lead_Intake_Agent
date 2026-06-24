from typing import Tuple, List
from models.schemas import BuyerRequirements, ValidationResult, ReasoningStep
from agents.dataset_profiler import DatasetProfiler

class Validator:
    """
    Validates buyer requirements against empirical market data to detect 
    unrealistic expectations, missing information, or contradictions.
    Also generates reasoning log steps explaining its decisions.
    """
    def __init__(self, profiler: DatasetProfiler):
        self.profiler = profiler

    def validate(self, reqs: BuyerRequirements, prompt_injection_detected: bool = False) -> Tuple[ValidationResult, List[ReasoningStep]]:
        is_valid = True
        notes = []
        market_insight = ""
        missing_info = False
        unrealistic_budget = False
        contradictory = False
        reasoning_steps = []

        # 1. Detect missing budget
        if not reqs.budget:
            notes.append("Budget was not specified.")
            missing_info = True
            reasoning_steps.append(ReasoningStep(step="Validation", decision="Missing budget detected."))
        else:
            reasoning_steps.append(ReasoningStep(step="Validation", decision=f"Budget identified: ${reqs.budget:,.0f}."))

        # 2. Detect missing location/property types
        if not reqs.locations and not reqs.property_types:
            notes.append("Missing location and property type preferences.")
            missing_info = True
            reasoning_steps.append(ReasoningStep(step="Validation", decision="Missing location and property type preferences."))

        # 3. Detect unrealistic budget based on market profile
        if reqs.locations and reqs.budget:
            lowest_possible_price = float('inf')
            checked_locations = []
            
            for loc in reqs.locations:
                for known_loc in self.profiler.get_neighborhood_stats().keys():
                    if loc.lower() in known_loc.lower():
                        checked_locations.append(known_loc)
                        price_range = self.profiler.get_price_range(known_loc)
                        if price_range:
                            lowest_possible_price = min(lowest_possible_price, price_range['min_price'])
                            
            if checked_locations and lowest_possible_price != float('inf'):
                if reqs.budget < lowest_possible_price:
                    unrealistic_budget = True
                    is_valid = False
                    market_insight = f"The lowest price in {', '.join(checked_locations)} starts at ${lowest_possible_price:,.0f}, which is above the requested budget of ${reqs.budget:,.0f}."
                    notes.append(market_insight)
                    reasoning_steps.append(ReasoningStep(step="Validation", decision=f"Unrealistic budget: {market_insight}"))
                else:
                    reasoning_steps.append(ReasoningStep(step="Validation", decision=f"Budget is realistic for {', '.join(checked_locations)}. Lowest market price is ${lowest_possible_price:,.0f}."))

        # 4. Detect contradictory requirements (e.g., massive house on a tiny budget)
        if reqs.budget and reqs.bedrooms:
            if reqs.budget < 500000 and reqs.bedrooms >= 5:
                contradictory = True
                notes.append("Budget is likely too low for a 5+ bedroom property in Miami.")
                is_valid = False
                reasoning_steps.append(ReasoningStep(step="Validation", decision="Contradictory requirements: Budget is too low for requested bedroom count."))

        result = ValidationResult(
            is_valid=is_valid,
            prompt_injection_detected=prompt_injection_detected,
            unrealistic_budget=unrealistic_budget,
            missing_information=missing_info,
            contradictory_requirements=contradictory,
            notes=notes,
            market_insight=market_insight
        )
        
        return result, reasoning_steps
