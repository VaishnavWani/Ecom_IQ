import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# ----------------------------------------------------------------------
# Numbered Canvas for "Page X of Y" and Running Header/Footer
# ----------------------------------------------------------------------
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
            # Suppress header and footer on cover page
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Running Header
        self.drawString(54, 750, "EcomIQ — System Architecture & Operations Manual")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)

        # Running Footer
        self.line(54, 50, 558, 50)
        self.setFont("Helvetica", 8)
        self.drawString(54, 38, "CONFIDENTIAL & PROPRIETARY — INTERNAL SYSTEMS DOCUMENTATION")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 38, page_str)
        self.restoreState()


def create_manual_pdf(filename="EcomIQ_System_Architecture_and_Operations_Manual.pdf", diagram_path=""):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0f172a")     # Slate 900
    SECONDARY = colors.HexColor("#1e293b")   # Slate 800
    ACCENT_BLUE = colors.HexColor("#2563eb") # Blue 600
    ACCENT_PURPLE = colors.HexColor("#7c3aed")# Violet 600
    BG_LIGHT = colors.HexColor("#f8fafc")    # Slate 50
    TEXT_DARK = colors.HexColor("#334155")   # Slate 700
    BORDER_COLOR = colors.HexColor("#e2e8f0")

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=PRIMARY,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=ACCENT_BLUE,
        spaceAfter=20
    )

    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b")
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceBefore=18,
        spaceAfter=10,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=ACCENT_PURPLE,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3_Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'Callout_Text',
        parent=body_style,
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e1b4b")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=TEXT_DARK
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=PRIMARY
    )

    story = []

    # ------------------------------------------------------------------
    # COVER / HEADER SECTION
    # ------------------------------------------------------------------
    story.append(Spacer(1, 20))
    story.append(Paragraph("EcomIQ Platform Manual", title_style))
    story.append(Paragraph("End-to-End System Architecture, Module Reference & Technology Rationale", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_BLUE, spaceBefore=0, spaceAfter=15))

    meta_text = "<b>Target Audience:</b> Technical Developers, Architects, & Non-Technical Stakeholders<br/>" \
                "<b>Author:</b> EcomIQ Engineering Team &nbsp;|&nbsp; <b>Version:</b> 2.4.0 &nbsp;|&nbsp; <b>Date:</b> July 2026<br/>" \
                "<b>Stack:</b> Python · Apache Kafka · PySpark · PostgreSQL · FastAPI · FastMCP · Gemini AI · Docker"
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 15))

    # Executive Summary Callout Box
    summary_box_data = [[
        Paragraph("<b>EXECUTIVE SUMMARY & SYSTEM PURPOSE</b><br/><br/>"
                  "<b>EcomIQ</b> is a real-time, event-driven e-commerce analytics and operational intelligence platform. "
                  "It continuously simulates, ingests, and processes streaming transactional events (orders, payments, shipments, returns, stock moves, user clicks) "
                  "across a 14-table relational database schema. On top of this data pipeline, EcomIQ features an autonomous Multi-Agent AI System "
                  "that converts plain English questions (e.g., <i>'Why are payments failing in West India?'</i>) into dynamic SQL filters, "
                  "executes statistical anomaly detection across 17,200+ records, and synthesizes root-cause executive markdown reports in seconds.", callout_style)
    ]]
    summary_table = Table(summary_box_data, colWidths=[504])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # ------------------------------------------------------------------
    # SECTION 1: ARCHITECTURE OVERVIEW & DIAGRAM
    # ------------------------------------------------------------------
    story.append(Paragraph("1. High-Level Architecture & Block Diagram", h1_style))
    story.append(Paragraph(
        "The EcomIQ platform is built using a microservice container architecture hosted on an isolated Docker network named "
        "<code>ecom_iq_network</code>. Below is the full block diagram illustrating how synthetic data flows from generation to storage, "
        "and how user queries pass through the AI pipeline.", body_style
    ))
    story.append(Spacer(1, 6))

    if diagram_path and os.path.exists(diagram_path):
        try:
            # Insert the generated architecture diagram image
            img = Image(diagram_path, width=6.8*inch, height=4.2*inch)
            story.append(img)
            story.append(Spacer(1, 6))
            story.append(Paragraph("<i>Figure 1.1: EcomIQ End-to-End System Block Diagram showing container networks, ports, and agent pipelines.</i>", ParagraphStyle('Caption', parent=body_style, fontSize=8, fontName='Helvetica-Oblique', textColor=colors.HexColor("#64748b"), alignment=1)))
        except Exception as e:
            story.append(Paragraph(f"<i>[Diagram Image Load Error: {e}]</i>", body_style))
    story.append(Spacer(1, 15))

    # ------------------------------------------------------------------
    # SECTION 2: CONTAINER & MODULE DEEP DIVE
    # ------------------------------------------------------------------
    story.append(Paragraph("2. Container & Module Deep Dive", h1_style))
    story.append(Paragraph(
        "EcomIQ consists of 6 distinct services operating across data generation, streaming, processing, storage, API serving, and UI rendering.", body_style
    ))

    # Module 1: Data Service
    story.append(Paragraph("2.1 Data Service (ecom_iq_producer)", h2_style))
    story.append(Paragraph(
        "<b>What it does:</b> Acts as the synthetic event generator for the entire system. It runs <code>generator.py</code> and <code>producer.py</code> in an infinite loop. "
        "It constructs 14 distinct JSON event payloads representing real-world e-commerce activities: customer profile updates, address registrations, "
        "placed orders, line items, payment processing attempts, courier shipments, product returns, warehouse stock transactions, and website clickstream events.", body_style
    ))
    story.append(Paragraph("• <b>Why Synthetic Data?</b> Allows end-to-end stress testing of streaming pipelines and AI analytics without requiring live production API integrations.", bullet_style))
    story.append(Paragraph("• <b>Internal Operation:</b> Uses Python's standard <code>uuid</code>, <code>random</code>, and <code>datetime</code> libraries to deterministically push events to Kafka topics over <code>ecom_iq_kafka:29092</code>.", bullet_style))

    # Module 2: Apache Zookeeper
    story.append(Paragraph("2.2 Apache Zookeeper (ecom_iq_zookeeper)", h2_style))
    story.append(Paragraph(
        "<b>What it does:</b> Manages and coordinates the Apache Kafka broker cluster. It maintains cluster metadata, tracks active broker nodes, "
        "and handles topic partition leader election.", body_style
    ))
    story.append(Paragraph("• <b>Port 2181:</b> Exposed internally and on the host for client coordination and health monitoring.", bullet_style))

    # Module 3: Apache Kafka
    story.append(Paragraph("2.3 Apache Kafka (ecom_iq_kafka)", h2_style))
    story.append(Paragraph(
        "<b>What it does:</b> Serves as the central high-throughput event streaming backbone. It maintains 14 separate Kafka topics (one per database table).", body_style
    ))
    story.append(Paragraph("• <b>Dual Listener Configuration:</b>", h3_style))
    story.append(Paragraph("  - <b>Internal Listener (port 29092):</b> Used by Docker containers (Producer, Spark Consumer, API) on <code>ecom_iq_network</code>.", bullet_style))
    story.append(Paragraph("  - <b>Host Listener (port 9092):</b> Allows external tools on Windows to inspect topics and consume raw messages.", bullet_style))

    # Module 4: Spark Service
    story.append(Paragraph("2.4 Spark Service (ecom_iq_consumer)", h2_style))
    story.append(Paragraph(
        "<b>What it does:</b> Runs a PySpark structured streaming job (<code>kafka_consumer.py</code>). It subscribes to all 14 Kafka topics, "
        "deserializes JSON streams in micro-batches, validates schema structures, and writes transformed records directly into PostgreSQL via JDBC.", body_style
    ))
    story.append(Paragraph("• <b>JDBC Target:</b> <code>jdbc:postgresql://ecommerce_iq_db:5432/postgres</code>.", bullet_style))

    # Module 5: PostgreSQL Database
    story.append(Paragraph("2.5 PostgreSQL Database (ecommerce_iq_db)", h2_style))
    story.append(Paragraph(
        "<b>What it does:</b> The primary relational data warehouse storing 17,250+ historical and real-time records formatted across 14 tables.", body_style
    ))
    story.append(Paragraph("• <b>Schema Breakdown:</b> Divided into 7 Dimension Tables (reference/lookup) and 7 Fact Tables (transactional).", bullet_style))
    story.append(Paragraph("  - <i>Dimension Tables:</i> <code>dim_customers</code>, <code>dim_customer_addresses</code>, <code>dim_regions</code>, <code>dim_skus</code>, <code>dim_categories</code>, <code>dim_payment_methods</code>, <code>dim_warehouses</code>.", bullet_style))
    story.append(Paragraph("  - <i>Fact Tables:</i> <code>fact_order_headers</code>, <code>fact_order_lines</code>, <code>fact_payments</code>, <code>fact_shipments</code>, <code>fact_returns</code>, <code>fact_inventory_transactions</code>, <code>fact_user_clickstream</code>.", bullet_style))

    # Module 6: API Service & AI Agents
    story.append(Paragraph("2.6 API Service & AI Agents (ecom_iq_api)", h2_style))
    story.append(Paragraph(
        "<b>What it does:</b> A dual-server container running both a REST API (FastAPI on port 8000) and an MCP Server (FastMCP on port 9500). "
        "It houses the Multi-Agent AI system:", body_style
    ))
    story.append(Paragraph("• <b>FetcherAgent (<code>agents/fetcher_agent.py</code>):</b> Uses Gemini AI to extract structured scope parameters (region, payment method, courier, date ranges) from natural language user prompts into JSON.", bullet_style))
    story.append(Paragraph("• <b>AnalyticsEngine (<code>analytics_engine.py</code>):</b> Converts scope JSON into parameterized SQL WHERE clauses across all 14 tables, executes queries via <code>psycopg2</code>, and runs a statistical Signal Detector algorithm (flagging anomalies where metrics deviate >1.5x or <0.5x from baseline averages).", bullet_style))
    story.append(Paragraph("• <b>RunnerAgent (<code>agents/runner_agent.py</code>):</b> Takes the SQL execution data and signal anomalies, feeding them back to Gemini AI to author a 6-section executive investigation report in markdown.", bullet_style))
    story.append(Paragraph("• <b>SupervisorAgent (<code>agents/supervisor_agent.py</code>):</b> Orchestrates the end-to-end flow from query input to final report output.", bullet_style))

    # Module 7: Spatial Glass Frontend UI
    story.append(Paragraph("2.7 Spatial Glass Frontend UI (frontend/)", h2_style))
    story.append(Paragraph(
        "<b>What it does:</b> A modular, zero-build client interface inspired by iOS liquid glassmorphism and spatial computing designs. "
        "It features animated parallax space nebula canvases, glowing lavender focus rings, auto-resizing text input, typing step indicators, and live markdown rendering.", body_style
    ))
    story.append(Spacer(1, 15))

    # ------------------------------------------------------------------
    # SECTION 3: PORT MAPPING & NETWORK REFERENCE TABLE
    # ------------------------------------------------------------------
    story.append(Paragraph("3. Port Mapping & Network Reference", h1_style))
    story.append(Paragraph(
        "Every network port in EcomIQ is explicitly configured to prevent host port collisions (specifically with native Windows PostgreSQL installations).", body_style
    ))

    port_table_data = [
        [Paragraph("Port", table_header_style), Paragraph("Container / Service", table_header_style), Paragraph("Accessibility", table_header_style), Paragraph("Protocol / Role", table_header_style), Paragraph("Why This Specific Port?", table_header_style)],
        [Paragraph("<b>2181</b>", table_cell_bold), Paragraph("ecom_iq_zookeeper", table_cell_style), Paragraph("Internal & Host", table_cell_style), Paragraph("TCP / Zookeeper Client", table_cell_style), Paragraph("Standard default port for Zookeeper cluster coordination.", table_cell_style)],
        [Paragraph("<b>29092</b>", table_cell_bold), Paragraph("ecom_iq_kafka", table_cell_style), Paragraph("Internal Docker", table_cell_style), Paragraph("PLAINTEXT / Broker", table_cell_style), Paragraph("Dedicated internal listener preventing IP collision with host OS.", table_cell_style)],
        [Paragraph("<b>9092</b>", table_cell_bold), Paragraph("ecom_iq_kafka", table_cell_style), Paragraph("Host (localhost)", table_cell_style), Paragraph("PLAINTEXT_HOST / Kafka", table_cell_style), Paragraph("Standard external Kafka listener port for Windows client tools.", table_cell_style)],
        [Paragraph("<b>5432</b>", table_cell_bold), Paragraph("ecommerce_iq_db", table_cell_style), Paragraph("Internal Docker", table_cell_style), Paragraph("PostgreSQL Database", table_cell_style), Paragraph("Default internal PostgreSQL listener for PySpark & FastAPI.", table_cell_style)],
        [Paragraph("<b>5431</b>", table_cell_bold), Paragraph("ecommerce_iq_db", table_cell_style), Paragraph("Host (localhost)", table_cell_style), Paragraph("PostgreSQL Host Map", table_cell_style), Paragraph("<b>Crucial:</b> Mapped to 5431 on host to avoid conflict with native Windows PG on 5432.", table_cell_style)],
        [Paragraph("<b>8000</b>", table_cell_bold), Paragraph("ecom_iq_api", table_cell_style), Paragraph("Host (localhost)", table_cell_style), Paragraph("HTTP / FastAPI REST", table_cell_style), Paragraph("Primary web server serving <code>/investigate</code> endpoint & Swagger UI.", table_cell_style)],
        [Paragraph("<b>9500</b>", table_cell_bold), Paragraph("ecom_iq_api", table_cell_style), Paragraph("Host (localhost)", table_cell_style), Paragraph("HTTP / FastMCP SSE", table_cell_style), Paragraph("Dedicated Model Context Protocol server endpoint for external AI agents.", table_cell_style)],
    ]

    port_table = Table(port_table_data, colWidths=[40, 95, 75, 100, 194])
    port_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(port_table)
    story.append(Spacer(1, 15))

    # ------------------------------------------------------------------
    # SECTION 4: TECHNOLOGY CHOICE & RATIONALE MATRIX
    # ------------------------------------------------------------------
    story.append(Paragraph("4. Technology Selection Rationale Matrix", h1_style))
    story.append(Paragraph(
        "Each technology in EcomIQ was chosen based on specific architectural trade-offs compared to industry alternatives:", body_style
    ))

    tech_table_data = [
        [Paragraph("Component", table_header_style), Paragraph("Chosen Technology", table_header_style), Paragraph("Alternative Considered", table_header_style), Paragraph("Why Chosen? (Decision Rationale)", table_header_style)],
        [
            Paragraph("<b>Message Streaming</b>", table_cell_bold),
            Paragraph("<b>Apache Kafka</b>", table_cell_style),
            Paragraph("RabbitMQ / AWS SQS", table_cell_style),
            Paragraph("Kafka provides log immutability, message replayability, and multi-consumer topic partition scaling required for stream analytics.", table_cell_style)
        ],
        [
            Paragraph("<b>Stream Processing</b>", table_cell_bold),
            Paragraph("<b>PySpark</b>", table_cell_style),
            Paragraph("Apache Flink / Pandas", table_cell_style),
            Paragraph("PySpark offers fault-tolerant structured streaming, micro-batch windowing, and built-in JDBC writers for PostgreSQL without memory caps.", table_cell_style)
        ],
        [
            Paragraph("<b>Data Storage</b>", table_cell_bold),
            Paragraph("<b>PostgreSQL</b>", table_cell_style),
            Paragraph("MongoDB / Snowflake", table_cell_style),
            Paragraph("ACID transactional compliance and ultra-fast multi-table SQL JOIN capabilities required for complex root-cause analytics across 14 tables.", table_cell_style)
        ],
        [
            Paragraph("<b>API Framework</b>", table_cell_bold),
            Paragraph("<b>FastAPI</b>", table_cell_style),
            Paragraph("Flask / Django", table_cell_style),
            Paragraph("Asynchronous ASGI performance (uvicorn), automatic OpenAPI documentation, and strict Pydantic request validation out of the box.", table_cell_style)
        ],
        [
            Paragraph("<b>AI Infrastructure</b>", table_cell_bold),
            Paragraph("<b>Google Gemini</b>", table_cell_style),
            Paragraph("OpenAI GPT-4 / Claude", table_cell_style),
            Paragraph("Ultra-fast inference latency, large context window for raw SQL dataset inspection, and native structured JSON schema generation.", table_cell_style)
        ],
        [
            Paragraph("<b>Agent Tool Protocol</b>", table_cell_bold),
            Paragraph("<b>FastMCP</b>", table_cell_style),
            Paragraph("Custom REST / LangChain", table_cell_style),
            Paragraph("Standardized Anthropic Model Context Protocol allowing any external AI agent to inspect and call analytics tools via SSE.", table_cell_style)
        ],
    ]

    tech_table = Table(tech_table_data, colWidths=[80, 85, 95, 244])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 15))

    # ------------------------------------------------------------------
    # SECTION 5: DATA & QUERY FLOW STEP-BY-STEP
    # ------------------------------------------------------------------
    story.append(Paragraph("5. Step-by-Step Data & Query Flow", h1_style))

    story.append(Paragraph("5.1 Real-Time Streaming Data Ingestion Flow", h2_style))
    story.append(Paragraph("1. <b>Event Trigger:</b> <code>data_service/main.py</code> invokes <code>generator.py</code> to construct synthetic JSON event objects.", bullet_style))
    story.append(Paragraph("2. <b>Kafka Publish:</b> <code>producer.py</code> sends payloads to designated Kafka topics (e.g., <code>fact_payments</code> topic).", bullet_style))
    story.append(Paragraph("3. <b>Stream Processing:</b> <code>spark_service/kafka_consumer.py</code> reads micro-batches from Kafka via <code>ecom_iq_kafka:29092</code>.", bullet_style))
    story.append(Paragraph("4. <b>DB Persist:</b> PySpark formats rows and commits inserts to PostgreSQL (<code>ecommerce_iq_db:5432</code>).", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("5.2 Natural Language AI Investigation Flow", h2_style))
    story.append(Paragraph("1. <b>User Input:</b> User types <i>'Why are payments failing in West India?'</i> in <code>frontend/index.html</code>.", bullet_style))
    story.append(Paragraph("2. <b>HTTP POST:</b> Frontend posts JSON payload <code>{\"query\": \"...\"}</code> to <code>http://localhost:8000/investigate</code>.", bullet_style))
    story.append(Paragraph("3. <b>FastAPI Entry:</b> <code>api_service/main.py</code> passes the prompt to <code>SupervisorAgent.investigate()</code>.", bullet_style))
    story.append(Paragraph("4. <b>Scope Extraction:</b> <code>FetcherAgent</code> calls Gemini API (<code>gemini-3.6-flash</code>) to extract: <code>{\"region\": \"West India\", \"payment_status\": \"failed\"}</code>.", bullet_style))
    story.append(Paragraph("5. <b>SQL Analytics:</b> <code>AnalyticsEngine</code> converts scope into dynamic SQL queries with <code>WHERE dr.region_name = 'West India'</code> across all 14 tables, returning aggregated row counts, failure rates, and triggering the statistical signal detector.", bullet_style))
    story.append(Paragraph("6. <b>Report Generation:</b> <code>RunnerAgent</code> sends SQL metric summaries to Gemini API to compose a structured 6-section markdown report.", bullet_style))
    story.append(Paragraph("7. <b>UI Render:</b> FastAPI returns the report JSON, and the Spatial Glass UI renders the report inside an animated floating glass slab.", bullet_style))

    story.append(Spacer(1, 15))

    # ------------------------------------------------------------------
    # SECTION 6: MODULE INVOCATION MECHANICS & OPERATIONS MANUAL
    # ------------------------------------------------------------------
    story.append(Paragraph("6. Module Invocation & Operations Manual", h1_style))

    story.append(Paragraph("6.1 Code Invocation Hierarchy", h2_style))
    story.append(Paragraph(
        "The table below details how source code files invoke each other during system execution:", body_style
    ))

    code_flow_data = [
        [Paragraph("Caller Module", table_header_style), Paragraph("Callee Module / Target Function", table_header_style), Paragraph("Interaction Purpose", table_header_style)],
        [Paragraph("<code>frontend/js/app.js</code>", table_cell_style), Paragraph("<code>frontend/js/api.js</code> → <code>fetchInvestigation()</code>", table_cell_style), Paragraph("Initiates HTTP POST request to API endpoint.", table_cell_style)],
        [Paragraph("<code>api_service/main.py</code>", table_cell_style), Paragraph("<code>SupervisorAgent.investigate()</code>", table_cell_style), Paragraph("Hands off user prompt to AI orchestration supervisor.", table_cell_style)],
        [Paragraph("<code>SupervisorAgent</code>", table_cell_style), Paragraph("<code>FetcherAgent.extract_scope()</code>", table_cell_style), Paragraph("Queries Gemini LLM to extract JSON filter parameters.", table_cell_style)],
        [Paragraph("<code>SupervisorAgent</code>", table_cell_style), Paragraph("<code>AnalyticsEngine.run()</code>", table_cell_style), Paragraph("Executes SQL queries against PostgreSQL DB.", table_cell_style)],
        [Paragraph("<code>AnalyticsEngine</code>", table_cell_style), Paragraph("<code>Database.query()</code> via <code>psycopg2</code>", table_cell_style), Paragraph("Sends raw SQL string commands to PostgreSQL.", table_cell_style)],
        [Paragraph("<code>SupervisorAgent</code>", table_cell_style), Paragraph("<code>RunnerAgent.generate_report()</code>", table_cell_style), Paragraph("Sends SQL data to Gemini LLM to write final report.", table_cell_style)],
    ]

    code_table = Table(code_flow_data, colWidths=[130, 174, 200])
    code_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(code_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph("6.2 Operations Cheat Sheet", h2_style))
    story.append(Paragraph("• <b>Start Entire Platform:</b>", h3_style))
    story.append(Paragraph("  <code>docker compose up -d</code><br/>"
                           "  <code>docker start ecommerce_iq_db</code><br/>"
                           "  <code>docker network connect ecom_iq_network ecommerce_iq_db</code>", bullet_style))

    story.append(Paragraph("• <b>Switch Gemini AI Models:</b>", h3_style))
    story.append(Paragraph("  Edit <code>model=\"gemini-3.6-flash\"</code> in <code>api_service/agents/fetcher_agent.py</code> and <code>runner_agent.py</code>.<br/>"
                           "  Hot-patch container: <code>docker cp api_service/agents/fetcher_agent.py ecom_iq_api:/app/agents/fetcher_agent.py</code> and <code>docker restart ecom_iq_api</code>.", bullet_style))

    story.append(Paragraph("• <b>Access User Interfaces:</b>", h3_style))
    story.append(Paragraph("  - <b>Spatial Glass Chat UI:</b> Double click <code>frontend/index.html</code> in any web browser.<br/>"
                           "  - <b>FastAPI Swagger Docs:</b> Open <code>http://localhost:8000/docs</code>.<br/>"
                           "  - <b>PostgreSQL pgAdmin Connection:</b> Host <code>localhost</code>, Port <code>5431</code>, DB <code>postgres</code>, User <code>postgres</code>, Password <code>bibtya1000</code>.", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF manual: {filename}")


if __name__ == "__main__":
    diag_file = r"C:\Users\Shubham\.gemini\antigravity-ide\brain\83e6dd3a-6318-459f-a614-a16eb376e044\ecomiq_architecture_diagram_1784996669916.png"
    out_pdf = r"C:\Users\Shubham\Desktop\Ecom_iq\EcomIQ_System_Architecture_and_Operations_Manual.pdf"
    create_manual_pdf(out_pdf, diag_file)
