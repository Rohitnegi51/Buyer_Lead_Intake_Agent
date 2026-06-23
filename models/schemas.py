from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MatchCategory(str, Enum):
    EXCELLENT = "Excellent Match"
    STRONG = "Strong Match"
    MODERATE = "Moderate Match"
    WEAK = "Weak Match"

class LeadType(str, Enum):
    STANDARD = "Standard"
    RELOCATION = "Relocation"
    FAMILY = "Family"
    INVESTOR = "Investor"
    FIRST_TIME_BUYER = "First-Time Buyer"
    LUXURY = "Luxury"
    ACCESSIBILITY = "Accessibility"
    CASH_BUYER = "Cash Buyer"

class StrategyType(str, Enum):
    STANDARD_SEARCH = "Standard Search"
    RELOCATION_ASSISTANCE = "Relocation Assistance"
    FAMILY_HOME_SEARCH = "Family Home Search"
    ACCESSIBILITY_SEARCH = "Accessibility-Oriented Search"
    LUXURY_SEARCH = "Luxury Search"
    INVESTMENT_SEARCH = "Investment Search"
    EXPECTATION_ALIGNMENT = "Expectation Alignment"
    CLARIFICATION_FIRST = "Clarification First"
    NEGOTIATION_ADVICE = "Negotiation Advice"
    FIRST_TIME_BUYER_GUIDANCE = "First-Time Buyer Guidance"

class SecurityResult(BaseModel):
    is_safe: bool = Field(description="True if the inquiry is safe to process, False if malicious intent is detected.")
    flags: List[str] = Field(default_factory=list, description="List of security flags like 'Prompt Injection', 'Data Exfiltration'.")

class BuyerRequirements(BaseModel):
    budget: Optional[float] = Field(None, description="The maximum budget of the buyer in dollars.")
    bedrooms: Optional[int] = Field(None, description="The minimum number of bedrooms requested.")
    locations: List[str] = Field(default_factory=list, description="List of desired neighborhoods or cities.")
    property_types: List[str] = Field(default_factory=list, description="List of property types like 'Condo', 'Single Family'.")
    must_have_features: List[str] = Field(default_factory=list, description="List of explicitly required features.")
    nice_to_have_features: List[str] = Field(default_factory=list, description="List of nice-to-have features.")
    lead_type: LeadType = Field(default=LeadType.STANDARD, description="Classification of the buyer's lead type.")
    extraction_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0 representing extraction quality.")

class ValidationResult(BaseModel):
    is_valid: bool = Field(description="Whether the lead can be reasonably processed.")
    prompt_injection_detected: bool = Field(False, description="Whether prompt injection or malicious text was detected.")
    unrealistic_budget: bool = Field(False, description="Whether the budget is unrealistically low for the requested criteria.")
    missing_information: bool = Field(False, description="Whether essential information is missing.")
    contradictory_requirements: bool = Field(False, description="Whether the buyer's requests contradict each other.")
    notes: List[str] = Field(default_factory=list, description="Specific notes from the validator.")
    market_insight: str = Field("", description="Insights derived from the dataset profiling, e.g., 'No active listings in Brickell satisfy the budget'.")

class LeadStrategy(BaseModel):
    strategy_type: StrategyType = Field(description="The high-level approach recommended.")
    recommended_approach: str = Field(description="Instructions on how to handle the property search.")
    follow_up_questions: List[str] = Field(default_factory=list, description="Questions the realtor should ask the buyer to clarify needs.")

class PropertyScore(BaseModel):
    property_id: str = Field(description="The unique listing_id or mls_number.")
    total_score: float = Field(description="Total computed score.")
    match_percentage: float = Field(description="Match percentage (0-100).")
    match_category: MatchCategory = Field(description="'Excellent Match', 'Strong Match', 'Moderate Match', or 'Weak Match'")
    search_level_used: int = Field(description="1 for Exact Match, 2 for Budget Expanded, 3 for Nearby Neighborhoods")
    score_breakdown: Dict[str, float] = Field(default_factory=dict, description="Breakdown of score into location, budget, bedrooms, features, etc.")
    match_reasons: Dict[str, str] = Field(default_factory=dict, description="Reasons organized by category: 'location', 'budget', 'features', 'lifestyle_fit'.")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details of the property for rendering.")

class ReasoningStep(BaseModel):
    step: str = Field(description="The phase of the pipeline, e.g., 'Security Check', 'Validation'.")
    decision: str = Field(description="The decision or finding made during this step.")

class ReasoningLog(BaseModel):
    lead_id: str = Field(description="The unique ID of the processed lead.")
    steps: List[ReasoningStep] = Field(default_factory=list, description="The sequence of reasoning steps taken.")

class LeadBrief(BaseModel):
    buyer_profile: str = Field(description="Markdown summary of the buyer profile.")
    extracted_requirements: Dict[str, Any] = Field(description="Dictionary representation of requirements.")
    recommended_properties: List[Dict[str, Any]] = Field(description="List of top property matches with details and reasoning.")
    match_analysis: str = Field(description="Explanation of how properties were scored and matched.")
    potential_concerns: List[str] = Field(default_factory=list, description="List of risk flags and concerns.")
    questions_to_clarify: List[str] = Field(default_factory=list, description="Suggested questions for the realtor to ask.")
    suggested_realtor_action: str = Field(description="Next immediate step for the realtor.")
