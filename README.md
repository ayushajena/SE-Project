# Agentic AI Requirements Engineering & SDLC Model Selection Engine

A multi-agent Software Engineering system built with Streamlit and Google Gemini that automates **IEEE 830 Software Requirements Specification (SRS)** extraction and **SDLC Model Selection** for Indian commercial banking systems.

## Architecture
- **Agent 1 (Requirements Engineering Engine):** Conducts multi-turn stakeholder elicitation grounded in RBI Master Directions and the IT Act, 2000 (`financial_regulations.txt`), generating categorized requirements (`FR`, `NFR`, `EI`, `CON`), a live Requirements Traceability Matrix (`RTM`), and targeted clarification questions.
- **Agent 2 (SDLC Selection Engine):** Evaluates the finalized SRS against canonical Software Engineering project criteria (`sdlc_frameworks.txt`) to recommend and justify the optimal SDLC model.
- **Persistence Layer:** Automatically logs all conversational turns and finalized SRS/SDLC artifacts into a local SQLite database (`se_project.db`).

## Setup & Execution
1. Install dependencies:
   pip install -r requirements.txt

2. Run the application:
   streamlit run app.py

3. Enter your Gemini API Key in the left sidebar and start defining your banking system scenario.
