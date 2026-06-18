# Remaining Tasks for Finemonix (Days 24-30)

Based on the `finemonix-project.txt` 30-day build planner and recent implementations, Phase 4 is mostly complete. The following is a detailed breakdown of the exact tasks remaining to fully complete the 30-day build plan.

## Phase 4: Regulatory Filing Monitor (Advanced ML)

### Day 24: Tone Drift Detector (Missing)
**Objective:** Detect negative shifts in management sentiment across quarterly/annual reports.
- **Task:** Implement `compute_tone_drift(bse_code)` Celery task.
- **Details:**
  - Extract "Management Discussion and Analysis" (MD&A) or general commentary from the extracted PDF text.
  - Generate embeddings of the text using `sentence-transformers` (`all-MiniLM-L6-v2`).
  - Store the embeddings in the Qdrant vector database.
  - Compute the cosine distance between the current quarter's embedding and the previous quarter's embedding.
  - Calculate a rolling z-score. If the z-score exceeds 2 standard deviations, flag a "tone drift" anomaly.
  - Update `anomaly_scores.score_tone` in the PostgreSQL database.

### Day 25: Knowledge Graph Anomaly Detector (Missing GDS Algorithms)
**Objective:** Detect structural risks in corporate shareholding and promoter networks using Neo4j Graph Data Science (GDS).
- **Task:** Implement `compute_graph_anomaly(bse_code)` Celery task.
- **Details:**
  - Ensure the Neo4j GDS plugin is correctly configured.
  - Run `PageRank` on the promoter-company graph to identify the most influential entities (e.g., shadow promoters).
  - Run `Weakly Connected Components` (WCC) to find circular shareholding loops or shell company clusters.
  - Run `Louvain` community detection to flag rapid, suspicious corporate restructuring events.
  - Aggregate these metrics and update `anomaly_scores.score_graph` in the database.

## Phase 5: Demo & Polish

### Day 27: DHFL & Yes Bank Retroactive Demo (Missing)
**Objective:** Prove the efficacy of the ML models using historical crisis data.
- **Task:** Prepare the historical demonstration fixtures.
- **Details:**
  - Run the entire completed Phase 4 pipeline retroactively on DHFL filings from 2016-2019 to demonstrate that the anomaly signals (Isolation Forest, Tone Drift, Graph Anomaly) spike leading up to the 2018 Q3/Q4 default.
  - Prepare similar fixtures for Yes Bank.
  - Write a `reset_demo()` utility script to easily wipe the database and re-seed this specific state for interview presentations.

### Day 28: Dashboard Integration Fixes (Pending)
**Objective:** Wire up the frontend Dashboard to the completed backend engines.
- **Task:** Update `backend/routers/dashboard.py`.
- **Details:**
  - The dashboard endpoint currently has hardcoded stub text indicating `"Loan engine is not implemented yet"`.
  - Wire the actual Loan Eligibility Engine (completed in Phase 3) into the dashboard summary response.
  - Ensure the unified dashboard seamlessly aggregates the cash flow forecasts, watchlist anomalies, and loan assessments.

### Day 29: Production Deployment (Pending)
**Objective:** Host the platform on a cloud provider for live access.
- **Task:** Deploy to Railway.app.
- **Details:**
  - Write the required `railway.json` / `railway.toml` configurations.
  - Ensure the existing `Dockerfile.api` and `Dockerfile.worker` are optimized.
  - Set up and configure production environment variables for PostgreSQL, Neo4j (AuraDB), Redis, and Qdrant Cloud.

### Day 30: Demo Hardening (Pending)
**Objective:** Ensure a flawless presentation experience.
- **Task:** Final UX polish and end-to-end testing.
- **Details:**
  - Perform a complete dry-run of the demo script: Upload Tally -> View Forecast -> Run What-If Scenario -> Trigger Loan Approval -> View Watchlist Anomalies.
  - Ensure frontend loading skeleton states and error handlers provide graceful degradation.
  - Prepare concise, 3-5 sentence answers for the key technical interview questions outlined in the project planner.
