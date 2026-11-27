import os
import sqlite3
import time
from datetime import datetime
import streamlit as st
from google import genai
from google.genai import types

# Page Configuration
st.set_page_config(
    page_title="Agentic AI Requirements & SDLC Engine",
    layout="wide",
    page_icon=""
)
st.markdown("""
    <style>
        .stAppDeployButton {display: none;}
        [data-testid="stStatusWidget"] {visibility: hidden;}
        [data-testid="stHeaderActionElements"] {display: none;}
        header[data-testid="stHeader"] {background: transparent;}
    </style>
""", unsafe_allow_html=True)

PRIMARY_MODEL = "gemini-3.5-flash-lite"

# -------------------------------------------------------------
# 1. DATABASE PERSISTENCE LAYER (SQLite)
# -------------------------------------------------------------
DB_FILE = "se_project.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            agent_name TEXT,
            user_prompt TEXT,
            response TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_artifacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            srs_output TEXT,
            sdlc_output TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_to_db(agent_name, prompt, response):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_logs (timestamp, agent_name, user_prompt, response) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), agent_name, prompt, response)
    )
    conn.commit()
    conn.close()

def save_artifact_to_db(srs_output, sdlc_output):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO project_artifacts (timestamp, srs_output, sdlc_output) VALUES (?, ?, ?)",
        (datetime.now().isoformat(), srs_output, sdlc_output)
    )
    conn.commit()
    conn.close()

init_db()

# -------------------------------------------------------------
# 2. RAG KNOWLEDGE BASE LOADERS
# -------------------------------------------------------------
def load_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

finance_kb = load_file("financial_regulations.txt")
sdlc_kb = load_file("sdlc_models.txt")

# -------------------------------------------------------------
# 3. RESILIENT API HANDLER WITH MULTI-MODEL FALLBACK
# -------------------------------------------------------------
def call_gemini_resilient(client, contents, system_instruction):
    models_to_try = [PRIMARY_MODEL, "gemini-3.5-flash", "gemini-2.5-flash"]
    last_error = None

    for model_name in models_to_try:
        for attempt in range(1, 3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2,
                    ),
                )
                return response.text
            except Exception as e:
                last_error = e
                if "400" in str(e) or "404" in str(e) or "API_KEY_INVALID" in str(e):
                    raise RuntimeError(f"API Configuration Error: {e}")
                time.sleep(attempt * 2)

    raise RuntimeError(f"Unable to connect to Gemini API endpoints: {last_error}")

# -------------------------------------------------------------
# 4. SIDEBAR CONTROLS
# -------------------------------------------------------------
st.sidebar.title("⚙️ Engine Configuration")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if st.sidebar.button("🔄 Reset Conversation / New Session"):
    st.session_state.messages = []
    st.session_state.final_srs = ""
    st.session_state.ieee_srs = ""
    st.session_state.sdlc_result = ""
    st.session_state.is_finalized = False
    st.rerun()

if st.sidebar.checkbox("View Database Audit Logs"):
    st.sidebar.subheader("SQLite Audit Records")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp, agent_name FROM audit_logs ORDER BY id DESC LIMIT 10")
    logs = cursor.fetchall()
    conn.close()
    if logs:
        for l in logs:
            st.sidebar.text(f"ID {l[0]} | {l[1][:19]} | {l[2]}")
    else:
        st.sidebar.info("No logs in database yet.")

# -------------------------------------------------------------
# 5. MAIN INTERFACE HEADER
# -------------------------------------------------------------
st.title("Agentic AI Requirements Engineering & SDLC Model Selection Engine")
st.caption("Grounded in RBI Master Directions & SDLC Selection Decision Criteria")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "final_srs" not in st.session_state:
    st.session_state.final_srs = ""
if "ieee_srs" not in st.session_state:
    st.session_state.ieee_srs = ""
if "sdlc_result" not in st.session_state:
    st.session_state.sdlc_result = ""
if "is_finalized" not in st.session_state:
    st.session_state.is_finalized = False

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -------------------------------------------------------------
# 6. AGENT 1: CONVERSATIONAL REQUIREMENTS ENGINEERING
# -------------------------------------------------------------

chat_placeholder = (
    "Session finalized. Reset conversation to start a new session."
    if st.session_state.is_finalized
    else "Provide loan system scenario or refine requirements (Agent 1)..."
)
user_input = st.chat_input(chat_placeholder, disabled=st.session_state.is_finalized)

