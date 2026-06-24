from models.schemas import BuyerRequirements, LeadType

class LeadTypeClassifier:
    """
    Provides a deterministic, rule-based classification of the lead type based on keyword 
    heuristics, strictly avoiding LLM usage.
    """
    def classify(self, reqs: BuyerRequirements, inquiry_text: str) -> LeadType:
        text = inquiry_text.lower()
        
        if "relocat" in text or "moving from" in text or "transfer" in text:
            return LeadType.RELOCATION
            
        if "family" in text or "school" in text or "kids" in text or "children" in text:
            return LeadType.FAMILY
            
        if "investment" in text or "roi" in text or "cap rate" in text or "tenant" in text or "income" in text:
            return LeadType.INVESTOR
            
        if "first house" in text or "first time" in text or "first-time" in text:
            return LeadType.FIRST_TIME_BUYER
            
        if reqs.budget and reqs.budget >= 3000000:
            return LeadType.LUXURY
            
        if "wheelchair" in text or "elevator" in text or "accessible" in text or "ramp" in text:
            return LeadType.ACCESSIBILITY
            
        if ("cash" in text and "buy" in text) or "all cash" in text:
            return LeadType.CASH_BUYER
            
        return LeadType.STANDARD
