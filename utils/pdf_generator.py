from fpdf import FPDF
import os
from datetime import datetime

import re

def clean_text(text):
    """Strips characters not supported by standard PDF fonts (Latin-1)."""
    if not isinstance(text, str):
        return str(text)
    # Remove emojis and other non-standard symbols
    return re.sub(r'[^\x00-\xff]', '', text)

class ResumeReport(FPDF):
    def header(self):
        # Logo placeholder or Icon
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 212, 255) # primary blue
        self.cell(0, 10, 'RESUME INTELLIGENCE REPORT', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(result, filename):
    """
    Generates a professional PDF report from analysis results.
    """
    pdf = ResumeReport()
    pdf.add_page()
    
    # ── Summary Section ──
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, clean_text(f"Analysis for: {filename}"), 0, 1)
    
    score = result.get("match_score", 0)
    tier = result.get("tier", "N/A")
    
    pdf.set_font('Arial', 'B', 24)
    if score >= 80: pdf.set_text_color(76, 255, 145) # Success
    elif score >= 60: pdf.set_text_color(255, 165, 0) # Warn
    else: pdf.set_text_color(255, 107, 107) # Danger
    
    pdf.cell(0, 20, clean_text(f"OVERALL SCORE: {score}% ({tier})"), 0, 1, 'C')
    pdf.ln(5)
    
    # ── Breakdown ──
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "DIMENSIONAL BREAKDOWN", 0, 1)
    
    pdf.set_font('Arial', '', 11)
    breakdown = result.get("score_breakdown", {})
    for dim, val in breakdown.items():
        pdf.cell(60, 8, clean_text(f"{dim}:"), 0, 0)
        # Simple progress bar
        pdf.set_fill_color(230, 230, 230)
        pdf.rect(70, pdf.get_y() + 2, 100, 4, 'F')
        pdf.set_fill_color(0, 212, 255)
        pdf.rect(70, pdf.get_y() + 2, val, 4, 'F')
        pdf.cell(100, 8, f"  {val}%", 0, 1)
    
    pdf.ln(10)
    
    # ── Skills ──
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "SKILL ANALYSIS", 0, 1)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, "Matched Skills:", 0, 1)
    pdf.set_font('Arial', '', 10)
    matched = result.get("matched_skills", [])
    pdf.multi_cell(pdf.epw, 6, clean_text(", ".join(matched) if matched else "None detected"))
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, "Priority Skill Gaps:", 0, 1)
    pdf.set_font('Arial', '', 10)
    missing = result.get("missing_skills", [])
    pdf.multi_cell(pdf.epw, 6, clean_text(", ".join(missing) if missing else "No major gaps detected"))
    
    pdf.ln(10)
    
    # ── Suggestions ──
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "IMPROVEMENT ACTION ITEMS", 0, 1)
    pdf.set_font('Arial', '', 10)
    for sug in result.get("improvement_suggestions", []):
        pdf.multi_cell(pdf.epw, 7, f"- {clean_text(sug.replace('**', ''))}")
    
    pdf.ln(10)
    
    # ── AI Rewrite Sample ──
    if result.get("rewritten_bullets"):
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "AI RESUME REWRITE SAMPLES", 0, 1)
        for item in result.get("rewritten_bullets", []):
            pdf.set_font('Arial', 'I', 10)
            pdf.multi_cell(pdf.epw, 6, f"Original: {clean_text(item['original'])}")
            pdf.set_font('Arial', 'B', 10)
            pdf.set_text_color(0, 150, 0)
            pdf.multi_cell(pdf.epw, 6, f"Optimized: {clean_text(item['rewritten'])}")
            pdf.set_text_color(0, 0, 0)
            pdf.ln(5)

    # Output as absolute bytes for Streamlit compatibility
    return bytes(pdf.output())
