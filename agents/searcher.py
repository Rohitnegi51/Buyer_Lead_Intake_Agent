import pandas as pd
from typing import Tuple, List
from models.schemas import BuyerRequirements, LeadStrategy, ReasoningStep

NEARBY_NEIGHBORHOODS = {
    "brickell": ["downtown miami", "edgewater"],
    "downtown miami": ["brickell", "edgewater"],
    "miami beach": ["south beach", "mid-beach", "north beach"],
    "south beach": ["miami beach", "mid-beach"],
    "mid-beach": ["miami beach", "south beach", "north beach"],
    "north beach": ["miami beach", "mid-beach"],
    "coral gables": ["coconut grove", "pinecrest"],
    "coconut grove": ["coral gables", "brickell"],
    "aventura": ["sunny isles beach", "north miami"],
    "north miami": ["aventura", "bal harbour"],
    "bal harbour": ["north miami", "surfside"],
    "wynwood": ["edgewater", "downtown miami"],
    "edgewater": ["wynwood", "downtown miami", "brickell"],
    "pinecrest": ["coral gables", "coconut grove"],
    "doral": ["coral gables"],
    "key biscayne": ["brickell"]
}

class PropertySearcher:
    """
    Deterministically filters the MLS DataFrame across 3 search levels.
    Level 1: Exact matches.
    Level 2: Budget expanded by 10%.
    Level 3: Budget expanded by 10% + Nearby neighborhoods included.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def get_nearby_neighborhoods(self, locations: List[str]) -> List[str]:
        expanded = set(loc.lower() for loc in locations)
        for loc in locations:
            neighbors = NEARBY_NEIGHBORHOODS.get(loc.lower(), [])
            expanded.update(neighbors)
        return list(expanded)

    def search(self, reqs: BuyerRequirements, strategy: LeadStrategy) -> Tuple[pd.DataFrame, int, List[ReasoningStep]]:
        reasoning = []
        
        # Level 1: Exact Match
        level = 1
        results = self._filter(self.df, reqs.budget, reqs.bedrooms, reqs.locations, reqs.property_types)
        reasoning.append(ReasoningStep(step="Search", decision=f"Level 1 (Exact Match): Found {len(results)} properties."))
        
        if len(results) >= 10:
            return results.head(10), level, reasoning
            
        # Level 2: Expand budget by 10%
        level = 2
        expanded_budget = reqs.budget * 1.1 if reqs.budget else None
        budget_str = f"${expanded_budget:,.0f}" if expanded_budget else "None"
        results = self._filter(self.df, expanded_budget, reqs.bedrooms, reqs.locations, reqs.property_types)
        reasoning.append(ReasoningStep(step="Search", decision=f"Level 2 (Expanded Budget by 10% to {budget_str}): Found {len(results)} properties."))
        
        if len(results) >= 10:
            return results.head(10), level, reasoning
            
        # Level 3: Include nearby neighborhoods (keep expanded budget)
        level = 3
        expanded_locations = self.get_nearby_neighborhoods(reqs.locations) if reqs.locations else []
        results = self._filter(self.df, expanded_budget, reqs.bedrooms, expanded_locations, reqs.property_types)
        reasoning.append(ReasoningStep(step="Search", decision=f"Level 3 (Included nearby neighborhoods: {expanded_locations}): Found {len(results)} properties."))
        
        return results.head(10), level, reasoning

    def _filter(self, df: pd.DataFrame, budget: float, bedrooms: int, locations: List[str], property_types: List[str]) -> pd.DataFrame:
        filtered = df.copy()
        
        if budget:
            filtered = filtered[filtered['price'] <= budget]
            
        if bedrooms:
            filtered = filtered[filtered['bedrooms'] >= bedrooms]
            
        if locations:
            loc_lower = [loc.lower() for loc in locations]
            filtered = filtered[filtered['neighborhood'].astype(str).str.lower().isin(loc_lower)]
            
        if property_types:
            pt_lower = [pt.lower() for pt in property_types]
            mask = filtered['property_type'].astype(str).str.lower().apply(lambda x: any(pt in x for pt in pt_lower))
            filtered = filtered[mask]
            
        return filtered
