import pandas as pd
from typing import List
from models.schemas import BuyerRequirements, PropertyScore, MatchCategory

class RankingEngine:
    """
    Scores and ranks candidate properties deterministically based on buyer requirements.
    Weights: Location: 40%, Budget: 25%, Bedrooms: 20%, Features: 15%.
    """
    def rank(self, candidates_df: pd.DataFrame, reqs: BuyerRequirements, search_level: int) -> List[PropertyScore]:
        scores = []
        
        for _, row in candidates_df.iterrows():
            breakdown = {}
            reasons = {}
            
            # 1. Location Score (40%)
            loc_score = 0
            loc_val = str(row.get('neighborhood', '')).lower()
            if not reqs.locations:
                loc_score = 40
                reasons['location'] = "No specific location constraints provided."
            else:
                requested_locs = [l.lower() for l in reqs.locations]
                if loc_val in requested_locs:
                    loc_score = 40
                    reasons['location'] = f"Exact match for preferred neighborhood ({row.get('neighborhood')})."
                else:
                    loc_score = 20
                    reasons['location'] = f"Nearby alternative neighborhood ({row.get('neighborhood')})."
            breakdown['location'] = loc_score

            # 2. Budget Score (25%)
            budg_score = 0
            price = row.get('price', float('inf'))
            if not reqs.budget:
                budg_score = 25
                reasons['budget'] = "No budget constraints provided."
            elif price <= reqs.budget:
                budg_score = 25
                reasons['budget'] = f"Price (${price:,.0f}) is within the target budget of ${reqs.budget:,.0f}."
            else:
                budg_score = 15
                reasons['budget'] = f"Price (${price:,.0f}) is slightly over budget but within the expanded search range."
            breakdown['budget'] = budg_score

            # 3. Bedrooms Score (20%)
            bed_score = 0
            beds = row.get('bedrooms', 0)
            if not reqs.bedrooms:
                bed_score = 20
                reasons['bedrooms'] = "No bedroom minimum provided."
            elif beds >= reqs.bedrooms:
                bed_score = 20
                reasons['bedrooms'] = f"Meets or exceeds bedroom requirement with {beds} beds."
            breakdown['bedrooms'] = bed_score

            # 4. Features Score (15%)
            feat_score = 0
            listing_features = str(row.get('features', '')).lower()
            if not reqs.nice_to_have_features:
                feat_score = 15
                reasons['features'] = "No specific additional features requested."
            else:
                matches = [f for f in reqs.nice_to_have_features if f.lower() in listing_features]
                if len(matches) > 0:
                    ratio = len(matches) / len(reqs.nice_to_have_features)
                    feat_score = round(15 * ratio, 2)
                    reasons['features'] = f"Contains requested features: {', '.join(matches)}."
                else:
                    feat_score = 5 # Base score for having some features
                    reasons['features'] = "Missing specific nice-to-have features."
            breakdown['features'] = feat_score

            # Total and Category
            total_score = loc_score + budg_score + bed_score + feat_score
            match_percentage = total_score
            
            if match_percentage >= 90:
                match_category = MatchCategory.EXCELLENT
            elif match_percentage >= 75:
                match_category = MatchCategory.STRONG
            elif match_percentage >= 60:
                match_category = MatchCategory.MODERATE
            else:
                match_category = MatchCategory.WEAK

            details = {
                "price": price,
                "bedrooms": beds,
                "neighborhood": row.get('neighborhood', ''),
                "property_type": row.get('property_type', ''),
                "features": row.get('features', '')
            }

            prop_score = PropertyScore(
                property_id=str(row.get('listing_id', row.get('mls_number', 'Unknown'))),
                total_score=total_score,
                match_percentage=match_percentage,
                match_category=match_category,
                search_level_used=search_level,
                score_breakdown=breakdown,
                match_reasons=reasons,
                details=details
            )
            scores.append(prop_score)

        # Sort descending by total score and return top 5
        scores.sort(key=lambda x: x.total_score, reverse=True)
        return scores[:5]
