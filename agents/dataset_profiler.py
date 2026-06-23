import pandas as pd
from typing import Dict, Any, Optional

class DatasetProfiler:
    """
    Profiles the MLS dataset to extract market statistics and distributions.
    Provides methods to support unrealistic budget detection and market insight generation.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        
        # Clean price data
        self.df['price'] = pd.to_numeric(self.df['price'], errors='coerce')
        
        # Exclude extreme outliers for accurate market profiling 
        # (e.g., the 250M INR listing)
        self.valid_df = self.df[(self.df['price'] > 0) & (self.df['price'] < 100000000)].copy()
        
        # Compute stats during initialization
        self._neighborhood_stats = self._compute_neighborhood_stats()
        self._property_type_counts = self.valid_df['property_type'].value_counts().to_dict()
        self._feature_distributions = self._compute_feature_distributions()

    def _compute_neighborhood_stats(self) -> Dict[str, Dict[str, float]]:
        stats = {}
        grouped = self.valid_df.groupby('neighborhood')['price']
        
        for name, group in grouped:
            stats[name] = {
                'min_price': float(group.min()),
                'max_price': float(group.max()),
                'median_price': float(group.median()),
                'listing_count': int(group.count())
            }
        return stats
        
    def _compute_feature_distributions(self) -> Dict[str, int]:
        feature_counts = {}
        for features_str in self.valid_df['features'].dropna():
            # Features are semicolon separated
            features_list = [f.strip() for f in features_str.split(';') if f.strip()]
            for feature in features_list:
                feature_counts[feature] = feature_counts.get(feature, 0) + 1
        return feature_counts

    def get_neighborhood_stats(self) -> Dict[str, Dict[str, float]]:
        """Returns min, max, median price, and count per neighborhood."""
        return self._neighborhood_stats

    def get_price_range(self, neighborhood: str) -> Optional[Dict[str, float]]:
        """Returns the price range for a specific neighborhood if it exists."""
        return self._neighborhood_stats.get(neighborhood)

    def get_property_type_counts(self) -> Dict[str, int]:
        """Returns distribution of property types across the market."""
        return self._property_type_counts

    def get_feature_distributions(self) -> Dict[str, int]:
        """Returns the count of how many properties have each feature."""
        return self._feature_distributions

    def get_market_summary(self) -> Dict[str, Any]:
        """Returns a high-level summary of the dataset for insight generation."""
        return {
            "total_valid_listings": len(self.valid_df),
            "neighborhoods_tracked": len(self._neighborhood_stats),
            "overall_median_price": float(self.valid_df['price'].median()),
            "most_common_property_type": max(self._property_type_counts, key=self._property_type_counts.get) if self._property_type_counts else None,
            "top_5_features": sorted(self._feature_distributions.items(), key=lambda x: x[1], reverse=True)[:5]
        }
