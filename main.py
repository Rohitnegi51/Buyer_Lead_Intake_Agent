import os
import json
import pandas as pd
from dotenv import load_dotenv

from models.schemas import LeadType, ReasoningLog
from agents.dataset_profiler import DatasetProfiler
from agents.security_checker import SecurityChecker
from agents.lead_analyzer import LeadAnalyzer
from agents.lead_type_classifier import LeadTypeClassifier
from agents.validator import Validator
from agents.planner import LeadPlanner
from agents.searcher import PropertySearcher
from agents.ranker import RankingEngine
from agents.brief_generator import BriefGenerator

def run_pipeline():
    load_dotenv()
    
    os.makedirs("outputs/briefs", exist_ok=True)
    os.makedirs("outputs/logs", exist_ok=True)
    
    print("Loading data and initializing agents...")
    df = pd.read_csv("miami_mls_listings.csv")
    profiler = DatasetProfiler(df)
    
    security = SecurityChecker()
    analyzer = LeadAnalyzer()
    classifier = LeadTypeClassifier()
    validator = Validator(profiler)
    planner = LeadPlanner()
    searcher = PropertySearcher(df)
    ranker = RankingEngine()
    generator = BriefGenerator()
    
    with open("sample_buyer_inquiries.json", "r") as f:
        leads = json.load(f)
        
    print(f"Loaded {len(leads)} leads. Processing...")
        
    for lead in leads:
        lead_id = lead['lead_id']
        print(f"\n--- Processing {lead_id} ---")
        inquiry = lead['message']
        full_reasoning = []
        
        # Security
        sec_res, sanitized_text = security.check_inquiry(inquiry)
        if not sec_res.is_safe:
            print(f"[{lead_id}] MALICIOUS LEAD CAUGHT: {sec_res.flags}")
            continue
            
        # Analysis
        try:
            reqs = analyzer.analyze(inquiry)
        except Exception as e:
            print(f"[{lead_id}] ERROR (Analyzer): {e}")
            continue
            
        # Classification
        lead_type = classifier.classify(reqs, inquiry)
        reqs.lead_type = lead_type
        
        # Validation
        val_res, val_reasoning = validator.validate(reqs)
        full_reasoning.extend(val_reasoning)
        
        # Planner
        strat, plan_reasoning = planner.determine_strategy(reqs, val_res, lead_type, inquiry)
        full_reasoning.extend(plan_reasoning)
        
        # Searcher
        results_df, level_used, search_reasoning = searcher.search(reqs, strat)
        full_reasoning.extend(search_reasoning)
        
        # Ranker
        top_scores = ranker.rank(results_df, reqs, level_used)
        
        # Generator
        try:
            brief_md = generator.generate_brief(reqs, val_res, strat, top_scores, full_reasoning)
            
            with open(f"outputs/briefs/{lead_id}_brief.md", "w") as f:
                f.write(brief_md)
                
            log = ReasoningLog(lead_id=lead_id, steps=full_reasoning)
            with open(f"outputs/logs/{lead_id}_log.json", "w") as f:
                f.write(log.model_dump_json(indent=2))
                
            print(f"[{lead_id}] SUCCESS: Brief and Log saved.")
        except Exception as e:
            print(f"[{lead_id}] ERROR (Generator): {e}")
            
        import time
        time.sleep(5) # Delay to respect the 15 RPM free tier quota

if __name__ == "__main__":
    run_pipeline()
