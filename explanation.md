# AgentMira: Real Estate Intake Pipeline Architecture

## 1. Overview and Philosophy
The AgentMira Intake Pipeline is designed to process unstructured, natural-language real estate buyer inquiries, validate them against real-world market constraints, and generate highly professional, actionable briefs for realtors.

The core philosophy of this architecture is a **Hybrid Agentic Design**. We deliberately isolate the non-deterministic nature of Large Language Models (LLMs) from the mission-critical business logic. LLMs are used exclusively at the "edges" of the pipeline (for extracting unstructured data and synthesizing final markdown), while the core reasoning—security, market validation, strategic planning, search, and ranking—is handled by deterministic, rule-based Python modules. This guarantees zero hallucinations in property recommendations, strict adherence to budget constraints, and consistent reasoning.

## 2. Agent Modules & Responsibilities

The pipeline follows a strict synchronous execution graph:

1. **DatasetProfiler (`agents/dataset_profiler.py`)**
   - **Role**: Analyzes the MLS dataset to establish baseline market statistics (e.g., minimum viable budgets for specific neighborhoods, common property types).
   - **Design Decision**: Pre-computing this profile prevents the Validator from needing to query the dataset repeatedly, optimizing performance and establishing dynamic, data-driven thresholds for "unrealistic" budgets.

2. **SecurityChecker (`agents/security_checker.py`)**
   - **Role**: Intercepts all incoming unstructured text before it reaches the LLMs.
   - **Design Decision**: Uses pattern-matching algorithms to detect common prompt injection techniques (e.g., "ignore previous instructions") and unauthorized data requests (e.g., asking for seller names). Malicious leads are immediately rejected, protecting the LLMs from manipulation.

3. **LeadAnalyzer (`agents/lead_analyzer.py` via `LLMClient`)**
   - **Role**: Uses AI to convert natural language inquiries into structured JSON matching the `BuyerRequirements` schema.
   - **Design Decision**: Extracts budget, locations, bedrooms, and features into strict data types. Also computes an `extraction_confidence` score to flag ambiguous leads.

4. **LeadTypeClassifier (`agents/lead_type_classifier.py`)**
   - **Role**: Classifies the buyer intent (e.g., Relocation, Investor, First-Time Buyer).
   - **Design Decision**: Deterministic classification ensures the downstream Planner agent always triggers the correct customized strategic workflow.

5. **Validator (`agents/validator.py`)**
   - **Role**: Cross-references the extracted `BuyerRequirements` against the `DatasetProfiler` statistics.
   - **Design Decision**: Automatically detects contradictions (e.g., "$250k budget for a 4BR condo in Brickell"), missing critical info, and generates market insights. This prevents the Searcher from running doomed queries.

6. **Planner (`agents/planner.py`)**
   - **Role**: Generates a custom `LeadStrategy` based on the validation results and the classification type.
   - **Design Decision**: Defines exactly how the search should be conducted (e.g., expand budget by 10% if Standard Search fails, or focus on neighborhood amenities for Family Search) and queues up intelligent follow-up questions for the realtor.

7. **Searcher (`agents/searcher.py`)**
   - **Role**: Executes iterative Pandas queries against the MLS dataset.
   - **Design Decision**: Implements a progressive 3-level search. If Level 1 (exact constraints) yields no results, it falls back to Level 2 (expanded budget) or Level 3 (expanded neighborhood boundaries), ensuring the realtor always has *some* options to discuss.

8. **Ranker (`agents/ranker.py`)**
   - **Role**: Scores the candidate pool based on a weighted formula (Location 40%, Budget 25%, Bedrooms 20%, Features 15%).
   - **Design Decision**: Ensures the top 5 most relevant properties are floated to the top, mathematically justifying the "Match Percentage" to the user.

9. **BriefGenerator (`agents/brief_generator.py` via `LLMClient`)**
   - **Role**: Ingests all structured data and reasoning logs and synthesizes a professional Markdown report.
   - **Design Decision**: Subjected to strict system rules ("Never invent facts," "Never infer seller motivation") to maintain compliance and accuracy.

## 3. Resilience and Fallback Architecture (`agents/llm_client.py`)
To handle API rate limits and connection instability, the pipeline uses a custom `LLMClient`. 
- The system defaults to **Google Gemini 2.5 Flash** due to its speed and native structured output capabilities.
- If Gemini exhausts its quota (HTTP 429) or becomes unavailable, the system automatically catches the exception and falls back to **xAI Grok API** (via `urllib.request` to avoid heavy SDK dependencies). 
- Both API paths enforce strict JSON structure requirements, ensuring downstream Python schemas never break.

## 4. Final Output 
The pipeline outputs two artifacts per lead:
- `outputs/briefs/LEAD_ID_Brief.md`: A highly readable, structured report intended for the Realtor's immediate use.
- `outputs/logs/LEAD_ID_log.json`: A transparent, step-by-step reasoning log explaining exactly *why* a property was chosen, *why* a budget was flagged as unrealistic, and *which* search expansion levels were used.
