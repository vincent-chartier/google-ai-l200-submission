"""Generate publication-quality 4-page PDF architecture blueprint with visual diagram."""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas calculating total page count for running headers & footers."""
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
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Running header on page 2 and later
        if self._pageNumber > 1:
            self.drawString(40, 755, "CINEMA OUTINGS AI  |  SYSTEM ARCHITECTURE & TECHNICAL BLUEPRINT")
            self.setFont("Helvetica", 7.5)
            self.drawRightString(572, 755, "GOOGLE AI L200 SUBMISSION")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(40, 747, 572, 747)

        # Running footer on all pages
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        footer_left = "Architecture Specification — Google Cloud & Agent Development Kit"
        footer_right = f"Page {self._pageNumber} of {page_count}"
        self.drawString(40, 25, footer_left)
        self.drawRightString(572, 25, footer_right)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(40, 35, 572, 35)
        self.restoreState()


def build_pdf(filename: str, diagram_image_path: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    PRIMARY = colors.HexColor("#0F172A")     # Slate 900
    ACCENT = colors.HexColor("#2563EB")      # Electric Blue 600
    ACCENT_LIGHT = colors.HexColor("#F0F7FF")# Soft Blue Tint
    SECONDARY = colors.HexColor("#334155")   # Slate 700
    TEXT_MUTED = colors.HexColor("#64748B")  # Slate 500
    BORDER_COLOR = colors.HexColor("#CBD5E1")# Slate 300
    CARD_BG = colors.HexColor("#F8FAFC")     # Slate 50

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=21,
        leading=25,
        textColor=PRIMARY,
        spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=ACCENT,
        spaceAfter=8,
    )
    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=15.5,
        textColor=PRIMARY,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=SECONDARY,
        spaceAfter=5,
    )
    caption_style = ParagraphStyle(
        "CaptionStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=TEXT_MUTED,
        alignment=TA_CENTER,
        spaceBefore=3,
        spaceAfter=4,
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.8,
        leading=10.5,
        textColor=SECONDARY,
    )
    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10.5,
        textColor=colors.white,
    )

    story = []

    # =========================================================================
    # PAGE 1: TITLE, EXECUTIVE SUMMARY & ARCHITECTURAL FOUNDATIONS
    # =========================================================================
    top_bar = [
        [
            Paragraph("<b>PROJECT SPECIFICATION & TECHNICAL BLUEPRINT</b>", ParagraphStyle("Badge", fontName="Helvetica-Bold", fontSize=7.5, textColor=ACCENT)),
            Paragraph("<b>VERSION 1.0  |  SEPTEMBER 2026</b>", ParagraphStyle("BadgeR", fontName="Helvetica-Bold", fontSize=7.5, textColor=TEXT_MUTED, alignment=TA_RIGHT))
        ]
    ]
    t_top = Table(top_bar, colWidths=[280, 252])
    t_top.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BOTTOMPADDING', (0,0), (-1,-1), 0), ('TOPPADDING', (0,0), (-1,-1), 0)]))
    story.append(t_top)
    story.append(Spacer(1, 4))

    story.append(Paragraph("Cinema Outings AI", title_style))
    story.append(Paragraph("Multi-Agent Autonomous Architecture, A2UI Protocol & Cloud Infrastructure", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceBefore=0, spaceAfter=8))

    meta_data = [
        [
            Paragraph("<b>Candidate / Author:</b> Vincent Chartier", table_cell),
            Paragraph("<b>Cloud Provider:</b> Google Cloud Platform (GCP)", table_cell),
            Paragraph("<b>Primary Stack:</b> Flutter + Google ADK + Gemini", table_cell),
        ],
        [
            Paragraph("<b>Submission Track:</b> Google AI L200", table_cell),
            Paragraph("<b>Region:</b> us-central1 (Council Bluffs)", table_cell),
            Paragraph("<b>Infrastructure as Code:</b> Terraform >= 1.5.0", table_cell),
        ]
    ]
    t_meta = Table(meta_data, colWidths=[177, 177, 178])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), CARD_BG),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    abstract_text = (
        "<b>Executive Summary:</b> Cinema Outings AI is a production-grade, full-stack multi-agent mobile and cloud "
        "platform designed to discover cinema screenings, personalize recommendations using taste memory, guarantee "
        "transaction safety, book tickets, and synchronize calendar invites. Built using the <b>Google Agent Development "
        "Kit (ADK)</b>, <b>Gemini 2.5</b> strategic tiered model routing, <b>FastMCP</b> (Model Context Protocol), and "
        "Flutter's dynamic <b>A2UI (Agent-to-UI)</b> declarative protocol, the architecture is provisioned with enterprise-grade "
        "<b>Terraform</b> Infrastructure as Code (IaC) on Google Cloud Platform."
    )
    story.append(Paragraph(abstract_text, body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Architectural Foundations & Design Principles", h1_style))
    story.append(Paragraph(
        "The architecture is engineered around five fundamental enterprise principles:", body_style
    ))

    principles = [
        "<b>1. Supervisor-Host Orchestration:</b> Built upon Google ADK's <code>LlmAgent</code> pattern. The Outing Coordinator Agent acts as the central host, delegating sub-tasks to specialized sub-agents while maintaining unified conversational state and session memory passing.",
        "<b>2. Declarative Agent-to-UI (A2UI) Protocol:</b> Rather than returning raw markdown or brittle plain text, agents output typed A2UI JSON components. The Flutter client dynamically parses and renders rich interactive widgets (movie discovery carousels, 2D seat selectors, boarding pass ticket passes, and calendar invitations).",
        "<b>3. Defense-in-Depth & Sensitive Data Protection:</b> Strict Google ADK lifecycle plugins inspect user input before agent execution. Google Cloud Sensitive Data Protection (DLP) automatically redacts payment cards, phone numbers, emails, and SSNs. Reservation safety plugins ensure zero unheld ticket charges.",
        "<b>4. Strategic Tiered Model Routing:</b> Semantic intent classification routes each request to its cost-optimal Gemini model tier—reserving <code>gemini-2.5-pro</code> for nuanced taste reasoning, <code>gemini-2.5-flash</code> for conversational agility and deterministic booking transactions, and <code>gemini-2.0-flash-lite</code> for profile maintenance and calendar formatting.",
        "<b>5. Fully Codified Infrastructure as Code (IaC):</b> All Google Cloud resources—including Cloud Run v2, Secret Manager, Artifact Registry, Cloud Storage FUSE volumes, Cloud Monitoring, and least-privilege IAM service accounts—are provisioned automatically via modular Terraform configurations."
    ]
    for p in principles:
        story.append(Paragraph(p, body_style))

    story.append(Spacer(1, 8))
    overview_box = [
        [
            Paragraph("<b>Architecture Blueprint Navigation:</b> Overleaf (Page 2) features the complete graphical system "
                      "architecture diagram depicting the six synchronized layers down to agent, tool, protocol, and cloud service "
                      "components. Pages 3 and 4 detail agent specifications, tool signatures, security guardrails, model tiers, and Terraform IaC.", table_cell)
        ]
    ]
    t_box = Table(overview_box, colWidths=[532])
    t_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), ACCENT_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.75, ACCENT),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_box)

    # =========================================================================
    # PAGE 2: FULL-PAGE VISUAL SYSTEM ARCHITECTURE DIAGRAM
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("Figure 1: Full-System Architecture & Component Interaction Blueprint", h1_style))
    story.append(Paragraph(
        "High-resolution component diagram detailing the interaction flow across Client, Gateway, Security, Multi-Agent Core, Tools & Cloud Persistence:", body_style
    ))
    story.append(Spacer(1, 4))

    # Embed High-Resolution Diagram Image
    # Image aspect ratio is ~1.09 (width=490, height=534)
    story.append(Image(diagram_image_path, width=490, height=534))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>Figure 1 Legend:</b> Blue: Client & ADK Agent Core  |  Purple: FastAPI Gateway & Telemetry  |  "
        "Red: Security Guardrails & Cloud DLP  |  Green: FastMCP & Transaction Tools  |  Amber: Session State, SQLite & GCP Cloud Run v2 (Terraform).",
        caption_style
    ))

    # =========================================================================
    # PAGE 3: SPECIALIZED AGENTS & TOOLS / PROTOCOLS
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("2. Specialized Multi-Agent System Breakdown", h1_style))
    story.append(Paragraph(
        "Each agent executes a specialized role within clear isolation boundaries, coordinated via shared Google ADK session memory:", body_style
    ))

    agent_table_data = [
        [
            Paragraph("Agent Role", table_header),
            Paragraph("Technology & Model", table_header),
            Paragraph("Core Architectural Responsibilities", table_header),
            Paragraph("Session Memory Keys", table_header),
        ],
        [
            Paragraph("<b>1. Outing Coordinator</b><br/>(Supervisor/Host)", table_cell),
            Paragraph("Google ADK<br/><code>gemini-2.5-flash</code>", table_cell),
            Paragraph("• Conversational intent classification<br/>• Sub-agent routing & delegation<br/>• A2UI declarative widget packaging<br/>• Dialog lifecycle & turn history", table_cell),
            Paragraph("<code>conversation_history</code><br/><code>active_intent</code><br/><code>session_id</code>", table_cell),
        ],
        [
            Paragraph("<b>2. Search & Reco</b>", table_cell),
            Paragraph("Google ADK + FastMCP<br/><code>gemini-2.5-pro</code> (Deep)<br/><code>gemini-2.5-flash</code> (Fast)", table_cell),
            Paragraph("• Live screenings lookup via FastMCP<br/>• Director & genre taste-matching<br/>• 0% duplicate seen movie filtering<br/>• Venue, hall & showtime discovery", table_cell),
            Paragraph("Reads:<br/><code>favorite_movies</code><br/><code>seen_movies</code>", table_cell),
        ],
        [
            Paragraph("<b>3. Booking Agent</b>", table_cell),
            Paragraph("Google ADK + Custom Tx<br/><code>gemini-2.5-flash</code><br/>(T=0, Deterministic)", table_cell),
            Paragraph("• Real-time seating grid inspection<br/>• 10-minute temporary seat reservation<br/>• Payment settlement & idempotency<br/>• Digital QR token boarding pass", table_cell),
            Paragraph("Mutates:<br/><code>active_reservation</code><br/><code>active_booking</code>", table_cell),
        ],
        [
            Paragraph("<b>4. Housekeeping</b>", table_cell),
            Paragraph("Google ADK + Summarizer<br/><code>gemini-2.0-flash-lite</code><br/><code>gemini-2.5-flash</code>", table_cell),
            Paragraph("• Watched archive ledger maintenance<br/>• User favorites list curation<br/>• RFC-5545 .ics & Google Calendar export<br/>• Automatic conversation compaction", table_cell),
            Paragraph("Mutates:<br/><code>seen_movies</code><br/><code>favorite_movies</code><br/><code>summary</code>", table_cell),
        ]
    ]
    t_agents = Table(agent_table_data, colWidths=[110, 115, 177, 130])
    t_agents.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_agents)
    story.append(Spacer(1, 8))

    story.append(Paragraph("3. Tools, Protocols & Integration Specifications", h1_style))
    story.append(Paragraph(
        "Standardized tool contracts connect the multi-agent core with cinema catalogs, transactional APIs, and client widgets:", body_style
    ))

    tools_data = [
        [
            Paragraph("Protocol / Subsystem", table_header),
            Paragraph("Implementation File", table_header),
            Paragraph("Methods & Interface Signatures", table_header),
            Paragraph("Operational Guarantees", table_header),
        ],
        [
            Paragraph("<b>FastMCP Server</b><br/>(Model Context Protocol)", table_cell),
            Paragraph("<code>backend/mcp_servers/<br/>movie_search_server.py</code>", table_cell),
            Paragraph("• <code>search_cinemas(location, query)</code><br/>• <code>get_showtimes(movie_title, date)</code><br/>• <code>get_movie_details(movie_title)</code><br/>• <code>list_now_showing(genre)</code>", table_cell),
            Paragraph("FastMCP stdio server providing screening catalogs, showtimes, auditorium formats (IMAX, standard), and capacity limits.", table_cell),
        ],
        [
            Paragraph("<b>Ticketing Engine</b><br/>(Custom Transactions)", table_cell),
            Paragraph("<code>backend/tools/<br/>booking_transactions.py</code>", table_cell),
            Paragraph("• <code>get_seat_availability(c, h, t)</code><br/>• <code>hold_seats_reservation(...)</code><br/>• <code>process_ticket_payment(...)</code><br/>• <code>cancel_booking(booking_id)</code>", table_cell),
            Paragraph("Atomic reservation management. Implements lock-lease timeouts (600s), idempotency keys, subtotal calculations, and digital QR boarding passes.", table_cell),
        ],
        [
            Paragraph("<b>Calendar Engine</b>", table_cell),
            Paragraph("<code>backend/tools/<br/>calendar_tools.py</code>", table_cell),
            Paragraph("• <code>generate_ics_calendar(...)</code><br/>• <code>create_google_calendar_link(...)</code>", table_cell),
            Paragraph("RFC-5545 iCalendar specification generator (`.ics`) and browser-compatible Google Calendar deep links with cinema venue and seat data.", table_cell),
        ],
        [
            Paragraph("<b>A2UI Protocol</b><br/>(Agent-to-UI)", table_cell),
            Paragraph("<code>backend/protocols/<br/>a2ui.py</code>", table_cell),
            Paragraph("• <code>A2UIMessage</code><br/>• <code>movie_card</code>, <code>seat_map_selector</code><br/>• <code>ticket_pass</code>, <code>calendar_invite_card</code><br/>• <code>seen_history_list</code>", table_cell),
            Paragraph("Declarative JSON protocol enabling autonomous backend agents to construct native Flutter widgets dynamically without app recompilation.", table_cell),
        ],
        [
            Paragraph("<b>Compaction Engine</b>", table_cell),
            Paragraph("<code>backend/state/<br/>history_summarizer.py</code>", table_cell),
            Paragraph("• <code>compact_conversation_history(...)</code><br/>• <code>extract_key_entities(...)</code>", table_cell),
            Paragraph("Autonomous conversation compaction. Compresses aged dialogue turns into running entity summaries while keeping recent turns intact.", table_cell),
        ]
    ]
    t_tools = Table(tools_data, colWidths=[110, 115, 160, 147])
    t_tools.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 3.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_tools)

    # =========================================================================
    # PAGE 4: SECURITY, MODEL ROUTING, TERRAFORM & TEST VERIFICATION
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("4. Security Guardrails, Cloud DLP & Observability", h1_style))
    story.append(Paragraph(
        "The system enforces defense-in-depth across the agent execution lifecycle using Google ADK BasePlugin hooks, "
        "OpenTelemetry distributed tracing, and Google Cloud Sensitive Data Protection (DLP):", body_style
    ))

    sec_data = [
        [
            Paragraph("Subsystem", table_header),
            Paragraph("Implementation File", table_header),
            Paragraph("Security & Operational Guarantees", table_header),
        ],
        [
            Paragraph("<b>Cloud DLP (Sensitive Data)</b>", table_cell),
            Paragraph("<code>backend/security/<br/>dlp_service.py</code>", table_cell),
            Paragraph("Inspects & redacts sensitive PII before agent processing: Credit Cards (<code>[REDACTED_PAYMENT_CARD]</code>), Emails, Phone Numbers, Social Security Numbers, Bearer/API Tokens.", table_cell),
        ],
        [
            Paragraph("<b>Input Security Guardrail</b>", table_cell),
            Paragraph("<code>backend/plugins/<br/>security_guardrails.py</code>", table_cell),
            Paragraph("Intercepts prompt injection attempts ('Ignore previous instructions', role hijacking), jailbreak sequences, and malicious formatting attacks before model execution.", table_cell),
        ],
        [
            Paragraph("<b>Booking Safety Guardrail</b>", table_cell),
            Paragraph("<code>backend/plugins/<br/>security_guardrails.py</code>", table_cell),
            Paragraph("Enforces that payments cannot execute without an active, unexpired seat hold token. Blocks replay attacks, double-charges, and seat reservation concurrency collisions.", table_cell),
        ],
        [
            Paragraph("<b>OpenTelemetry Tracing</b>", table_cell),
            Paragraph("<code>backend/telemetry/<br/>tracing.py</code>", table_cell),
            Paragraph("W3C <code>traceparent</code> HTTP header propagation across Flutter client, FastAPI gateway, LLM inference, MCP tool calls, and SQLite persistence.", table_cell),
        ],
        [
            Paragraph("<b>Structured JSON Logging</b>", table_cell),
            Paragraph("<code>backend/telemetry/<br/>logging.py</code>", table_cell),
            Paragraph("GCP Cloud Logging semantic format with severity levels, trace correlation (<code>logging.googleapis.com/trace</code>), span IDs, and session context metadata.", table_cell),
        ],
    ]
    t_sec = Table(sec_data, colWidths=[125, 120, 287])
    t_sec.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_sec)
    story.append(Spacer(1, 6))

    story.append(Paragraph("5. Strategic Model Routing & Terraform Infrastructure (IaC)", h1_style))
    story.append(Paragraph(
        "Semantic intent classification routes queries to optimal Gemini model tiers, all provisioned via modular Terraform:", body_style
    ))

    tier_data = [
        [
            Paragraph("Model Tier", table_header),
            Paragraph("Model Identifier", table_header),
            Paragraph("Assigned Agents & Roles", table_header),
            Paragraph("Architectural & Cost Rationale", table_header),
        ],
        [
            Paragraph("<b>Deep Reasoning</b>", table_cell),
            Paragraph("<code>gemini-2.5-pro</code>", table_cell),
            Paragraph("Search & Reco (Taste Analysis)", table_cell),
            Paragraph("Nuanced stylistic comparisons, director filmography synthesis, and complex multi-criteria recommendation grounding.", table_cell),
        ],
        [
            Paragraph("<b>Fast Conversational</b>", table_cell),
            Paragraph("<code>gemini-2.5-flash</code>", table_cell),
            Paragraph("Coordinator, Search (Catalog)", table_cell),
            Paragraph("Sub-second intent classification, conversational turn handling, and high-throughput screening discovery.", table_cell),
        ],
        [
            Paragraph("<b>Deterministic Tx</b>", table_cell),
            Paragraph("<code>gemini-2.5-flash</code> (T=0)", table_cell),
            Paragraph("Booking Agent", table_cell),
            Paragraph("Strict schema compliance, zero-temperature execution for reservation holding and financial transaction calls.", table_cell),
        ],
        [
            Paragraph("<b>Ultra-Lite</b>", table_cell),
            Paragraph("<code>gemini-2.0-flash-lite</code>", table_cell),
            Paragraph("Housekeeping & Calendar", table_cell),
            Paragraph("Lowest cost tier for conversation compaction, profile memory updates, and simple RFC-5545 `.ics` formatting.", table_cell),
        ]
    ]
    t_tier = Table(tier_data, colWidths=[95, 110, 145, 182])
    t_tier.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_tier)
    story.append(Spacer(1, 5))

    iac_summary = (
        "<b>Modular Terraform Infrastructure as Code (GCP):</b><br/>"
        "• <b><code>modules/apis</code>:</b> Enables 14 GCP APIs (Cloud Run, Cloud DLP, Vertex AI, Secret Manager, Cloud Trace, Logging, Monitoring).<br/>"
        "• <b><code>modules/iam</code>:</b> Creates dedicated least-privilege service account (<code>cinema-outings-sa</code>) with strict role bindings.<br/>"
        "• <b><code>modules/secrets</code>:</b> Manages <code>GEMINI_API_KEY</code> in Google Secret Manager with automated accessor policies.<br/>"
        "• <b><code>modules/storage</code>:</b> Provisions encrypted GCS bucket with versioning & lifecycle rules, mounted to Cloud Run via FUSE.<br/>"
        "• <b><code>modules/registry</code>:</b> Private Artifact Registry Docker repository for container images.<br/>"
        "• <b><code>modules/cloud_run</code>:</b> Cloud Run v2 service deploying the FastAPI multi-agent backend with startup/liveness health probes.<br/>"
        "• <b><code>modules/monitoring</code>:</b> Cloud Monitoring dashboard (latencies, CPU/RAM, requests, Cloud DLP PII log metrics) and 5xx alerts.<br/>"
        "• <b>Environments:</b> Pre-configured <code>environments/dev</code> (cost-optimized) and <code>environments/prod</code> (high-availability warm instances)."
    )
    story.append(Paragraph(iac_summary, body_style))
    story.append(Spacer(1, 4))

    verif_data = [
        [
            Paragraph("<b>Automated Verification & Test Results:</b> All <b>63 pytest test cases pass cleanly</b> across agent delegation, "
                      "memory passing, A2UI protocol serialization, MCP tool execution, security guardrails, Cloud DLP sanitization, "
                      "OpenTelemetry tracing, conversation compaction, and Terraform syntax/module validation.", table_cell)
        ]
    ]
    t_verif = Table(verif_data, colWidths=[532])
    t_verif.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), ACCENT_LIGHT),
        ('BOX', (0,0), (-1,-1), 0.75, ACCENT),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_verif)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated 4-page PDF with architecture diagram at: {filename}")


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    out_pdf = repo_root / "Cinema_Outings_AI_Architecture.pdf"
    diagram_img = repo_root / "docs" / "architecture_diagram.png"
    build_pdf(str(out_pdf), str(diagram_img))
