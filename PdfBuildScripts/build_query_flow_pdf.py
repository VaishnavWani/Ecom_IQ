import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Header
        self.drawString(54, 750, "EcomIQ — Query Processing & Multi-Agent Architecture Guide")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)

        # Footer
        self.line(54, 50, 558, 50)
        self.setFont("Helvetica", 8)
        self.drawString(54, 38, "TECHNICAL GUIDE — INTERNAL AGENT ARCHITECTURE")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 38, page_str)
        self.restoreState()


def create_query_flow_pdf(filename="EcomIQ_Query_Processing_and_Agent_Guide.pdf", diagram_path=""):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    PRIMARY = colors.HexColor("#0f172a")
    SECONDARY = colors.HexColor("#1e293b")
    ACCENT_BLUE = colors.HexColor("#2563eb")
    ACCENT_PURPLE = colors.HexColor("#7c3aed")
    BG_LIGHT = colors.HexColor("#f8fafc")
    TEXT_DARK = colors.HexColor("#334155")
    BORDER_COLOR = colors.HexColor("#e2e8f0")

    title_style = ParagraphStyle(
        'Title', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=24, leading=28, textColor=PRIMARY, spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=13, leading=16, textColor=ACCENT_BLUE, spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'H1', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=PRIMARY, spaceBefore=16, spaceAfter=8, keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=ACCENT_PURPLE, spaceBefore=12, spaceAfter=6, keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.5, leading=14, textColor=TEXT_DARK, spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet', parent=body_style,
        leftIndent=15, firstLineIndent=-10, spaceAfter=4
    )

    code_block_style = ParagraphStyle(
        'CodeBlock', parent=styles['Normal'],
        fontName='Courier', fontSize=8.5, leading=11, textColor=colors.HexColor("#1e1b4b")
    )

    table_header = ParagraphStyle('TH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)
    table_cell = ParagraphStyle('TC', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11, textColor=TEXT_DARK)
    table_cell_bold = ParagraphStyle('TCB', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=PRIMARY)

    story = []

    # Title Section
    story.append(Paragraph("EcomIQ Query Processing & Agent Architecture", title_style))
    story.append(Paragraph("Detailed Guide on Query Execution Lifecycle and Agent-to-Agent (A2A) Protocols", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_BLUE, spaceBefore=0, spaceAfter=12))

    meta_text = "<b>Document Type:</b> Engineering Lifecycle Specification &nbsp;|&nbsp; <b>Version:</b> 2.4.0<br/>" \
                "<b>Scope:</b> Natural Language Query Flow, A2A Protocol, FastAPI Routing, SQL Analytics & Report Authoring"
    story.append(Paragraph(meta_text, body_style))
    story.append(Spacer(1, 10))

    # SECTION 1: INTRODUCTION & PHILOSOPHY
    story.append(Paragraph("1. System Design Philosophy & Architectural Overview", h1_style))
    story.append(Paragraph(
        "The primary challenge in conversational business intelligence is converting high-level, ambiguous human questions "
        "(e.g., <i>'Why are payments failing in West India?'</i>) into precise database queries and actionable executive reports "
        "without incurring infinite LLM loops or severe latency.", body_style
    ))
    story.append(Paragraph(
        "To achieve both high reliability and sub-second execution, EcomIQ implements a <b>hybrid multi-agent architecture</b>. "
        "It decouples intent extraction (LLM), deterministic database analytics (SQL + Python), and narrative synthesis (LLM) into dedicated, specialized modules.", body_style
    ))
    story.append(Spacer(1, 10))

    # SECTION 2: A2A PROTOCOL & INTERACTION MODELS
    story.append(Paragraph("2. Agent-to-Agent (A2A) Interaction Breakdown", h1_style))
    story.append(Paragraph(
        "EcomIQ utilizes two distinct Agent-to-Agent interaction models operating at different boundaries of the software architecture:", body_style
    ))

    story.append(Paragraph("2.1 Internal In-Memory A2A Orchestration", h2_style))
    story.append(Paragraph(
        "Inside the core <code>api_service</code> container, agents interact via a synchronous, in-memory supervisor pattern managed by <code>SupervisorAgent</code> (<code>agents/supervisor_agent.py</code>). "
        "Rather than relying on unpredictable chat-based message queues between agents, the Supervisor executes a strict, deterministic sequence: "
        "<code>FetcherAgent</code> → <code>AnalyticsEngine</code> → <code>RunnerAgent</code>. Data is passed as typed Python dictionaries and Pydantic primitives, guaranteeing 0% loop failure rate and maximum speed.", body_style
    ))

    story.append(Paragraph("2.2 External Network A2A Protocol (Model Context Protocol - MCP)", h2_style))
    story.append(Paragraph(
        "At the external network boundary, EcomIQ exposes an authentic <b>Agent-to-Agent (A2A) protocol</b> over HTTP/SSE via <b>FastMCP on Port 9500</b> (<code>mcp_server.py</code>). "
        "This adheres strictly to Anthropic's open Model Context Protocol standard, allowing any autonomous third-party AI agent (e.g., Claude Desktop, Cursor IDE, AutoGen bots) to discover, inspect, and execute EcomIQ analytics tools over the wire.", body_style
    ))
    story.append(Spacer(1, 10))

    # SECTION 3: SEQUENCE FLOW DIAGRAM
    story.append(Paragraph("3. Query Execution Sequence Diagram", h1_style))
    story.append(Paragraph(
        "The diagram below details the 9-step chronological flow of a user query through every container and agent in the platform:", body_style
    ))
    story.append(Spacer(1, 6))

    if diagram_path and os.path.exists(diagram_path):
        try:
            img = Image(diagram_path, width=6.8*inch, height=4.2*inch)
            story.append(img)
            story.append(Spacer(1, 6))
            story.append(Paragraph("<i>Figure 3.1: Complete End-to-End User Query Processing Flow from Chat UI to PostgreSQL and Gemini LLM.</i>", ParagraphStyle('Cap', parent=body_style, fontSize=8, fontName='Helvetica-Oblique', textColor=colors.HexColor("#64748b"), alignment=1)))
        except Exception as e:
            story.append(Paragraph(f"<i>[Diagram Image Load Error: {e}]</i>", body_style))
    story.append(Spacer(1, 12))

    # SECTION 4: STEP-BY-STEP DETAILED PROCESSING STAGES
    story.append(Paragraph("4. Detailed Processing Stages (Steps 1 through 9)", h1_style))

    stages = [
        ("Step 1: UI Request Dispatch", "Frontend (frontend/js/app.js & api.js)",
         "User enters prompt into Spatial Glass UI. JavaScript captures input and fires HTTP POST to http://localhost:8000/investigate with body: {\"query\": \"...\"}."),
        ("Step 2: FastAPI Routing", "API Gateway (api_service/main.py)",
         "FastAPI validates request headers/CORS, parses JSON payload via Pydantic schema, and routes execution to SupervisorAgent().investigate(user_query)."),
        ("Step 3: Scope Extraction (AI)", "Fetcher Agent (agents/fetcher_agent.py)",
         "Supervisor calls FetcherAgent.extract_scope(query). The Fetcher sends a system-instructed prompt to Gemini API (gemini-3.6-flash) returning JSON scope: {\"region\": \"West India\", \"payment_status\": \"failed\"}."),
        ("Step 4: Engine Invocation", "Supervisor Orchestrator",
         "Supervisor receives JSON scope dictionary and passes it directly into the deterministic analytical engine: InvestigationEngine.run(scope=scope)."),
        ("Step 5: SQL Execution", "Analytics Engine (analytics_engine.py → Postgres)",
         "ScopeFilter converts scope into dynamic SQL WHERE clauses. psycopg2 connects to PostgreSQL (ecommerce_iq_db:5432) and executes queries across 14 tables (dim & fact) over 17,250+ records."),
        ("Step 6: Signal Detection", "Analytics Engine (analytics_engine.py)",
         "Engine computes metric baselines and runs the statistical Signal Detector algorithm. Flagged anomalies (>1.5x or <0.5x baseline) are attached to dataset."),
        ("Step 7: Executive Report Generation (AI)", "Runner Agent (agents/runner_agent.py)",
         "Supervisor passes extracted scope, SQL dataset, and signal anomaly flags to RunnerAgent. The agent prompts Gemini API to author a formal 6-section Markdown Executive Report."),
        ("Step 8 & 9: UI Rendering", "FastAPI → Frontend UI",
         "FastAPI packages report markdown, scope chips, and query metadata into JSON response. Chat UI receives 200 OK, clears typing indicator, and renders liquid glass response card.")
    ]

    for title, loc, desc in stages:
        story.append(Paragraph(f"<b>{title}</b> — <i>{loc}</i>", h2_style))
        story.append(Paragraph(desc, body_style))

    story.append(Spacer(1, 10))

    # SECTION 5: PIPELINE COMPONENT CODE MATRIX
    story.append(Paragraph("5. Pipeline Component Code & Data Contract Matrix", h1_style))

    contract_data = [
        [Paragraph("Pipeline Phase", table_header), Paragraph("Executing Code Module", table_header), Paragraph("Input Data Contract", table_header), Paragraph("Output Data Contract", table_header)],
        [
            Paragraph("<b>1. Dispatch</b>", table_cell_bold),
            Paragraph("<code>frontend/js/app.js</code>", table_cell),
            Paragraph("User keystroke / text input", table_cell),
            Paragraph("JSON <code>{\"query\": str}</code>", table_cell)
        ],
        [
            Paragraph("<b>2. Scope Extract</b>", table_cell_bold),
            Paragraph("<code>FetcherAgent</code> + Gemini", table_cell),
            Paragraph("Natural language query string", table_cell),
            Paragraph("Structured JSON Scope Dict", table_cell)
        ],
        [
            Paragraph("<b>3. Analytics</b>", table_cell_bold),
            Paragraph("<code>AnalyticsEngine</code> + PG", table_cell),
            Paragraph("JSON Scope Dict", table_cell),
            Paragraph("SQL Dict + Anomaly Signals", table_cell)
        ],
        [
            Paragraph("<b>4. Report Synthesis</b>", table_cell_bold),
            Paragraph("<code>RunnerAgent</code> + Gemini", table_cell),
            Paragraph("Scope Dict + SQL Analytics", table_cell),
            Paragraph("6-Section Markdown Report", table_cell)
        ],
        [
            Paragraph("<b>5. Rendering</b>", table_cell_bold),
            Paragraph("<code>frontend/js/ui.js</code>", table_cell),
            Paragraph("JSON API Response", table_cell),
            Paragraph("Rendered Spatial Glass UI Card", table_cell)
        ],
    ]

    contract_table = Table(contract_data, colWidths=[80, 130, 144, 150])
    contract_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(contract_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF guide: {filename}")


if __name__ == "__main__":
    diag_file = r"C:\Users\Shubham\.gemini\antigravity-ide\brain\83e6dd3a-6318-459f-a614-a16eb376e044\ecomiq_query_processing_flow_1785135083316.png"
    out_pdf = r"C:\Users\Shubham\Desktop\Ecom_iq\EcomIQ_Query_Processing_and_Agent_Guide.pdf"
    create_query_flow_pdf(out_pdf, diag_file)