if user_input and not st.session_state.is_finalized:
    if not api_key:
        st.error("Please enter a valid Gemini API Key in the sidebar.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        is_first_turn = len(st.session_state.messages) == 1

        if is_first_turn:
            turn_rules = """
            THIS IS TURN 1 (INITIAL PROMPT):
            - Extract baseline requirements across ALL FOUR IEEE 830 SRS categories:
              * Functional Requirements (FR-01, FR-02, ...)
              * Non-Functional Requirements (NFR-01, NFR-02, ...)
              * External Interfaces (EI-01, EI-02, ...)
              * Constraints (CON-01, CON-02, ...)
            - Include ALL extracted requirements in the initial Requirements Traceability Matrix (RTM).
            - Ask a MAXIMUM of 3 Clarification Questions focused strictly on clarifying ambiguous/incomplete software requirements (do NOT ask low-level code or architectural design questions).
            """
        else:
            turn_rules = """
            THIS IS A FOLLOW-UP TURN (TURN 2+):
            - Print ONLY the NEWLY extracted or modified requirements from this latest user reply under their respective `###` headings.
            - COMPLETELY OMIT any category heading (`### Functional Requirements (FRs)`, `### Non-Functional Requirements (NFRs)`, `### External Interfaces (EIs)`, or `### Constraints (CONs)`) that has zero new or modified items in this turn. NEVER print placeholder lines like "(No new requirements added in this turn)".
            - In `### Requirements Traceability Matrix (RTM)`, retain ALL previous rows from the prior turn's RTM word-for-word (unless explicitly modified/deleted) and insert the new rows grouped strictly by category order (all `FR` rows first, then `NFR`, then `EI`, then `CON`).
            - Ask a MAXIMUM of 2 bulleted Clarification Questions focused strictly on remaining requirement gaps (or write `- No further clarification needed.` if requirements are complete).
            """

        chat_context = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])

        agent1_system_instruction = f"""
        You are an expert Software Requirements Engineering Agent specializing in Indian Financial Systems (RBI Guidelines & IT Act 2000) following the IEEE 830 SRS standard.

        Grounded Knowledge Base (Domain Regulations RAG):
        ---
        {finance_kb}
        ---

        {turn_rules}

        STRICT OUTPUT FORMAT RULES:
        - Output ONLY the applicable sections using these exact unnumbered Markdown level-3 headings (`###`) in this exact order—do NOT append any parenthetical descriptions or extra text to the headings themselves (on Turn 2+, skip any requirement category heading with zero new/modified items; never include User Stories, Acceptance Criteria, Gherkin, or intro/outro chatter):
          ### Functional Requirements (FRs)
          ### Non-Functional Requirements (NFRs)
          ### External Interfaces (EIs)
          ### Constraints (CONs)
          ### Requirements Traceability Matrix (RTM)
          ### Clarification Questions

        - Category Classification Rules:
          * **Non-Functional Requirements (NFRs):** Quality metrics such as performance, availability, encryption strength, and auditability.
          * **External Interfaces (EIs):** User interfaces, external APIs, Core Banking Systems (CBS), credit bureaus, and payment gateways.
          * **Constraints (CONs):** Mandated databases/tech stacks (e.g., PostgreSQL), physical hosting/data localization boundaries, and statutory/legal mandates.

        - Every requirement item under the first four sections MUST strictly follow this exact format:
          **[ID]: [Title]**
          * **Description:** [Concise, verifiable requirement statement specifying WHAT the system must do]
          * **Justification & Source:** [Clearly state whether this stems from **User/Stakeholder Input**, **RBI / IT Act Regulations** (citing the specific rule from the RAG knowledge base), or **Both**, along with the SE rationale]

        - Under `### Requirements Traceability Matrix (RTM)`, output a Markdown table with ONLY these 3 columns, with rows strictly grouped by category order (`FR`, then `NFR`, then `EI`, then `CON`):
          | Requirement ID | Category | Short Description |

        - Under `### Clarification Questions`, list questions as unnumbered bullet points (`- `) focused strictly on requirements-level gaps (what the system should do, edge cases, business rules) — never implementation/design details.
        """

        with st.chat_message("assistant"):
            with st.spinner("Agent 1 Analyzing User Story..."):
                try:
                    client = genai.Client(api_key=api_key)
                    agent1_response = call_gemini_resilient(client, chat_context, agent1_system_instruction)
                    agent1_response += "\n\n> *Note: You do not need to answer these specific questions; feel free to introduce any additional requirements or constraints you missed in earlier turns.*"
                    st.markdown(agent1_response)

                    st.session_state.messages.append({"role": "assistant", "content": agent1_response})
                    if is_first_turn:
                        st.session_state.final_srs = agent1_response
                    else:
                        st.session_state.final_srs += "\n\n--- REFINEMENT UPDATE ---\n\n" + agent1_response

                    log_to_db("Agent_1_Requirements_Engine", user_input, agent1_response)

                except Exception as e:
                    st.error(f"Execution Error: {e}")

