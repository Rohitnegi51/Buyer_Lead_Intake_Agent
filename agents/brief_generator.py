import os
import json
from models.schemas import BuyerRequirements, ValidationResult, LeadStrategy, PropertyScore, LeadBrief, ReasoningStep
from typing import List
from agents.llm_client import LLMClient

class BriefGenerator:
    """
    Uses LLMClient to synthesize all deterministic agent outputs into a 
    cohesive, professional markdown brief for the realtor.
    """
    def __init__(self):
        self.llm = LLMClient()

    def generate_brief(
        self, 
        reqs: BuyerRequirements, 
        val_res: ValidationResult, 
        strategy: LeadStrategy, 
        top_properties: List[PropertyScore], 
        reasoning_summary: List[ReasoningStep]
    ) -> str:
        
        # Serialize inputs
        reqs_dict = reqs.model_dump(mode='json')
        val_dict = val_res.model_dump(mode='json')
        strat_dict = strategy.model_dump(mode='json')
        props_list = [p.model_dump(mode='json') for p in top_properties]
        reasoning_list = [r.model_dump(mode='json') for r in reasoning_summary]
        
        prompt = f"""
        You are an expert real estate assistant. Synthesize the following deterministic pipeline data into a final Lead Brief for a realtor.
        
        CRITICAL RULES:
        1. Never invent facts. Rely ONLY on the provided data.
        2. Never infer seller motivation unless explicitly available in the data.
        3. Maintain a highly professional, concise, and actionable tone.
        4. If there are no recommended properties, state that clearly and rely on the Validation and Strategy data to suggest next steps.
        5. For potential concerns, include any flags from validation (like unrealistic budgets, missing info, prompt injection attempts).
        6. For questions to clarify, use the ones recommended in the Strategy data.

        INPUT DATA:
        Requirements: {json.dumps(reqs_dict, indent=2)}
        Validation: {json.dumps(val_dict, indent=2)}
        Strategy: {json.dumps(strat_dict, indent=2)}
        Top Properties: {json.dumps(props_list, indent=2)}
        Reasoning Log: {json.dumps(reasoning_list, indent=2)}
        
        Respond ONLY with a valid JSON object matching this exact structure:
        {{
            "buyer_profile": "Concise string summary of who the buyer is and what they want.",
            "extracted_requirements": {{ "budget": "string", "locations": "string", "property_types": "string", "bedrooms": "string", "features": "string" }},
            "recommended_properties": [ 
                {{ "id": "MLS-...", "score": "95%", "details": "Price, Beds, Neighborhood...", "reasons": "Why it matched..." }} 
            ],
            "match_analysis": "Explanation of how the properties fit the overall criteria and search levels used.",
            "potential_concerns": ["Concern 1", "Concern 2"],
            "questions_to_clarify": ["Question 1", "Question 2"],
            "suggested_realtor_action": "The immediate next step."
        }}
        """

        response_text = self.llm.generate_brief(prompt)
        
        # Enforce validation against our schema
        brief = LeadBrief.model_validate_json(response_text)

        # Generate formatting Markdown
        return self._render_markdown(brief)

    def _render_markdown(self, brief: LeadBrief) -> str:
        md = f"# Realtor Lead Brief\n\n"
        
        md += f"## 1. Buyer Profile\n{brief.buyer_profile}\n\n"
        
        md += f"## 2. Extracted Requirements\n"
        for k, v in brief.extracted_requirements.items():
            if v and v != "string": # prevent empty placeholder
                clean_k = k.replace('_', ' ').title()
                md += f"- **{clean_k}:** {v}\n"
        md += "\n"
        
        md += f"## 3. Recommended Properties\n"
        if not brief.recommended_properties:
            md += "No properties found matching the current criteria. See concerns below.\n\n"
        else:
            for p in brief.recommended_properties:
                prop_id = p.get('id', p.get('property_id', 'Unknown ID'))
                score = p.get('score', p.get('match_percentage', 'N/A'))
                details = p.get('details', '')
                reasons = p.get('reasons', p.get('match_reasons', ''))
                
                md += f"### {prop_id} - Score: {score}\n"
                if details:
                    md += f"- **Details:** {details}\n"
                if reasons:
                    md += f"- **Why it matches:** {reasons}\n"
                md += "\n"
                
        md += f"## 4. Match Analysis\n{brief.match_analysis}\n\n"
        
        md += f"## 5. Potential Concerns\n"
        if brief.potential_concerns:
            for c in brief.potential_concerns:
                md += f"- {c}\n"
        else:
            md += "None flagged.\n"
        md += "\n"
        
        md += f"## 6. Questions To Clarify\n"
        if brief.questions_to_clarify:
            for q in brief.questions_to_clarify:
                md += f"- {q}\n"
        else:
            md += "None at this time.\n"
        md += "\n"
        
        md += f"## 7. Suggested Realtor Action\n{brief.suggested_realtor_action}\n"
        
        return md
