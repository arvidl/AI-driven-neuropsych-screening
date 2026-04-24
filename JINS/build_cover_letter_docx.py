"""
Build the JINS submission cover letter as a Microsoft Word .docx.

Output: JINS/submission/manuscript/cover_letter.docx
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm, Pt


JINS_DIR = Path(__file__).resolve().parent
OUTPUT = JINS_DIR / "submission" / "manuscript" / "cover_letter.docx"

FONT = "Times New Roman"
FONT_SIZE = Pt(12)
LINE_SPACING = 1.15  # single-spaced letter


def _apply_font(run, *, bold=False, italic=False, underline=False, size=None):
    run.font.name = FONT
    run.font.size = size if size is not None else FONT_SIZE
    run.font.bold = bold
    run.font.italic = italic
    run.font.underline = underline
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(attr), FONT)


def _format_para(p, *, alignment=None, space_after=Pt(6), space_before=Pt(0),
                 line_spacing=LINE_SPACING, left_indent=None,
                 first_line_indent=None):
    pf = p.paragraph_format
    if alignment is not None:
        p.alignment = alignment
    pf.line_spacing = line_spacing
    pf.space_before = space_before
    pf.space_after = space_after
    if left_indent is not None:
        pf.left_indent = left_indent
    if first_line_indent is not None:
        pf.first_line_indent = first_line_indent


def add_runs(doc, runs, *, alignment=None, space_after=Pt(6),
             space_before=Pt(0), line_spacing=LINE_SPACING,
             left_indent=None, first_line_indent=None):
    """runs = list of (text, fmt_dict)."""
    p = doc.add_paragraph()
    _format_para(p, alignment=alignment, space_after=space_after,
                 space_before=space_before, line_spacing=line_spacing,
                 left_indent=left_indent, first_line_indent=first_line_indent)
    for text, fmt in runs:
        run = p.add_run(text)
        _apply_font(
            run,
            bold=fmt.get("bold", False),
            italic=fmt.get("italic", False),
            underline=fmt.get("underline", False),
            size=fmt.get("size"),
        )
    return p


def add_text(doc, text="", **kwargs):
    return add_runs(doc, [(text, {})], **kwargs)


def add_section_heading(doc, text):
    add_runs(
        doc,
        [(text, {"bold": True})],
        space_before=Pt(12),
        space_after=Pt(4),
    )


def add_bullet(doc, runs):
    """Bulleted list item with manual leader for portability across Word versions."""
    leader = [("\u2022 ", {})]
    add_runs(doc, leader + runs, left_indent=Cm(0.6),
             first_line_indent=Cm(-0.4),
             space_after=Pt(4))


def add_horizontal_rule(doc):
    p = doc.add_paragraph()
    _format_para(p, space_before=Pt(6), space_after=Pt(6))
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "808080")
    pBdr.append(bottom)
    pPr.append(pBdr)


def build():
    doc = Document()

    # Document defaults
    style = doc.styles["Normal"]
    style.font.name = FONT
    style.font.size = FONT_SIZE
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rFonts.set(qn(attr), FONT)
    style.paragraph_format.line_spacing = LINE_SPACING
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.space_before = Pt(0)

    # Page setup
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    # ---- Title ----
    add_runs(
        doc,
        [("Cover Letter \u2014 Journal of the International "
          "Neuropsychological Society", {"bold": True})],
        alignment=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=Pt(18),
    )

    # ---- Date ----
    add_runs(
        doc,
        [("Date: ", {"bold": True}), ("2026-04-24", {})],
        space_after=Pt(6),
    )

    # ---- Recipient ----
    add_runs(
        doc,
        [("To: ", {"bold": True}),
         ("The Editor-in-Chief", {})],
        space_after=Pt(0),
    )
    add_text(doc, "Journal of the International Neuropsychological Society",
             space_after=Pt(0))
    add_text(doc, "Cambridge University Press", space_after=Pt(12))

    # ---- Re ----
    add_runs(
        doc,
        [("Re: ", {"bold": True}),
         ("Manuscript submission to the Special Issue on ", {}),
         ("Artificial Intelligence in Neuropsychology", {"bold": True}),
         (" \u2014 ", {}),
         ("\u201cAn AI-Initiated, Rule-Based Pipeline for Pre-Examination "
          "Screening in Clinical Neuropsychology\u201d", {"italic": True}),
         (".", {})],
        space_after=Pt(6),
    )

    add_horizontal_rule(doc)

    # ---- Salutation ----
    add_text(doc, "Dear Editor,", space_after=Pt(8))

    # ---- Lead paragraph ----
    add_runs(
        doc,
        [("We are pleased to submit the enclosed manuscript, ", {}),
         ("\u201cAn AI-Initiated, Rule-Based Pipeline for Pre-Examination "
          "Screening in Clinical Neuropsychology,\u201d", {"italic": True}),
         (" for consideration as a ", {}),
         ("Regular Research Article", {"bold": True}),
         (" in the ", {}),
         ("Journal of the International Neuropsychological Society",
          {"italic": True}),
         (". ", {}),
         ("This submission is in response to the call for papers for the "
          "Special Issue on \u201cArtificial Intelligence in "
          "Neuropsychology\u201d", {"bold": True}),
         (" (deadline 15 May 2026), and we have selected that special issue "
          "at the corresponding ScholarOne submission step. The paper falls "
          "squarely within JINS\u2019 interest in methodological innovation "
          "and clinical decision support that strengthens, rather than "
          "displaces, neuropsychological judgment.", {})],
        space_after=Pt(8),
    )

    # ---- Contribution ----
    add_section_heading(doc, "Contribution")
    add_text(
        doc,
        "The manuscript presents a fully deterministic, rule-based pipeline "
        "that automates the synthesis of multi-domain pre-examination "
        "screening data into a structured clinical formulation, "
        "audience-tailored reports, and visual summaries. We demonstrate the "
        "framework on N = 105 adults (65 patients with irritable bowel "
        "syndrome, 40 healthy controls) from the Bergen Brain\u2013Gut\u2013"
        "Microbiota study, using five established instruments (Bergen "
        "Insomnia Scale, Conners\u2019 CPT-3, Chalder Fatigue Scale, HADS, "
        "and RBANS). The pipeline applies published cutoffs together with "
        "cohort-relative interpretive rules, performs cross-domain reasoning "
        "(e.g., insomnia\u2013fatigue\u2013attention cascades), and emits "
        "PDF reports adapted to clinical peers, referring physicians, and "
        "patients.",
        space_after=Pt(8),
    )
    add_text(
        doc,
        "Two contrasting case illustrations show how the pipeline "
        "differentiates a circumscribed sleep-centered profile from a "
        "broader multi-domain involvement, while explicitly highlighting "
        "where clinician interpretation must extend the rule-based output. "
        "Because every classification, flag, reasoning step, and "
        "recommendation traces back to an explicit rule, the framework "
        "offers transparency, reproducibility, and traceability \u2014 "
        "properties we consider essential for clinical neuropsychology.",
        space_after=Pt(8),
    )

    # ---- Use of AI ----
    add_section_heading(doc, "Use of AI")
    add_text(
        doc,
        "In line with Cambridge University Press\u2019s policy on the "
        "declaration of AI tools, we note explicitly:",
        space_after=Pt(4),
    )
    add_bullet(
        doc,
        [("The pipeline source code and parts of the manuscript text were ", {}),
         ("co-developed with AI coding assistants", {"bold": True}),
         (" (Anthropic Claude Opus 4.7 and OpenAI GPT-5.4, accessed via the "
          "Cursor IDE between February and April 2026).", {})],
    )
    add_bullet(
        doc,
        [("All AI-generated content was reviewed, verified, and edited by "
          "the authors.", {})],
    )
    add_bullet(
        doc,
        [("No AI is used at runtime.", {"bold": True}),
         (" The deployed pipeline contains no LLM API calls, no AI client "
          "libraries, and no network dependencies. All clinical "
          "classifications and recommendations are produced by "
          "deterministic, rule-based logic operating on published cutoffs "
          "and pre-authored text templates.", {})],
    )
    add_bullet(
        doc,
        [("A full account of AI\u2019s role (development time vs. runtime), "
          "together with the complete prompt and rule specifications, is "
          "provided in Supplementary Material S1.", {})],
    )

    # ---- Standard declarations ----
    add_section_heading(doc, "Standard declarations")
    add_bullet(
        doc,
        [("The manuscript is original, has not been published previously, "
          "and is not under consideration elsewhere.", {})],
    )
    add_bullet(
        doc,
        [("All listed authors approved the submitted version and meet the "
          "authorship criteria of Cambridge University Press.", {})],
    )
    add_bullet(
        doc,
        [("The original Bergen Brain\u2013Gut\u2013Microbiota study was "
          "approved by the Regional Committee for Medical and Health "
          "Research Ethics, South East Norway (REK2015-01621); all "
          "participants provided written informed consent.", {})],
    )
    add_bullet(
        doc,
        [("Competing interests:", {"bold": True}),
         (" The authors declare none.", {})],
    )
    add_bullet(
        doc,
        [("Funding:", {"bold": True}),
         (" University of Bergen; Research Council of Norway "
          "(FRIMED-BIO276010, project 294594); Helse Vest\u2019s Research "
          "Funding (HV912243); Trond Mohn Research Foundation "
          "(BFS2018TMT0).", {})],
    )
    add_bullet(
        doc,
        [("Data availability:", {"bold": True}),
         (" The cohort dataset is restricted by ethics approval and is not "
          "publicly available; the pipeline source code, an analysis-ready "
          "blinded subset, the two anonymised example reports, and "
          "notebooks reproducing the public subset of Table 1 are openly "
          "available at https://github.com/arvidl/"
          "AI-driven-neuropsych-screening.", {})],
    )

    # ---- Files included ----
    add_section_heading(doc, "Files included")
    add_bullet(
        doc,
        [("Main manuscript (", {}),
         ("AI_driven_neuropsych_screening_20260424.docx", {"italic": True}),
         (") \u2014 Microsoft Word format, JINS-compliant (Times New Roman "
          "12 pt, double-spaced, continuous line numbering, structured "
          "Abstract, Statement of Research Significance, ethics statement, "
          "[INSERT TABLE/FIGURE x HERE] callouts, all tables and figures "
          "placed after the references).", {})],
    )
    add_bullet(
        doc,
        [("Five figure files (Figure 1\u20135) as separate high-resolution "
          "PDFs (vector; \u2265 300 dpi equivalent).", {})],
    )
    add_bullet(
        doc,
        [("Supplementary Material S1 \u2014 ", {}),
         ("S1_supplementary_methods.pdf", {"italic": True}),
         (" (prompt and rule specifications, complete deterministic rule "
          "set).", {})],
    )
    add_bullet(
        doc,
        [("Supplementary Material S2 \u2014 ", {}),
         ("S2_case_1_report.pdf", {"italic": True}),
         (" (full audience-tailored pipeline report, Case 1).", {})],
    )
    add_bullet(
        doc,
        [("Supplementary Material S3 \u2014 ", {}),
         ("S3_case_2_report.pdf", {"italic": True}),
         (" (full audience-tailored pipeline report, Case 2).", {})],
    )

    # ---- Suggested reviewers ----
    add_section_heading(doc, "Suggested reviewers")
    add_text(
        doc,
        "We respectfully suggest the following experts as potential "
        "reviewers, with no recent collaboration or conflict of interest "
        "with the authors:",
        space_after=Pt(4),
    )
    reviewer_topics = [
        "AI in neuropsychological practice",
        "clinical decision support / report writing",
        "IBS and cognition / gut\u2013brain axis",
        "computerised cognitive assessment",
    ]
    for i, topic in enumerate(reviewer_topics, start=1):
        add_runs(
            doc,
            [(f"{i}. ", {}),
             ("(reviewer name, affiliation, email)", {"italic": True}),
             (f" \u2014 {topic}", {})],
            left_indent=Cm(0.6),
            first_line_indent=Cm(-0.4),
            space_after=Pt(4),
        )
    add_text(doc, "We have no non-preferred reviewers to declare.",
             space_before=Pt(4), space_after=Pt(8))

    add_horizontal_rule(doc)

    # ---- Closing ----
    add_text(
        doc,
        "We thank you and the editorial team in advance for considering our "
        "work and look forward to the review process.",
        space_after=Pt(12),
    )
    add_text(doc, "Sincerely,", space_after=Pt(24))

    # ---- Signature block ----
    add_runs(
        doc,
        [("Astri J. Lundervold, PhD", {"bold": True}),
         (" (corresponding author)", {"italic": True})],
        space_after=Pt(0),
    )
    add_text(
        doc,
        "Department of Clinical and Biological Psychology, "
        "University of Bergen",
        space_after=Pt(0),
    )
    add_text(doc, "Christiesgate 12, 5015 Bergen, Norway", space_after=Pt(0))
    add_text(doc, "Email: Astri.Lundervold@uib.no", space_after=Pt(0))
    add_text(doc, "ORCID: https://orcid.org/0000-0002-6819-6164",
             space_after=Pt(8))
    add_text(
        doc,
        "on behalf of co-authors Birgitte Berentsen and Arvid Lundervold",
        space_after=Pt(0),
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    build()