# -------------------------------------------------------------
# 7. AGENT 2: TRIGGERED SDLC SELECTION & ARCHITECTURE
# -------------------------------------------------------------
st.divider()
st.subheader("SRS Finalization & SDLC Model Selection")

if st.button("🔴 Compile SRS (Agent 1) & Deduce SDLC Model (Agent 2)", disabled=st.session_state.is_finalized):
    if not api_key:
        st.error("Please enter a valid Gemini API Key in the sidebar.")
    elif not st.session_state.final_srs:
        st.warning("Please interact with Agent 1 first to establish requirements before running Agent 2.")
    else:
        agent1_compile_instruction = f"""
        You are an expert Software Requirements Engineering Agent specializing in Indian Financial Systems (RBI Guidelines & IT Act 2000).
        Synthesize all gathered requirements and conversation history into a formal, complete **IEEE 830-1998 Software Requirements Specification (SRS)** document.

        Grounded Knowledge Base (Domain Regulations RAG):
        ---
        {finance_kb}
        ---

        STRICT OUTPUT FORMAT RULES:
        - Follow the exact IEEE 830-1998 section hierarchy below using Markdown headings (`###` for top-level sections, `####` for subsections).
        - Do NOT include conversational chatter, intro/outro text, or clarification questions.
        - Output ONLY these exact sections in order:

          ### 1. Introduction
          #### 1.1 Purpose
          *(Describe the purpose of the Commercial Loan Origination & Credit Risk Management system and its intended audience: bank credit officers, risk committees, developers, testers, and RBI auditors.)*
          #### 1.2 Scope
          *(Define what the software system will and will not do, including currency/domain boundaries.)*
          #### 1.3 Definitions, Acronyms, and Abbreviations
          *(Define key domain/regulatory terms used in the SRS such as CBS, CKYC, LEF, KFS, WORM, DSCR, RWA, etc.)*
          #### 1.4 References
          *(List all referenced RBI Master Directions, IT Act 2000 sections, and statutory guidelines cited from the RAG knowledge base.)*
          #### 1.5 Overview
          *(Briefly describe how the rest of this SRS document is organized.)*

          ### 2. Overall Description
          #### 2.1 Product Perspective
          *(Describe the system context within the bank's IT ecosystem and high-level interfaces with CBS, credit bureaus, and Account Aggregators.)*
          #### 2.2 Product Functions
          *(Summarize the major functional capabilities at a high level.)*
          #### 2.3 User Characteristics
          *(Describe the user classes—Applicants, Credit Officers, Senior Managers, Risk Committee, Auditors—and their roles/technical expertise.)*
          #### 2.4 Constraints
          *(Consolidate all CON-XX items: database/tech stack mandates, Indian data localization, and statutory retention rules.)*
          #### 2.5 Assumptions and Dependencies
          *(State operational assumptions and external API/infrastructure dependencies.)*

          ### 3. Specific Requirements
          #### 3.1 External Interfaces
          *(Detail all EI-XX items: user interfaces, CBS APIs, credit bureau APIs, and GSTN/Account Aggregator interfaces with inputs/outputs.)*
          #### 3.2 Functional Requirements
          *(Detail every FR-XX item systematically with Description, Inputs, Processing Logic, Outputs, and Regulatory/Stakeholder Source.)*
          #### 3.3 Performance Requirements
          *(Specify latency, throughput, and availability metrics from NFRs.)*
          #### 3.4 Logical Database Requirements
          *(Specify key data entities, ACID integrity, and WORM audit log retention structures.)*
          #### 3.5 Design Constraints
          *(Specify regulatory compliance standards, encryption algorithms like AES-256/TLS 1.3, and hosting boundaries.)*
          #### 3.6 Software System Quality Attributes
          *(Detail security, auditability, reliability, maintainability, and non-repudiation attributes.)*
          #### 3.7 Object-Oriented Models
          *(Provide structured textual specifications for: (a) Primary Use Cases with actors, preconditions, main flow, and exception flows; and (b) Loan Application State Transition lifecycle from submission to final decision/disbursement.)*

          ### Appendices
          #### Appendix A: Requirements Traceability Matrix (RTM)
          *(Render the complete, finalized 3-column Markdown table `| Requirement ID | Category | Short Description |` grouped strictly by FR, NFR, EI, and CON.)*
        """
        agent2_system_instruction = f"""
        You are a Senior Software Architect and SDLC Selection Expert.
        
        STRICT BOUNDARY - Available SDLC Models to choose from (SELECT EXACTLY ONE):
        1. Waterfall
        2. V-Shaped Model (Verification and Validation Model)
        3. Prototyping Model
        4. Incremental / Iterative Model
        5. Rapid Application Development (RAD)
        6. Spiral Model
        7. Agile Methodology

        Grounded SDLC Selection Decision Rules (Knowledge Base RAG):
        ---
        {sdlc_kb}
        ---

        STRICT OUTPUT FORMAT RULES:
        - Never use the word "coursework" anywhere in your response.
        - Do NOT number the section headings.
        - Output ONLY the following 3 sections using unnumbered Markdown level-3 headings (`###`) in this exact order (do NOT include workflow phases, quality gates, role assignments, or requirement-to-phase mappings):

          ### SDLC Selection Criteria Matrix
          *(Render a 2-column Markdown table with headers `| SDLC Selection Criteria | Project Observations & Analysis |` containing ONLY these exact 4 rows in the left column:
          1. **Requirements Characteristics**
          2. **Project Team Characteristics**
          3. **User Community Characteristics**
          4. **Project Type & Risk**
          In the right column, summarize the concrete observations derived from Agent 1's FRs, NFRs, EIs, and CONs.)*

          ### Recommended SDLC Model
          **[Exact Model Name from the 7 allowed models]**

          ### Software Engineering Justification
          *(Provide 6 bullet points comparing the recommended model against each of the other 6 models based on the observations in the matrix above. Format every bullet strictly with bold lead-ins like: `- **Superiority over [Model Name]:** [Explanation]`)*
        """

        with st.spinner("Compiling IEEE 830 SRS (Agent 1) & Evaluating SDLC Model (Agent 2)..."):
            try:
                client = genai.Client(api_key=api_key)

                compile_prompt = f"Compile the complete IEEE 830-1998 SRS from these gathered requirements:\n---\n{st.session_state.final_srs}\n---"
                compiled_srs = call_gemini_resilient(client, compile_prompt, agent1_compile_instruction)
                st.session_state.ieee_srs = compiled_srs
                log_to_db("Agent_1_IEEE830_Compiler", compile_prompt, compiled_srs)

                agent2_prompt = f"Analyze this finalized IEEE 830-1998 SRS from Agent 1:\n---\n{compiled_srs}\n---"
                agent2_response = call_gemini_resilient(client, agent2_prompt, agent2_system_instruction)
                
                st.session_state.sdlc_result = agent2_response
                st.session_state.is_finalized = True
                log_to_db("Agent_2_SDLC_Engine", agent2_prompt, agent2_response)
                save_artifact_to_db(compiled_srs, agent2_response)
                st.rerun()

            except Exception as e:
                st.error(f"Execution Error: {e}")

if st.session_state.ieee_srs:
    with st.expander("📄 Finalized IEEE 830-1998 Software Requirements Specification (SRS)", expanded=False):
        st.markdown(st.session_state.ieee_srs)

if st.session_state.sdlc_result:
    with st.expander("✅ Suitable SDLC Model Selection & Justification", expanded=False):
        st.markdown(st.session_state.sdlc_result)
    st.success("IEEE 830 SRS & SDLC Evaluation complete! Session artifacts and audit logs saved to 'se_project.db'.")