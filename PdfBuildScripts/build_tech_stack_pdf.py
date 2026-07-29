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
        self.drawString(54, 750, "EcomIQ — Module-Wise Technology Stack Reference")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)

        # Footer
        self.line(54, 50, 558, 50)
        self.setFont("Helvetica", 8)
        self.drawString(54, 38, "TECHNICAL SPECIFICATION — MODULE TECHNOLOGY DEEP DIVE")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 38, page_str)
        self.restoreState()


def create_tech_stack_pdf(filename="EcomIQ_Technology_Stack_Reference.pdf", diagram_path=""):
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

    table_header = ParagraphStyle('TH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)
    table_cell = ParagraphStyle('TC', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11, textColor=TEXT_DARK)
    table_cell_bold = ParagraphStyle('TCB', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=PRIMARY)

    story = []

    # Title Section
    story.append(Paragraph("EcomIQ Technology Stack Reference", title_style))
    story.append(Paragraph("Module-by-Module Technology Specifications, Functional Roles, and Selection Rationale", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT_BLUE, spaceBefore=0, spaceAfter=12))

    meta_text = "<b>Document Type:</b> Architecture & Technology Reference Manual &nbsp;|&nbsp; <b>Version:</b> 2.4.0<br/>" \
                "<b>Coverage:</b> All 7 System Modules, Libraries, Frameworks, Protocols, and Infrastructure Tools"
    story.append(Paragraph(meta_text, body_style))
    story.append(Spacer(1, 10))

    # SECTION 1: VISUAL DIAGRAM
    story.append(Paragraph("1. System Technology Stack Visual Map", h1_style))
    story.append(Paragraph(
        "Below is the complete module-wise technology stack diagram for EcomIQ, mapping every library, framework, "
        "database, broker, and protocol to its corresponding container layer.", body_style
    ))
    story.append(Spacer(1, 6))

    if diagram_path and os.path.exists(diagram_path):
        try:
            img = Image(diagram_path, width=6.8*inch, height=4.2*inch)
            story.append(img)
            story.append(Spacer(1, 6))
            story.append(Paragraph("<i>Figure 1.1: EcomIQ Module-Wise Technology Stack Diagram showing all tools, versions, and relationships.</i>", ParagraphStyle('Cap', parent=body_style, fontSize=8, fontName='Helvetica-Oblique', textColor=colors.HexColor("#64748b"), alignment=1)))
        except Exception as e:
            story.append(Paragraph(f"<i>[Diagram Image Load Error: {e}]</i>", body_style))
    story.append(Spacer(1, 12))

    # SECTION 2: MODULE-BY-MODULE BREAKDOWN
    story.append(Paragraph("2. Module-by-Module Technology Deep Dive", h1_style))

    modules_data = [
        ("2.1 Data Generation Module (data_service/)", [
            ("Python 3.11", "Core runtime environment.", "Chosen for rich data science libraries and rapid scripting capability."),
            ("Python Standard Libraries (uuid, random, datetime)", "Built-in generation utilities.", "Generates static and transient random transactional values, keys, and timestamps deterministically."),
            ("kafka-python", "Apache Kafka client for Python.", "Lightweight, pure-Python producer client for publishing JSON records.")
        ]),
        ("2.2 Message Streaming Broker Module (ecom_iq_kafka & ecom_iq_zookeeper)", [
            ("Apache Kafka 7.5.0", "Distributed event streaming platform.", "Provides log immutability, high throughput, and message replay across 14 topics."),
            ("Apache Zookeeper 7.5.0", "Cluster coordination service.", "Manages Kafka broker state, topic metadata, and leader elections.")
        ]),
        ("2.3 Stream Processing Module (spark_service/)", [
            ("Apache Spark / PySpark", "Distributed analytics processing framework.", "Executes parallel micro-batch transformations over Kafka streams."),
            ("Spark Structured Streaming", "Declarative stream processing engine.", "Ensures fault-tolerant, exactly-once processing semantics."),
            ("PostgreSQL JDBC Driver", "Java Database Connectivity driver.", "High-throughput parallel writer connector for PostgreSQL database ingestion.")
        ]),
        ("2.4 Relational Database Storage Module (ecommerce_iq_db)", [
            ("PostgreSQL 15", "Relational ACID SQL database.", "Provides strict relational integrity across 14 tables (7 Dim + 7 Fact) and fast SQL JOINs."),
            ("SQL Schema Engine", "Structured Query Language.", "Optimized indexes on regions, couriers, payment status, and order IDs across 17,250+ rows.")
        ]),
        ("2.5 API Server & Multi-Agent AI Module (api_service/)", [
            ("FastAPI 0.140.0", "High-performance Python web framework.", "Serves asynchronous REST API endpoints (/investigate) with automatic Swagger docs."),
            ("Uvicorn 0.51.0", "Lightning-fast ASGI web server.", "Handles asynchronous request routing on port 8000 and port 9500."),
            ("Google Gemini API (google-genai)", "LLM AI Engine (gemini-3.6-flash).", "Extracts JSON search scope from natural language and synthesizes executive reports."),
            ("FastMCP 3.4.4", "Model Context Protocol framework.", "Exposes 8 specialized analytics tools to external AI agents over SSE (Port 9500)."),
            ("psycopg2-binary 2.9.12", "PostgreSQL database adapter.", "Low-level C-optimized Python driver for raw SQL execution in AnalyticsEngine."),
            ("Pydantic", "Data validation library.", "Enforces strict JSON schema validation for HTTP requests and AI agent outputs.")
        ]),
        ("2.6 Spatial Glass Frontend UI Module (frontend/)", [
            ("HTML5 & Vanilla JS (ES6+)", "Zero-build web frontend.", "Lightweight DOM manipulation without heavy React/Vue framework overhead."),
            ("Vanilla CSS3", "Modern styling engine.", "Powers iOS spatial glassmorphism, backdrop-filter blur(40px), 3D perspective transforms, and space canvas."),
            ("Marked.js", "Client-side Markdown renderer.", "Converts AI executive markdown reports into HTML instantly inside floating glass cards."),
            ("Google Fonts", "Typography library.", "Integrates Google Sans and Google Sans Mono for crisp executive readability.")
        ]),
        ("2.7 Infrastructure & Deployment Module", [
            ("Docker & Docker Compose", "Container orchestration.", "Encapsulates all 6 microservices into isolated environments with unified networking (ecom_iq_network).")
        ])
    ]

    for mod_title, tech_list in modules_data:
        story.append(Paragraph(mod_title, h2_style))
        for tech_name, role, rationale in tech_list:
            story.append(Paragraph(f"• <b>{tech_name}:</b> {role} <i>Why: {rationale}</i>", bullet_style))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))

    # SECTION 3: COMPREHENSIVE TECHNOLOGY SUMMARY TABLE
    story.append(Paragraph("3. Complete Technology Stack Summary Table", h1_style))

    summary_table_data = [
        [Paragraph("Module", table_header), Paragraph("Technology", table_header), Paragraph("Category", table_header), Paragraph("Why Chosen Over Alternatives?", table_header)],
        [
            Paragraph("<b>Data Service</b>", table_cell_bold),
            Paragraph("Python + Stdlib (uuid, random)", table_cell),
            Paragraph("Generator", table_cell),
            Paragraph("Fastest developer velocity for generating 14 complex e-commerce JSON schemas using deterministic generators.", table_cell)
        ],
        [
            Paragraph("<b>Streaming</b>", table_cell_bold),
            Paragraph("Apache Kafka", table_cell),
            Paragraph("Message Broker", table_cell),
            Paragraph("Chosen over RabbitMQ for message replayability and multi-topic partition scaling.", table_cell)
        ],
        [
            Paragraph("<b>Processing</b>", table_cell_bold),
            Paragraph("PySpark", table_cell),
            Paragraph("Stream Engine", table_cell),
            Paragraph("Chosen over Pandas/Flink for native Spark SQL micro-batching and JDBC sink writers.", table_cell)
        ],
        [
            Paragraph("<b>Storage</b>", table_cell_bold),
            Paragraph("PostgreSQL", table_cell),
            Paragraph("RDBMS Database", table_cell),
            Paragraph("Chosen over MongoDB for ACID compliance and complex multi-table SQL JOIN analytics.", table_cell)
        ],
        [
            Paragraph("<b>API Layer</b>", table_cell_bold),
            Paragraph("FastAPI + Uvicorn", table_cell),
            Paragraph("Web Framework", table_cell),
            Paragraph("Chosen over Flask/Django for high-concurrency async performance and Swagger generation.", table_cell)
        ],
        [
            Paragraph("<b>AI Layer</b>", table_cell_bold),
            Paragraph("Google Gemini API", table_cell),
            Paragraph("LLM Engine", table_cell),
            Paragraph("Chosen for ultra-fast inference speed, large context windows, and low cost.", table_cell)
        ],
        [
            Paragraph("<b>MCP Server</b>", table_cell_bold),
            Paragraph("FastMCP", table_cell),
            Paragraph("Agent Protocol", table_cell),
            Paragraph("Standardized Anthropic Model Context Protocol allowing external agent connection.", table_cell)
        ],
        [
            Paragraph("<b>Frontend UI</b>", table_cell_bold),
            Paragraph("Vanilla HTML/CSS/JS", table_cell),
            Paragraph("Client UI", table_cell),
            Paragraph("Chosen over React/Next.js to avoid npm build step and enable instant browser execution.", table_cell)
        ],
    ]

    summary_table = Table(summary_table_data, colWidths=[75, 100, 85, 244])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF reference manual: {filename}")


if __name__ == "__main__":
    diag_file = r"C:\Users\Shubham\.gemini\antigravity-ide\brain\83e6dd3a-6318-459f-a614-a16eb376e044\ecomiq_technology_stack_diagram_updated_1785136945688.png"
    out_pdf = r"C:\Users\Shubham\Desktop\Ecom_iq\EcomIQ_Technology_Stack_Reference.pdf"
    create_tech_stack_pdf(out_pdf, diag_file)
