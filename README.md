# Agentic AI Requirements Engineering & SDLC Model Selection Engine
## For Automated Commercial Loan Origination & Credit Risk Management System

A multi-agent Software Engineering system built with Streamlit and Google Gemini that automates **IEEE 830 Software Requirements Specification (SRS) Extraction** and **SDLC Model Selection** for Indian commercial banking loan origination systems.

## Problem Domain
Commercial banks evaluating corporate and MSME loan applications must simultaneously assess **borrower repayment reliability** (via credit bureau histories, GST filings, and financial ratios) and **institutional lending capacity** (enforcing capital exposure limits and preventing systemic risk concentration), all while adhering to strict Reserve Bank of India (RBI) compliance mandates.

## Architecture
- **Agent 1 (Requirements Engineering Engine):** Conducts multi-turn stakeholder elicitation grounded in RBI Master Directions and the IT Act, 2000 (`financial_regulations.txt`), generating categorized requirements (FR, NFR, EI, CON), a live Requirements Traceability Matrix (RTM), and targeted clarification questions.
- **Agent 2 (SDLC Model Selection Engine):** Evaluates the finalized SRS against Software Engineering project criteria (`sdlc_models.txt`) to recommend and justify the optimal SDLC model.
- **Persistence Layer:** Automatically logs all conversational turns and finalized SRS/SDLC artifacts into a local SQLite database (`se_project.db`).

## Setup & Execution
1. Install dependencies:
   `pip install -r run_requirements.txt`

2. Run the application:
   `python -m streamlit run app.py`

3. Enter your Gemini API Key in the left sidebar and start defining your loan origination system scenario to **Agent 1 via prompts**.

4. Click **Finalize Requirements & Deduce SDLC Model (Agent 2)** to recommend the most suitable model and justify the choice (automatically persisted to `se_project.db`).
