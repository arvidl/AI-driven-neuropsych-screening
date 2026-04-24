"""
Build a JINS-compliant Microsoft Word manuscript from the aligned LaTeX source.

Output: AI_driven_neuropsych_screening_20260424.docx

JINS submission requirements applied (from Preparing_your_materials_JINS.pdf):
- Times New Roman 12 pt, double-spaced throughout
- Continuous line numbering on the manuscript section
- Title page (running head, title, authors, affiliations, corresponding author,
  ORCID, word counts) -> page 1
- Structured Abstract (Objective / Method / Results / Conclusions) + 6 keywords -> page 2
- Statement of Research Significance with three underlined headings -> page 3
- Manuscript body (Introduction, Method, Results, Discussion, Conclusions) -> page 4+
- Ethics statement in Methods explicitly references the Helsinki Declaration
- [INSERT TABLE/FIGURE n HERE] callouts in body text
- Acknowledgements with "Competing Interests" and "Sources of Support" subheadings
- References (APA 7, all authors listed for 3-20 author works)
- Tables (each on its own page) after References
- Figure Legends on a separate page
- Figures (each on its own page) after the figure legends
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm, Pt, RGBColor


JINS_DIR = Path(__file__).resolve().parent
OUTPUT = JINS_DIR / "AI_driven_neuropsych_screening_20260424.docx"
FIGURES_DIR = JINS_DIR / "submission" / "figures"

FONT = "Times New Roman"
FONT_SIZE = Pt(12)
LINE_SPACING = 2.0  # double-spaced


# ---------------------------------------------------------------------------
# Low-level docx helpers
# ---------------------------------------------------------------------------

def _apply_default_font(run, *, bold=False, italic=False, underline=False, size=None):
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


def _format_paragraph(p, *, alignment=None, space_after=None, space_before=None,
                      line_spacing=LINE_SPACING, first_line_indent=None,
                      keep_with_next=False):
    pf = p.paragraph_format
    if alignment is not None:
        p.alignment = alignment
    pf.line_spacing = line_spacing
    pf.space_after = space_after if space_after is not None else Pt(0)
    pf.space_before = space_before if space_before is not None else Pt(0)
    if first_line_indent is not None:
        pf.first_line_indent = first_line_indent
    pf.keep_with_next = keep_with_next


def add_para(doc, text="", *, bold=False, italic=False, underline=False,
             alignment=None, space_after=None, space_before=None,
             line_spacing=LINE_SPACING, first_line_indent=None,
             size=None, keep_with_next=False):
    p = doc.add_paragraph()
    _format_paragraph(
        p,
        alignment=alignment,
        space_after=space_after,
        space_before=space_before,
        line_spacing=line_spacing,
        first_line_indent=first_line_indent,
        keep_with_next=keep_with_next,
    )
    if text:
        run = p.add_run(text)
        _apply_default_font(run, bold=bold, italic=italic, underline=underline, size=size)
    return p


def add_runs_para(doc, runs, *, alignment=None, space_after=None,
                  space_before=None, line_spacing=LINE_SPACING,
                  first_line_indent=None, keep_with_next=False):
    """runs = list of (text, dict-of-formatting). Empty text creates blank run."""
    p = doc.add_paragraph()
    _format_paragraph(
        p,
        alignment=alignment,
        space_after=space_after,
        space_before=space_before,
        line_spacing=line_spacing,
        first_line_indent=first_line_indent,
        keep_with_next=keep_with_next,
    )
    for text, fmt in runs:
        run = p.add_run(text)
        _apply_default_font(
            run,
            bold=fmt.get("bold", False),
            italic=fmt.get("italic", False),
            underline=fmt.get("underline", False),
            size=fmt.get("size"),
        )
    return p


def add_heading_apa(doc, text, *, level=1):
    """APA-style heading without numbering. level 1 -> Centered Bold; level 2 -> Left Bold."""
    if level == 1:
        p = add_para(doc, text, bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                     space_before=Pt(12), space_after=Pt(6), keep_with_next=True)
    elif level == 2:
        p = add_para(doc, text, bold=True, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                     space_before=Pt(12), space_after=Pt(6), keep_with_next=True)
    else:
        p = add_para(doc, text, bold=True, italic=True, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                     space_before=Pt(6), space_after=Pt(3), keep_with_next=True)
    return p


def add_page_break(doc):
    p = doc.add_paragraph()
    _format_paragraph(p, line_spacing=LINE_SPACING)
    p.add_run().add_break(WD_BREAK.PAGE)


def enable_line_numbering(section, *, start=1, distance=Cm(0.4)):
    """Enable continuous line numbering on the given section."""
    sectPr = section._sectPr
    existing = sectPr.find(qn("w:lnNumType"))
    if existing is not None:
        sectPr.remove(existing)
    ln = OxmlElement("w:lnNumType")
    ln.set(qn("w:countBy"), "1")
    ln.set(qn("w:start"), str(start))
    ln.set(qn("w:distance"), str(distance))
    ln.set(qn("w:restart"), "continuous")
    sectPr.append(ln)


def restart_line_numbering_for_section(section, *, restart="newSection"):
    sectPr = section._sectPr
    existing = sectPr.find(qn("w:lnNumType"))
    if existing is not None:
        sectPr.remove(existing)


def disable_line_numbering(section):
    sectPr = section._sectPr
    existing = sectPr.find(qn("w:lnNumType"))
    if existing is not None:
        sectPr.remove(existing)


def set_running_head(section, *, header_text, page_x_of_y=False):
    header = section.header
    header.is_linked_to_previous = False
    p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    p.text = ""
    _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.RIGHT, line_spacing=1.0)
    run = p.add_run(header_text)
    _apply_default_font(run, size=Pt(12))


def set_page_number_footer(section):
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.text = ""
    _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.RIGHT, line_spacing=1.0)
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run = p.add_run()
    _apply_default_font(run, size=Pt(12))
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

TITLE = ("An AI-Initiated, Rule-Based Pipeline for Pre-Examination Screening "
         "in Clinical Neuropsychology")

RUNNING_HEAD = "Lundervold-AI Pre-Examination Screening"  # 39 chars

# (text, superscripts) pairs for authors
AUTHORS = [
    ("Astri J. Lundervold", "a,b"),
    ("Birgitte Berentsen", "c"),
    ("Arvid Lundervold", "d,e"),
]

AFFILIATIONS = [
    ("a", "Department of Clinical and Biological Psychology, University of Bergen, "
          "Bergen, Norway"),
    ("b", "Department of Geriatric Medicine, Haraldsplass Deaconess Hospital AS "
          "Surgical Clinic, Bergen, Norway"),
    ("c", "National Centre for Functional Gastrointestinal Disorders, Department of "
          "Medicine, Haukeland University Hospital, Bergen, Norway"),
    ("d", "Department of Biomedicine, University of Bergen, Bergen, Norway"),
    ("e", "Mohn Medical Imaging and Visualization Centre (MMIV), Department of "
          "Radiology, Haukeland University Hospital, Bergen, Norway"),
]

CORRESPONDING_AUTHOR = {
    "name": "Astri J. Lundervold",
    "address": ("Department of Clinical and Biological Psychology, "
                "University of Bergen, Christiesgate 12, 5015 Bergen, Norway"),
    "email": "Astri.Lundervold@uib.no",
}

ORCIDS = [
    ("Astri J. Lundervold", "0000-0002-6819-6164"),
    ("Birgitte Berentsen", "0000-0003-3574-7078"),
    ("Arvid Lundervold", "0000-0002-0032-4182"),
]

KEYWORDS = [
    "Decision Support Systems, Clinical",
    "Neuropsychological Tests",
    "Artificial Intelligence",
    "Irritable Bowel Syndrome",
    "Cognitive Dysfunction",
    "Electronic Health Records",
]

# ---------------------------------------------------------------------------
# Body text — sourced from jins_main.tex (already aligned with .docx 20260423).
# ---------------------------------------------------------------------------

ABSTRACT_OBJECTIVE = (
    "We present a proof-of-concept framework for automated pre-examination "
    "screening in clinical neuropsychology. Because fully digital cognitive "
    "instruments are not yet universally available, the framework is "
    "demonstrated on existing data from a study of irritable bowel syndrome "
    "(IBS). A deterministic pipeline transforms multi-domain scores into a "
    "structured clinical analysis with cross-domain reasoning and "
    "audience-tailored reports."
)

ABSTRACT_METHOD = (
    "The pipeline processes five instruments (Bergen Insomnia Scale [BIS], "
    "Conners' CPT-3, Chalder Fatigue Scale, Hospital Anxiety and Depression "
    "Scale [HADS], and the Repeatable Battery for the Assessment of "
    "Neuropsychological Status [RBANS]), applying published cutoffs and "
    "cohort-relative summaries. For each patient it generates an eight-step "
    "rule-based reasoning chain, cohort-contextualized visualizations, and "
    "PDF reports in three variants for clinical peers, referring physicians, "
    "and patients. Analyses were performed on an analysis-ready cohort "
    "dataset comprising 105 adults (65 IBS, 40 healthy controls) from the "
    "Bergen Brain\u2013Gut\u2013Microbiota study. The pipeline was "
    "co-developed with an AI coding assistant; no AI is used at runtime."
)

ABSTRACT_RESULTS = (
    "The pipeline identified flagged findings in sleep (50%), fatigue (40%), "
    "anxiety (35%), and attention (30%), with multi-domain flags in 60%. "
    "Cross-domain reasoning chains linked co-occurring findings to plausible "
    "mechanisms (e.g., insomnia\u2013fatigue\u2013attention cascades). Two case "
    "illustrations demonstrated differentiated clinical formulations across "
    "diverse profiles."
)

ABSTRACT_CONCLUSIONS = (
    "The framework augments rather than replaces clinical judgment, and its "
    "transparent, reproducible architecture supports professional oversight. "
    "Full realization depends on the ongoing digitalization of cognitive "
    "assessment instruments for remote administration."
)

# Statement of Research Significance (NEW JINS requirement, <=150 words, plain
# language, no acronyms, three underlined headings).
SRS_RESEARCH_QUESTION = (
    "Can a transparent, rule-based system that combines questionnaire and "
    "cognitive screening data into an integrated clinical summary support "
    "neuropsychologists during the planning phase of an outpatient examination?"
)

SRS_MAIN_FINDINGS = (
    "Applied to one hundred and five adults with and without irritable bowel "
    "syndrome, the system produced patient-level summaries that highlighted "
    "clinically meaningful patterns across sleep, fatigue, mood, attention, "
    "and broader thinking ability, and generated readable summaries tailored "
    "separately for clinical colleagues, referring doctors, and patients and "
    "their families."
)

SRS_STUDY_CONTRIBUTIONS = (
    "The work shows that a deterministic, rule-based system can deliver "
    "structured pre-examination summaries without using artificial "
    "intelligence at the moment the patient is processed. Because every step "
    "traces back to an explicit rule, the approach offers a transparent and "
    "traceable model for using artificial intelligence safely during the "
    "design phase while keeping clinical decisions firmly with the "
    "neuropsychologist."
)


# ---------------------------------------------------------------------------
# Body sections (each as list of paragraph texts; tuples ("HEAD", text) mark headings)
# ---------------------------------------------------------------------------

INTRODUCTION = [
    "In outpatient neuropsychological practice, clinicians often begin their "
    "pre-examination preparation with a referral letter and a set of intake "
    "questionnaires that must be synthesized into a clinically meaningful "
    "picture of the patient's difficulties and likely needs. This synthesis "
    "requires forming preliminary hypotheses about which cognitive, "
    "emotional, and functional domains are most relevant, whether "
    "interactions across domains are likely to affect test performance, and "
    "which aspects of the examination should be prioritized. This work is "
    "often done under time pressure and with limited opportunity for "
    "systematic review. As a result, clinically relevant patterns may be "
    "overlooked, and the examination may default to a standard battery "
    "rather than being tailored to the individual patient. More broadly, "
    "neuropsychologists must balance clinical productivity with precision "
    "in patient care while integrating complex multi-domain information, "
    "tailoring assessments to the individual patient, and preparing reports "
    "that are both clinically accurate and understandable to others. Report "
    "writing itself remains a major workload burden, often requiring two to "
    "ten hours per patient depending on report length and patient complexity "
    "(Postal et al., 2018). In this setting, tools that can support "
    "efficiency while preserving clinical precision are naturally of interest.",

    "This helps explain why artificial intelligence has become increasingly "
    "relevant to neuropsychology. In a recent perspective article, Lundervold "
    "(2025) proposed the framework of precision neuropsychology, within which "
    "incorporating AI into practice presents both opportunities and risks. "
    "Used carefully and ethically, AI may help reduce clinician workload, "
    "improve access to services, and extend aspects of neuropsychological "
    "care to underserved populations (Kronenberger et al., 2025). At the "
    "same time, such use must remain transparent, clinically grounded, and "
    "subject to professional oversight so that computational support "
    "strengthens rather than displaces clinical judgment (DeRight & Puente, "
    "2026; Lundervold, 2025).",

    "Despite broader advances in medical AI (Mesk\u00f3 & Topol, 2023; "
    "Thirunavukarasu et al., 2023), relatively few concrete changes in "
    "everyday neuropsychological practice can be attributed directly to AI "
    "adoption (DeRight & Puente, 2026). Existing applications have mainly "
    "focused on computerized testing, automated scoring, and diagnostic "
    "classification (Andersen et al., 2026; Parsons et al., 2018). These "
    "developments are useful for organizing scores and findings, but they "
    "do not address the interpretive task at the center of neuropsychological "
    "work: bringing cognitive, emotional, and genetic and environmental "
    "factors together into a coherent clinical formulation. In addition, "
    "neuropsychological reports must be tailored to the differing needs of "
    "patients and referral sources (Postal et al., 2018).",

    "This leaves an important gap between what automated systems can "
    "calculate and what clinicians need before meeting the patient. In "
    "practice, the neuropsychologist must consider not only whether a domain "
    "is elevated, but also how findings relate to one another and which "
    "aspects of the examination deserve particular attention. Support at "
    "this stage therefore requires more than score reporting. It requires a "
    "structured way of relating findings across domains so that screening "
    "data can inform examination planning in a clinically meaningful way.",

    "IBS provides a useful context for examining this challenge. It is a "
    "common functional gastrointestinal disorder affecting approximately "
    "14% of the global population and associated with chronic abdominal "
    "pain, altered bowel habits, and reduced quality of life (Arif et al., "
    "2025). Through the gut\u2013brain axis (Cryan et al., 2019; Mayer et al., "
    "2015), IBS may also be linked to sleep disturbance (Tu et al., 2017), "
    "fatigue (Han & Yang, 2016), emotional symptoms such as anxiety and "
    "depression (Staudacher et al., 2023), and more subtle cognitive "
    "difficulties (Billing et al., 2024; Lam et al., 2019). Because these "
    "difficulties often co-occur and may influence one another, IBS offers "
    "a clinically relevant context for examining how multi-domain screening "
    "data may be integrated before formal assessment. In the present study, "
    "this question is examined using data from the Bergen "
    "Brain\u2013Gut\u2013Microbiota study (Berentsen et al., 2020), and the data "
    "set presented in the present study overlaps with data analyzed in "
    "prior work on psychological distress subgroups in this cohort "
    "(Lundervold et al., 2024). Both that study and a subsequent analysis "
    "(Lundervold et al., 2026) have shown considerable overlap in "
    "neuropsychological profiles between IBS patients and healthy controls, "
    "making the full cohort a useful testbed across a broad range of symptom "
    "profiles.",

    "In this study, we present a fully automated, deterministic pipeline as "
    "a proof-of-concept framework for pre-examination screening in "
    "outpatient neuropsychological practice. Using five established "
    "instruments covering sleep, fatigue, emotional distress, sustained "
    "attention, and neurocognitive function, the pipeline applies published "
    "cutoffs together with cohort-based interpretive rules to generate a "
    "structured clinical overview, visual summaries, and report-ready "
    "outputs. It is intended as decision support for the pre-examination "
    "phase rather than as an autonomous diagnostic system, and the "
    "clinician retains full responsibility for diagnostic and therapeutic "
    "conclusions.",
]

# ---------- Method ----------
PARTICIPANTS_PARAS = [
    "The cohort comprises N = 105 adults: 65 patients meeting Rome IV criteria "
    "for IBS and 40 age- and gender-matched healthy controls (HC). Participants "
    "were recruited through the National Centre for Functional Gastrointestinal "
    "Disorders at Haukeland University Hospital, Bergen, Norway, as part of the "
    "Bergen Brain\u2013Gut\u2013Microbiota (B-BGM) study (Berentsen et al., 2020). "
    "Inclusion criteria for IBS patients required an Irritable Bowel Syndrome "
    "Severity Scoring System (IBS-SSS) score \u2265 175, corresponding to at "
    "least moderate symptom severity (Francis et al., 1997).",

    "The study was conducted in accordance with the Declaration of Helsinki "
    "and was approved by the Regional Committee for Medical and Health Research "
    "Ethics, South East Norway (REK2015-01621). All participants provided "
    "written informed consent.",

    "All analyses were performed on an analysis-ready cohort file derived from "
    "the source dataset after documented data cleaning, while the raw source "
    "file was preserved unchanged. The cleaning decisions are documented in "
    "the project repository.",

    "Demographic characteristics are summarized in Table 1. The IBS group "
    "included three subtypes: IBS-D (diarrhea-predominant, n = 24), IBS-C "
    "(constipation-predominant, n = 9), and IBS-M (mixed, n = 32). IBS "
    "symptom severity was assessed using the Irritable Bowel Syndrome "
    "Severity Scoring System, IBS-SSS (range 0\u2013500; available for n = 56 "
    "IBS patients), with a mean of M = 273.8 (SD = 71.3).",

    "[INSERT TABLE 1 HERE]",
]

INSTRUMENTS_PARAS = [
    "Five assessment domains were evaluated using established instruments with "
    "known psychometric properties. The instruments differ in their "
    "administration requirements, which has direct implications for how much "
    "of the screening profile can be collected before the patient's first "
    "clinic visit. Three self-report questionnaires, the Bergen Insomnia "
    "Scale (BIS), Chalder Fatigue Scale (Chalder), and Hospital Anxiety and "
    "Depression Scale (HADS), can be administered digitally and completed by "
    "patients remotely. The Conners' Continuous Performance Test, Third "
    "Edition (CPT-3), is self-administered but currently requires "
    "proprietary software on a clinic computer, restricting it to in-clinic "
    "use. The Repeatable Battery for the Assessment of Neuropsychological "
    "Status (RBANS) requires administration by a trained psychometrician. "
    "Thus, in the current landscape, the questionnaire data can arrive "
    "before the consultation, while the cognitive test data require an "
    "initial clinic-based session:",
]

INSTRUMENT_LIST = [
    ("Sleep/Insomnia \u2013 Bergen Insomnia Scale (BIS) [self-report]: ",
     "Six items scored 0\u20137 (days/week), total 0\u201342 (Pallesen et al., "
     "2008). Pipeline cutoffs: Minimal (\u2264 6), Mild (7\u201314), Moderate "
     "(15\u201324), Severe (\u2265 25); clinical flags at total \u2265 19 or "
     "\u2265 3 items at \u2265 3 days/week."),

    ("Sustained attention \u2013 Conners' CPT-3 [self-administered, "
     "clinic-based]: ",
     "A 14-minute continuous performance test yielding T-scored metrics "
     "(M = 50, SD = 10) including Detectability (d\u2032), Omissions, "
     "Commissions, and Hit Reaction Time (Conners, 2014). Pipeline "
     "thresholds: T \u2265 60 (mildly elevated), T \u2265 65 (clinically "
     "significant)."),

    ("Fatigue \u2013 Chalder Fatigue Scale [self-report]: ",
     "Eleven items with bimodal scoring (0\u201311) covering physical and "
     "mental fatigue (Chalder et al., 1993). Pipeline caseness threshold: "
     "\u2265 4."),

    ("Emotional distress \u2013 HADS [self-report]: ",
     "Anxiety (HADS-A) and Depression (HADS-D) subscales, each 0\u201321 "
     "(Zigmond & Snaith, 1983). Pipeline cutoffs: Normal (\u2264 7), "
     "Borderline (8\u201310), Clinical (\u2265 11) (Bjelland et al., 2002)."),

    ("Neurocognition \u2013 RBANS [clinician-administered]: ",
     "Ten subtests assessing the five cognitive domains (Immediate Memory, "
     "Visuospatial/Constructional, Language, Attention, Delayed Memory) were "
     "administered by a trained psychometrician in approximately 30 minutes "
     "using the Norwegian version (Randolph, 2013). In the pipeline, raw "
     "RBANS subtests are standardized within the cohort and averaged into "
     "domain summary composites aligned with these five domains, while "
     "recognition scores are retained as an auxiliary summary and "
     "RBANS_Sum_Raw is used as a broad total-score indicator. Cognitive "
     "flags are raised for marked cohort-relative weakness (domain-summary "
     "or total-score percentile < 16)."),
]

INSTRUMENTS_TAIL = (
    "The CPT-3 and RBANS are retained as separate domains because they "
    "assess complementary aspects of cognition: the CPT-3 targets sustained "
    "attention and response inhibition, while the RBANS covers broad "
    "cognitive function. Their separation also enables the reasoning engine "
    "to distinguish differential patterns (e.g., isolated sustained "
    "attention deficits driven by fatigue vs. broader cognitive involvement)."
)

PIPELINE_OVERVIEW = [
    "The deterministic pipeline is implemented as a standalone Python "
    "program that combines a quantitative analysis layer with structured "
    "clinical reasoning. The pipeline was applied to the analysis-ready "
    "cohort file described above. Cleaning decisions that required source "
    "verification were not overwritten at runtime. Instead, the upstream "
    "files preserved the recorded values together with explicit flags, "
    "allowing downstream interpretation to remain conservative and auditable.",
]

CLARIFICATION_AI = (
    "During development, the pipeline was co-authored with an AI coding "
    "assistant (Cursor IDE with Claude Opus 4.6 and GPT-5.4); all "
    "AI-generated content was reviewed, verified, and edited by the "
    "authors. At runtime, however, no AI is involved: the deployed pipeline "
    "contains no large language model API calls, no AI client libraries, "
    "and no network dependencies. All clinical classifications, reasoning "
    "chains, and recommendations are produced by deterministic, rule-based "
    "logic operating on published cutoffs and pre-authored text templates "
    "(Supplementary Material S1). In short, AI was used to author the "
    "rules; the rules themselves execute deterministically without AI."
)

PIPELINE_STAGES_INTRO = "The pipeline processes each patient through five sequential stages:"

PIPELINE_STAGES = [
    ("Data ingestion and preprocessing: ",
     "Loading the analysis-ready cohort file, computing derived scores (BIS "
     "total, Chalder bimodal total, HADS total), and validating score "
     "ranges. Upstream cleaning standardizes datatypes, missing-value "
     "encoding, and selected metadata labels while preserving unresolved "
     "discrepancies as flagged values rather than silently correcting them."),

    ("Per-domain analysis: ",
     "For each of the five domains, the pipeline applies established "
     "clinical cutoffs to generate severity classifications and identify "
     "clinically significant findings. For the self-report instruments "
     "(BIS, Chalder, HADS), cutoffs are applied directly to raw or derived "
     "sum scores. For CPT-3, the pipeline uses software-generated T-scores "
     "and interprets higher values as less favorable across the selected "
     "metrics; Detectability, Omissions, Commissions, HRT, HRT SD, "
     "Perseverations, and Variability are flagged at T \u2265 60/T \u2265 65. "
     "For RBANS, the pipeline uses cohort-standardized raw subtests rather "
     "than age-corrected index columns, with a total raw-score composite "
     "retained as a broad overall indicator. Cognitive flags are raised for "
     "marked cohort-relative weakness (domain-summary or total-score "
     "percentile < 16). Because missingness is handled on a domain-specific "
     "basis, the effective denominator varies across measures."),

    ("Cross-domain pattern analysis: ",
     "A rule-based engine identifies co-occurring elevations across domains "
     "and generates mechanistic hypotheses. For example, elevated BIS "
     "combined with low cohort-relative RBANS memory summaries triggers "
     "hypotheses about impaired sleep-dependent memory consolidation, "
     "whereas co-occurring HADS anxiety elevation with CPT decrements "
     "triggers hypotheses about anxiety-related attentional interference. "
     "The full set of cross-domain rules is documented in Supplementary "
     "Material S1."),

    ("Eight-step clinical reasoning chain: ",
     "A structured protocol designed to mirror the integrative reasoning "
     "used in clinical neuropsychological interpretation (Figure 1; example "
     "content in Table 2). Step 1 establishes demographic and clinical "
     "context. Steps 2\u20136 assess each domain independently: sleep (BIS), "
     "fatigue (Chalder), emotional distress (HADS), sustained attention "
     "(CPT), and neurocognition (RBANS). Step 7 integrates findings across "
     "domains, identifying co-occurring patterns and formulating mechanistic "
     "hypotheses. Step 8 synthesizes the integrated profile into a "
     "prognostic formulation. The full reasoning-chain specification is "
     "provided in Supplementary Material S1."),

    ("Output generation: ",
     "Three output streams are produced: (a) a structured JSON file "
     "containing quantitative results, interpretations, flags, reasoning "
     "steps, and recommendations; (b) two visualization types, a "
     "multi-panel domain profile and a radar plot, each produced in three "
     "audience-tailored variants; and (c) a compiled PDF report integrating "
     "text, tables, and figures."),
]

INSERT_FIGURE_1 = "[INSERT FIGURE 1 HERE]"

AUDIENCE_DESIGN_PARAS = [
    "A distinctive feature of the pipeline is the generation of outputs "
    "tailored to three audiences (Table 3):",
]
AUDIENCE_BULLETS = [
    ("Clinical peers: ",
     "Full statistical detail including z-scores, percentile ranks, and "
     "effect sizes, with technical labels and expanded radar plots."),
    ("Referring physicians: ",
     "Simplified summaries with traffic-light color coding, brief clinical "
     "annotations, and compact radar plots designed for rapid triage and "
     "referral decisions."),
    ("Patients and families: ",
     "Accessible infographic-style outputs with plain-language labels, "
     "qualitative anchors, and non-alarming visual design."),
]
AUDIENCE_TAIL = (
    "All visualizations use a color-blind-friendly palette (Wong, 2011) and "
    "normalize scores to a common percentile-of-wellness scale (0\u2013100, "
    "higher = better functioning) with inverted polarity for scales where "
    "high raw scores indicate worse outcomes."
)

RECOMMENDATIONS_PARAS = [
    "The pipeline generates two categories of recommendations relevant to "
    "neuropsychological decision-making: therapeutic interventions and "
    "further examinations. Each recommendation is explicitly linked to the "
    "domain findings that justify it and uses conditional logic intended to "
    "reflect clinical reasoning (e.g., \u201cIf memory weaknesses persist "
    "after sleep intervention, consider expanded memory testing\u201d). "
    "Recommendations reference established treatment guidelines where "
    "applicable (e.g., cognitive behavioral therapy for insomnia [CBT-I]: "
    "Grade A recommendation; Riemann et al., 2017). They are intended as a "
    "starting point for clinician review rather than as stand-alone "
    "clinical advice.",
]

REPRO_PARAS = [
    "The pipeline source code and anonymised example outputs are available "
    "in a public GitHub repository "
    "(https://github.com/arvidl/AI-driven-neuropsych-screening), together "
    "with an environment specification file (environment.yml) for "
    "dependency replication. The cohort dataset is not publicly available "
    "due to ethics approval conditions; reproducibility at the dataset "
    "level is supported by documentation of cleaning decisions in the "
    "repository. The complete audience-tailored reports generated for the "
    "two case illustrations are provided as supplementary files.",
]

STATS_GROUP_PARAS = [
    "IBS\u2013HC group differences across all five domains were reassessed on "
    "the analysis-ready cohort file and are treated here as secondary, "
    "context-setting analyses rather than as the paper's primary empirical "
    "contribution. Comparisons used two-tailed independent-samples Welch's "
    "t-tests with effect sizes reported as Cohen's d (pooled SD). "
    "Significance was set at \u03b1 = .05 with no correction for multiple "
    "comparisons, consistent with the exploratory proof-of-concept nature "
    "of the study. Domain-specific complete-case samples were used for each "
    "comparison.",
]

STATS_PIPELINE_EVAL = [
    "Pipeline outputs were re-evaluated on the analysis-ready cohort file "
    "along three dimensions: (a) quantitative accuracy, that is, whether "
    "computed scores, percentiles, cutoff classifications, and flags "
    "matched the cleaned input data and documented scoring rules; (b) "
    "clinical coherence, that is, whether the generated reasoning chains "
    "remained clinically plausible after data cleaning and score "
    "verification; and (c) output completeness, that is, whether analyzable "
    "patient-level outputs could be generated across the full cohort.",
]

# ---------- Results ----------
RESULTS_COHORT = [
    "Demographic and clinical characteristics from the analysis-ready cohort "
    "file are presented in Table 1. The IBS and HC groups did not differ "
    "significantly in age (t(77) = 0.90, p = .37) or education (t(68) = "
    "\u22121.54, p = .13; HC n = 28 because of missing data). The cohort was "
    "predominantly female (74.3%), consistent with the known sex "
    "distribution of IBS (Sperber et al., 2021). The two groups were well "
    "matched on sample-level characteristics. Domain-specific denominators "
    "vary across instruments because of blockwise missingness in a subset "
    "of participants. For clarity, the RBANS rows in Table 1 report "
    "conventional index scores for cohort-level group comparison, whereas "
    "the patient-level pipeline uses raw RBANS subtests and "
    "cohort-standardized summary composites.",
]

RESULTS_GROUP_DIFF = [
    "Table 1 summarizes IBS\u2013HC comparisons. Particularly pronounced "
    "differences emerged for fatigue (Chalder total, p < .001), anxiety "
    "(HADS-A, p < .001), insomnia (BIS total, p < .001), and depression "
    "(HADS-D, p < .001). CPT Detectability also differed significantly "
    "between groups (p < .01), and CPT Omissions reached significance as "
    "well (p < .01). RBANS index scores revealed significant IBS\u2013HC "
    "differences for Total Scale (p < .01), Immediate Memory (p < .01), "
    "Attention (p < .05), and Delayed Memory (p < .05), with non-significant "
    "differences for Visuospatial and Language.",

    "These findings remain consistent with the gut-brain axis literature "
    "(Cryan et al., 2019; Mayer et al., 2015): IBS patients showed elevated "
    "insomnia, fatigue, and emotional distress relative to controls. At the "
    "same time, these group comparisons are secondary to the main purpose "
    "of the paper, which is to demonstrate a transparent deterministic "
    "screening pipeline.",
]

RESULTS_PIPELINE_OUTPUT = [
    "The analysis-ready cohort file was processed successfully for all 105 "
    "participants. For each participant, the pipeline generates a "
    "structured clinical analysis, a report-ready LaTeX source file, a "
    "compiled PDF report, and two visualization families (multi-panel "
    "profiles and radar plots) in three audience-tailored variants. Thus, "
    "when full report generation is invoked, the pipeline yields 15 output "
    "files per participant. The pipeline preserved the overall "
    "distributional pattern while domain-flag counts reflect the scoring "
    "and classification rules described above.",
]

RESULTS_DISTRIBUTION_INTRO = (
    "The distribution of domain-specific flags across the 105 pipeline "
    "summaries was as follows:"
)

RESULTS_DISTRIBUTION_BULLETS = [
    ("Sleep (BIS): ",
     "53 participants (50%) triggered a sleep-domain flag through "
     "moderate/severe insomnia classification, total score \u2265 19, and/or "
     "\u2265 3 BIS items endorsed at \u2265 3 days/week; 40 of these were IBS "
     "patients."),
    ("Fatigue (Chalder): ",
     "42 participants (40%) met the fatigue caseness threshold (\u2265 4); "
     "36 were IBS patients."),
    ("Emotional distress (HADS): ",
     "37 participants (35%) reached borderline or clinical caseness on the "
     "Anxiety subscale (\u2265 8); 31 were IBS patients. For Depression, 8 "
     "participants (8%) reached borderline or clinical caseness; 7 were IBS "
     "patients."),
    ("Attention (CPT-3): ",
     "32 participants (30%) had at least one flagged CPT metric "
     "(Detectability, Omissions, Commissions, HRT, HRT SD, Perseverations, "
     "or Variability at T \u2265 60); 24 of these were IBS patients."),
    ("Neurocognition (RBANS): ",
     "48 participants (46%) met the pipeline's cognition-flag criterion, "
     "defined as at least one RBANS domain-summary percentile < 16 or a "
     "total raw-score percentile < 16; 36 of these were IBS patients."),
]

RESULTS_DISTRIBUTION_TAIL = (
    "The pipeline identified multi-domain elevations (flags in \u2265 2 "
    "domains) in 63 participants (60%), predominantly within the IBS group "
    "(n = 51)."
)

CASE_INTRO = [
    "We present two illustrative cases demonstrating the pipeline's "
    "clinical reasoning and audience-tailored output. Table 2 summarizes "
    "the eight-step reasoning chain across both cases and highlights the "
    "contrast between a circumscribed sleep-centered profile and a broader "
    "multi-domain profile.",
    "[INSERT TABLE 2 HERE]",
]

CASE_1 = {
    "intro": "The patient is a 38-year-old male with IBS-D (moderate severity, IBS-SSS = 195).",
    "pipeline_lead": "Pipeline output. ",
    "pipeline_body": (
        "As summarized in Table 2, the pipeline produced a relatively focal "
        "profile centered on clinically elevated sleep disturbance, with "
        "Detectability at the CPT flag threshold and otherwise preserved "
        "fatigue, mood, and cohort-relative cognition. The reasoning chain "
        "therefore characterized the case as an interacting sleep\u2013"
        "attention pattern and recommended prioritising CBT-I and structured "
        "sleep-hygiene measures, with re-evaluation of sustained attention if "
        "difficulties persist after sleep treatment."
    ),
    "figures_para": (
        "The corresponding clinical multi-panel profile and "
        "audience-tailored radar plots are shown in Figures 2 and 3. The "
        "complete audience-tailored report for this case is provided as "
        "Supplementary Material S2 (case_1_report.pdf)."
    ),
    "figure_callouts": ["[INSERT FIGURE 2 HERE]", "[INSERT FIGURE 3 HERE]"],
    "interp_lead": "Clinical interpretation Case 1 after reading the rule-based report. ",
    "interp_body": (
        "Prior to examination, these data warrant careful consideration in "
        "planning the assessment. The convergence of moderate insomnia, "
        "borderline attentional inefficiency, and verbal-learning weakness "
        "could suggest sleep disturbance as a principal upstream "
        "contributor, but this interpretation should be held tentatively. "
        "Detectability (d\u2019), a core index of the capacity to "
        "discriminate target from non-target stimuli, is of particular "
        "concern. In IBS, hypervigilance toward somatic and threat-related "
        "stimuli may lower the response criterion independently of sleep "
        "quality, reducing detectability even without a primary attentional "
        "capacity deficit (Akbari et al., 2025). The upcoming examination "
        "should therefore disentangle the relative contributions of sleep "
        "disruption and hypervigilance-driven arousal, and determine "
        "whether the verbal memory difficulties reflect "
        "sleep-mediated consolidation impairment or a more specific "
        "learning vulnerability. Sleep-focused intervention remains "
        "indicated, but the full examination should precede any decision "
        "to defer broader neuropsychological follow-up."
    ),
}

CASE_2 = {
    "intro": (
        "A second IBS patient (IBS-M subtype, female, age 31, IBS-SSS = 305) "
        "provides a contrasting example of multi-domain involvement."
    ),
    "pipeline_lead": "Pipeline output. ",
    "pipeline_body": (
        "As summarized in Table 2, the second case showed a broader profile "
        "with severe insomnia, maximum fatigue caseness, clinical anxiety, "
        "and cohort-relative RBANS weakness, while sustained attention "
        "remained within expected range and depression remained unflagged. "
        "The pipeline's cross-domain reasoning linked insomnia and fatigue, "
        "noted the bidirectional mood\u2013sleep relationship, and supported "
        "a coordinated multi-component intervention strategy before "
        "reassessing the cognitive weaknesses, with close gastroenterology "
        "follow-up given the high IBS symptom burden."
    ),
    "figures_para": (
        "The corresponding clinical multi-panel and radar visualizations "
        "for this case are shown in Figures 4 and 5. The complete "
        "audience-tailored report for this case is provided as "
        "Supplementary Material S3 (case_2_report.pdf)."
    ),
    "figure_callouts": ["[INSERT FIGURE 4 HERE]", "[INSERT FIGURE 5 HERE]",
                         "[INSERT TABLE 3 HERE]"],
    "interp_lead": "Clinical interpretation Case 2 after reading the rule-based report. ",
    "interp_body": (
        "While the AI-generated report appropriately identifies sleep "
        "disturbance, fatigue, and anxiety as primary intervention targets, "
        "the figures reveal several features that warrant clinical "
        "attention beyond what the rule-based output captures. Most notably, "
        "the RBANS subtest profile shows a degree of specificity that is "
        "difficult to attribute to insomnia or anxiety alone. The Naming "
        "subtest falls severely below the cohort mean, a pattern more "
        "consistent with a language network vulnerability than with the "
        "diffuse processing inefficiency typically associated with sleep "
        "disruption or elevated arousal. Fatigue and insomnia tend to "
        "impair processing speed, working memory, and retrieval, but not "
        "confrontation naming, and this dissociation should prompt careful "
        "observation during the examination itself. Equally important is "
        "the stark contrast visible in the radar plots between preserved "
        "attentional performance, with concentration near the 50th "
        "percentile, and severely compromised memory and thinking at "
        "approximately the 3rd percentile. This degree of dissociation "
        "argues against a unitary sleep-fatigue explanation and raises the "
        "possibility of a primary cognitive vulnerability operating "
        "independently of the functional factors identified by the "
        "pipeline. Taken together, these observations suggest that "
        "comprehensive neuropsychological follow-up should proceed "
        "concurrently. The severity and specificity of the cognitive "
        "profile visible here justifies prioritizing clarification of the "
        "memory and language weaknesses as an immediate clinical step "
        "rather than a deferred one."
    ),
}

# ---------- Discussion ----------
DISCUSSION_SUMMARY = [
    "We developed and demonstrated a deterministic, rule-based pipeline for "
    "automated pre-examination screening in outpatient neuropsychological "
    "practice. Applied to a cohort of 105 participants (65 IBS, 40 HC), "
    "the pipeline identified clinically significant findings across five "
    "assessment domains, generated structured cross-domain reasoning "
    "chains, and produced audience-tailored outputs for clinical peers, "
    "referring physicians, and patients.",

    "Its primary purpose is to provide the neuropsychologist with a "
    "structured synthesis of available screening data before the clinical "
    "encounter. In this way, it may reduce the time needed for "
    "pre-examination preparation and enable a more targeted clinical "
    "interview and test selection.",

    "The main contribution of the framework is not automated diagnosis, but "
    "automated integration. Rather than merely organizing scores, the "
    "pipeline combines domain-specific findings into a preliminary clinical "
    "formulation and expresses that formulation in formats adapted to "
    "different end users. The case illustrations suggest that this approach "
    "can differentiate between relatively circumscribed and broader "
    "multi-domain profiles while also making explicit where subsequent "
    "clinician review remains essential.",
]

DISCUSSION_PRIOR = [
    "Traditional template-based systems can present summaries with scores "
    "but typically provide more limited support for cross-domain reasoning.",

    "A central feature of the pipeline is the eight-step reasoning chain, "
    "which mirrors the sequence of integrative judgments clinicians make "
    "when reviewing screening data. Rather than listing isolated "
    "elevations, it links findings across domains and generates clinically "
    "plausible hypotheses about how sleep, fatigue, emotional distress, "
    "sustained attention, and broader cognition may interact. In this "
    "sense, the framework aims to support both interpretation and "
    "communication.",

    "The deterministic architecture is important in this context. "
    "Clinicians need to understand why a tool generated a particular "
    "interpretation, and to be able to challenge it when the clinical "
    "picture calls for it. Because every classification, flag, reasoning "
    "step, and recommendation traces back to an explicit rule, the "
    "pipeline offers transparency, reproducibility, and traceability. This "
    "is a practical advantage in clinical neuropsychology, where "
    "interpretive judgment is itself a core professional competency and "
    "where opaque generative output would be difficult to justify "
    "clinically.",
]

DISCUSSION_CLINICAL = [
    "From a workflow perspective, the pipeline is best understood as a "
    "structured briefing tool for the pre-examination phase. In many "
    "outpatient services, patients or families already provide "
    "questionnaires or background information before the appointment "
    "(e.g., King's College Hospital NHS Foundation Trust, 2026; Stanford "
    "Health Care, 2026). The present framework extends that workflow by "
    "automatically integrating the available screening data into a "
    "cross-domain summary before the first face-to-face encounter. Instead "
    "of reviewing separate forms manually at the start of the consultation, "
    "the clinician receives a synthesized overview of flagged areas, "
    "possible cross-domain interactions, and preliminary next-step "
    "suggestions.",

    "This may have several practical benefits. The screening summary may "
    "help clinicians prioritise patients with multi-domain elevations, "
    "guide the selection of follow-up instruments, and serve as a "
    "discussion aid during the clinical interview. Because the pipeline "
    "applies the same cutoffs and rules across patients, it may also "
    "reduce inconsistency that can arise when intake material is reviewed "
    "using memory or idiosyncratic judgment alone, and the standardized "
    "output may serve as a starting point for later documentation "
    "(Postal et al., 2018).",

    "The cross-domain component is particularly relevant to "
    "neuropsychological practice. Its purpose is not to infer causality "
    "autonomously, but to highlight clinically meaningful constellations "
    "of findings that might otherwise remain fragmented across separate "
    "instruments. Such outputs are best understood as "
    "hypothesis-generating rather than definitive and require clinical "
    "verification during the subsequent assessment.",

    "The audience-tailored outputs address a related practical problem. "
    "Referring physicians often prefer brief, targeted summaries, whereas "
    "patients and family members benefit from accessible language and "
    "visual presentation (Gruters et al., 2022; Postal & Armstrong, 2024; "
    "Postal et al., 2018). By producing distinct but data-equivalent "
    "outputs for clinical peers, physicians, and patients, the framework "
    "supports communication without requiring the clinician to create "
    "multiple reports from scratch.",

    "The case illustrations clarify an important boundary condition: the "
    "pipeline produces a structured preliminary formulation, not a complete "
    "clinical interpretation. In both cases, the rule-based report "
    "identified the major domain findings, but clinician interpretation "
    "added inferences the rules alone did not capture. In Case 1, this "
    "concerned the mechanistic significance of reduced detectability, "
    "where hypervigilance-driven criterion shift may operate independently "
    "of sleep quality. In Case 2, it concerned the subtest-level "
    "specificity of the RBANS profile, where the naming deficit and the "
    "dissociation between preserved attention and compromised memory and "
    "language raised the possibility of a primary cognitive vulnerability. "
    "Together, these cases illustrate that rule-based reasoning performs "
    "well in integrating domain-level findings, but that clinician "
    "interpretation remains essential for recognizing mechanistic "
    "dissociations and determining the sequencing of intervention and "
    "further assessment.",

    "The framework is therefore best understood as clinician-supervised "
    "decision support. Rules encode population-level evidence and "
    "predefined thresholds, whereas a skilled neuropsychologist integrates "
    "contextual factors, domain knowledge, clinical experience, and the "
    "patient's own account of difficulties. The pipeline does not diagnose "
    "and does not interact with patients; all outputs require professional "
    "review and may need to be modified when factors such as language, "
    "education, culture, sensory limitations, genetics, or referral "
    "context alter the meaning of the data. In this respect, the framework "
    "may extend efficiency and consistency while preserving the "
    "neuropsychologist's interpretive authority (Lundervold, 2025).",
]

DISCUSSION_LIMITATIONS = [
    "Several limitations should be acknowledged. The present study is a "
    "single-cohort, cross-sectional proof of concept based on a specific "
    "instrument battery (BIS, CPT-3, Chalder, HADS, RBANS), and extension "
    "of the framework to other batteries or clinical populations would "
    "require reconfiguration of cutoffs, variable mappings, and "
    "domain-specific logic. In addition, the validation reported here "
    "concerns computational accuracy and output completeness rather than "
    "formal clinical validity. Further work comparing pipeline-generated "
    "reports with clinician-written reports, using blinded expert ratings, "
    "is needed before broader implementation can be considered.",

    "The interpretive scope is also bounded by the structure of the "
    "reasoning rules. The cross-domain engine generates plausible "
    "hypotheses but does not establish causal relationships, and its "
    "outputs require clinical evaluation. Cohort-relative percentiles are "
    "based on N = 105, and the RBANS summaries are cohort-standardized "
    "rather than norm-corrected, which limits interpretive precision. "
    "Finally, the full pre-examination workflow envisioned by the "
    "framework was not achievable within the present design. Although "
    "remotely administered cognitive tools are already available in some "
    "settings, the present dataset required clinic-based collection of "
    "CPT-3 and RBANS data. The study did not examine usability, "
    "accessibility, or equity, and it is unknown how the pipeline's "
    "outputs would perform for patients with limited digital access, "
    "language barriers, low health literacy, or disability-related access "
    "needs.",
]

DISCUSSION_FUTURE = [
    "Future work should address both clinical translation and further "
    "development of the framework. One important direction is to examine "
    "how the pipeline performs when paired with cognitive assessment "
    "tools that allow a larger proportion of the screening profile to be "
    "collected before the first clinic visit. Another is longitudinal "
    "application, as repeated processing of patient data could support "
    "structured monitoring of symptom change and treatment response over "
    "time. Because the pipeline is modular, it may also be extended to "
    "additional neuropsychological instruments and clinical populations, "
    "allowing evaluation of how well the present reasoning logic "
    "generalizes across assessment contexts.",

    "Equally important will be studies of usability and implementation in "
    "routine care. Evaluation involving neuropsychologists, referring "
    "physicians, and patients is needed to determine whether the "
    "audience-tailored outputs improve examination planning, clinical "
    "communication, and workflow efficiency. Such work should test "
    "performance across patients with differing language backgrounds, "
    "digital access, health literacy, and disability-related needs. In the "
    "longer term, integration with electronic health record systems may "
    "support use within ordinary clinical workflows, provided that "
    "transparency, governance, and professional accountability remain "
    "central.",

    "This work also aligns with recent proposals for characterizing AI "
    "systems by their cognitive capabilities and benchmarking them against "
    "meaningful human baselines (Burnell et al., 2026).",
]

CONCLUSIONS = [
    "The present study introduces a proof-of-concept framework for "
    "automated pre-examination screening in outpatient neuropsychological "
    "practice. Within the limits of the present dataset and rule set, the "
    "deterministic pipeline identified clinically relevant findings, "
    "generated structured cross-domain hypotheses, and produced "
    "audience-tailored outputs for different stakeholders. The framework "
    "is intended to support, rather than replace, neuropsychological "
    "judgment, and its deterministic architecture offers transparency, "
    "traceability, and reproducibility. At the same time, it should be "
    "regarded as an initial demonstration rather than as a fully "
    "validated model for routine clinical use. Its clinical value will "
    "depend on formal validation, usability testing, and careful "
    "integration with assessment workflows.",
]

# ---------- References ----------
REFERENCES = [
    "Akbari, R., Salimi, Y., Dehghani-Aarani, F., & Rezayat, E. (2025). "
    "Attention in irritable bowel syndrome: A systematic review of "
    "affected domains and brain-gut axis interactions. Journal of "
    "Psychosomatic Research, 191, 112067. "
    "https://doi.org/10.1016/j.jpsychores.2025.112067",

    "Andersen, S. L., Lundervold, A. J., & Ronold, E. H. (2026). Automated "
    "versus human scoring of the Rey\u2013Osterrieth Complex Figure Test: "
    "A rapid review. Frontiers in Psychiatry, 16, 1746720. "
    "https://doi.org/10.3389/fpsyt.2025.1746720",

    "Arif, T. B., Ali, S. H., Bhojwani, K. D., Sadiq, M., Siddiqui, A. A., "
    "Ur-Rahman, A., Khan, M. Z., Hasan, F., & Shahzil, M. (2025). Global "
    "prevalence and risk factors of irritable bowel syndrome from 2006 to "
    "2024 using the Rome III and IV criteria: A meta-analysis. European "
    "Journal of Gastroenterology & Hepatology, 37(12), 1314\u20131325. "
    "https://doi.org/10.1097/MEG.0000000000002994",

    "Berentsen, B., Nagaraja, B. H., Teige, E. P., Lied, G. A., "
    "Lundervold, A. J., Lundervold, K., Steinsvik, E. K., Hillestad, "
    "E. R., Valeur, J., Br\u00f8nstad, I., Gilja, O. H., Osnes, B., "
    "Hatlebakk, J. G., Ha\u00e1sz, J., Labus, J., Gupta, A., Mayer, "
    "E. A., Benitez-P\u00e1ez, A., Sanz, Y., \u2026 Hausken, T. (2020). "
    "Study protocol of the Bergen brain\u2013gut\u2013microbiota-axis "
    "study. Medicine, 99(37), e21950. "
    "https://doi.org/10.1097/MD.0000000000021950",

    "Billing, J., Berentsen, B., Lundervold, A., Hillestad, E. M. R., Lied, "
    "G. A., Hausken, T., & Lundervold, A. J. (2024). Cognitive function in "
    "patients with irritable bowel syndrome: Impairment is common and only "
    "weakly correlated with depression/anxiety and severity of "
    "gastrointestinal symptoms. Scandinavian Journal of Gastroenterology, "
    "59(1), 25\u201333. https://doi.org/10.1080/00365521.2023.2256916",

    "Bjelland, I., Dahl, A. A., Haug, T. T., & Neckelmann, D. (2002). The "
    "validity of the Hospital Anxiety and Depression Scale: An updated "
    "literature review. Journal of Psychosomatic Research, 52(2), "
    "69\u201377. https://doi.org/10.1016/S0022-3999(01)00296-3",

    "Burnell, R., Yamamori, Y., Firat, O., Olszewska, K., Hughes-Fitt, S., "
    "Kelly, O., Galatzer-Levy, I. R., Morris, M. R., Dafoe, A., Snyder, "
    "A. M., Goodman, N. D., Botvinick, M., & Legg, S. (2026). Measuring "
    "progress toward AGI: A cognitive framework (Technical report). Google "
    "DeepMind. https://storage.googleapis.com/deepmind-media/DeepMind.com/"
    "Blog/measuring-progress-toward-agi/measuring-progress-toward-agi-a-"
    "cognitive-framework.pdf",

    "Chalder, T., Berelowitz, G., Pawlikowska, T., Watts, L., Wessely, S., "
    "Wright, D., & Wallace, E. P. (1993). Development of a fatigue scale. "
    "Journal of Psychosomatic Research, 37(2), 147\u2013153. "
    "https://doi.org/10.1016/0022-3999(93)90081-P",

    "Conners, C. K. (2014). Conners' Continuous Performance Test 3rd "
    "edition (CPT-3): Technical manual. Multi-Health Systems Inc.",

    "Cryan, J. F., O'Riordan, K. J., Cowan, C. S. M., Sandhu, K. V., "
    "Bastiaanssen, T. F. S., Boehme, M., Codagnone, M. G., Cussotto, S., "
    "Fulling, C., Golubeva, A. V., Guzzetta, K. E., Jaggar, M., Long-Smith, "
    "C. M., Lyte, J. M., Martin, J. A., Molinero-Perez, A., Moloney, G., "
    "Morelli, E., Morillas, E., \u2026 Dinan, T. G. (2019). The "
    "microbiota\u2013gut\u2013brain axis. Physiological Reviews, 99(4), "
    "1877\u20132013. https://doi.org/10.1152/physrev.00018.2018",

    "DeRight, J., & Puente, A. N. (2026). Artificial intelligence in "
    "neuropsychological practice: Tool selection, privacy, and billing "
    "guidance. The Clinical Neuropsychologist, 1\u201319. "
    "https://doi.org/10.1080/13854046.2026.2635117",

    "Francis, C. Y., Morris, J., & Whorwell, P. J. (1997). The irritable "
    "bowel severity scoring system: A simple method of monitoring irritable "
    "bowel syndrome and its progress. Alimentary Pharmacology & "
    "Therapeutics, 11(2), 395\u2013402. "
    "https://doi.org/10.1046/j.1365-2036.1997.142318000.x",

    "Gruters, A. A. A., Ramakers, I. H. G. B., Verhey, F. R. J., Kessels, "
    "R. P. C., & de Vugt, M. E. (2022). A scoping review of communicating "
    "neuropsychological test results to patients and family members. "
    "Neuropsychology Review, 32(2), 294\u2013315. "
    "https://doi.org/10.1007/s11065-021-09507-2",

    "Han, C. J., & Yang, G. S. (2016). Fatigue in irritable bowel syndrome: "
    "A systematic review and meta-analysis of pooled frequency and "
    "severity of fatigue. Asian Nursing Research, 10(1), 1\u201310. "
    "https://doi.org/10.1016/j.anr.2016.01.003",

    "King's College Hospital NHS Foundation Trust. (2026). Neuropsychology. "
    "Retrieved March 18, 2026, from "
    "https://www.kch.nhs.uk/services/services-a-to-z/neuropsychology/",

    "Kronenberger, O. R., Gottlieb, M. C., & Cullum, C. M. (2025). Large "
    "language models in neuropsychology: Emerging applications and ethical "
    "considerations [Advance online publication]. The Clinical "
    "Neuropsychologist. https://doi.org/10.1080/13854046.2025.2604094",

    "Lam, N. C.-Y., Yeung, H.-Y., Li, W.-K., Lo, H.-Y., Yuen, C.-F., Chang, "
    "R. C.-C., & Ho, Y.-S. (2019). Cognitive impairment in irritable bowel "
    "syndrome (IBS): A systematic review. Brain Research, 1719, "
    "274\u2013284. https://doi.org/10.1016/j.brainres.2019.05.036",

    "Lundervold, A., Billing, J., Berentsen, B., & Lundervold, A. J. "
    "(2026). Patient similarity networks for irritable bowel syndrome: "
    "Revisiting brain morphometry and cognitive features. Diagnostics, "
    "16(2), 357. https://doi.org/10.3390/diagnostics16020357",

    "Lundervold, A. J. (2025). Precision neuropsychology in the era of AI. "
    "Frontiers in Psychology, 16, 1537368. "
    "https://doi.org/10.3389/fpsyg.2025.1537368",

    "Lundervold, A. J., Billing, J. E., Berentsen, B., Lied, G. A., "
    "Steinsvik, E. K., Hausken, T., & Lundervold, A. (2024). Decoding IBS: "
    "A machine learning approach to psychological distress and "
    "gut\u2013brain interaction. BMC Gastroenterology, 24, 267. "
    "https://doi.org/10.1186/s12876-024-03355-z",

    "Mayer, E. A., Tillisch, K., & Gupta, A. (2015). Gut/brain axis and the "
    "microbiota. The Journal of Clinical Investigation, 125(3), "
    "926\u2013938. https://doi.org/10.1172/JCI76304",

    "Mesk\u00f3, B., & Topol, E. J. (2023). The imperative for regulatory "
    "oversight of large language models (or generative AI) in healthcare. "
    "npj Digital Medicine, 6(1), 120. "
    "https://doi.org/10.1038/s41746-023-00873-0",

    "Pallesen, S., Bjorvatn, B., Nordhus, I. H., Sivertsen, B., Hjornevik, "
    "M., & Morin, C. M. (2008). A new scale for measuring insomnia: The "
    "Bergen Insomnia Scale. Perceptual and Motor Skills, 107(3), "
    "691\u2013706. https://doi.org/10.2466/pms.107.3.691-706",

    "Parsons, T. D., McMahan, T., & Kane, R. (2018). Practice parameters "
    "facilitating adoption of advanced technologies for enhancing "
    "neuropsychological assessment paradigms. The Clinical "
    "Neuropsychologist, 32(1), 16\u201341. "
    "https://doi.org/10.1080/13854046.2017.1337932",

    "Postal, K. S., & Armstrong, K. (2024). Feedback that sticks: The art "
    "of effectively communicating neuropsychological assessment results "
    "(2nd ed.). Oxford University Press.",

    "Postal, K. S., Chow, C., Jung, S., Erickson-Moreo, K., Geier, F., "
    "Lanca, M., & Adams, R. L. (2018). The stakeholders' project in "
    "neuropsychological report writing: A survey of neuropsychologists' "
    "and referral sources' views of neuropsychological reports. The "
    "Clinical Neuropsychologist, 32(3), 326\u2013344. "
    "https://doi.org/10.1080/13854046.2017.1373859",

    "Randolph, C. (2013). RBANS: Repeatable battery for the assessment of "
    "neuropsychological status, Norwegian manual. NCS Pearson, Inc.",

    "Riemann, D., Baglioni, C., Bassetti, C., Bjorvatn, B., Dolenc "
    "Gro\u0161elj, L., Ellis, J. G., Espie, C. A., Garcia-Borreguero, D., "
    "Gjerstad, M., Gon\u00e7alves, M., Hertenstein, E., Jansson-Fr\u00f6jmark, "
    "M., Jennum, P. J., Leger, D., Nissen, C., Parrino, L., Paunio, T., "
    "Pevernagie, D., Verbraecken, J., \u2026 Spiegelhalder, K. (2017). "
    "European guideline for the diagnosis and treatment of insomnia. "
    "Journal of Sleep Research, 26(6), 675\u2013700. "
    "https://doi.org/10.1111/jsr.12594",

    "Sperber, A. D., Bangdiwala, S. I., Drossman, D. A., Ghoshal, U. C., "
    "Simren, M., Tack, J., Whitehead, W. E., Dumitrascu, D. L., Fang, X., "
    "Fukudo, S., Kellow, J., Okeke, E., Quigley, E. M. M., Schmulson, M., "
    "Whorwell, P., Archampong, T., Adibi, P., Andresen, V., Benninga, "
    "M. A., \u2026 Palsson, O. S. (2021). Worldwide prevalence and burden "
    "of functional gastrointestinal disorders, results of Rome Foundation "
    "Global Study. Gastroenterology, 160(1), 99\u2013114.e3. "
    "https://doi.org/10.1053/j.gastro.2020.04.014",

    "Stanford Health Care. (2026). Patient forms \u2013 Neuropsychology "
    "Clinic. Retrieved March 18, 2026, from "
    "https://stanfordhealthcare.org/medical-clinics/neuropsychology-clinic/"
    "what-to-expect/patient-forms.html",

    "Staudacher, H. M., Black, C. J., Teasdale, S. B., Mikocka-Walus, A., & "
    "Keefer, L. (2023). Irritable bowel syndrome and mental health "
    "comorbidity\u2014Approach to multidisciplinary management. Nature "
    "Reviews Gastroenterology & Hepatology, 20(9), 582\u2013596. "
    "https://doi.org/10.1038/s41575-023-00794-z",

    "Thirunavukarasu, A. J., Ting, D. S. J., Elangovan, K., Gutierrez, L., "
    "Tan, T. F., & Ting, D. S. W. (2023). Large language models in "
    "medicine. Nature Medicine, 29(8), 1930\u20131940. "
    "https://doi.org/10.1038/s41591-023-02448-8",

    "Tu, Q., Heitkemper, M. M., Jarrett, M. E., & Buchanan, D. T. (2017). "
    "Sleep disturbances in irritable bowel syndrome: A systematic review. "
    "Neurogastroenterology & Motility, 29(3), e12946. "
    "https://doi.org/10.1111/nmo.12946",

    "Wong, B. (2011). Points of view: Color blindness. Nature Methods, "
    "8(6), 441. https://doi.org/10.1038/nmeth.1618",

    "Zigmond, A. S., & Snaith, R. P. (1983). The Hospital Anxiety and "
    "Depression Scale. Acta Psychiatrica Scandinavica, 67(6), 361\u2013370. "
    "https://doi.org/10.1111/j.1600-0447.1983.tb09716.x",
]


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

TABLE_1_HEADER = ["Measure", "IBS (n = 65)", "HC (n = 40)", "t / \u03c7\u00b2", "Cohen's d"]
TABLE_1_SUBHEADER = ["", "M (SD)", "M (SD)", "", ""]

TABLE_1_ROWS = [
    ("__SECTION__", "Demographics"),
    ("Age (years)", "37.8 (11.4)", "35.6 (12.5)", "0.90", "0.19"),
    ("Education (years)\u1d43", "15.8 (1.9)", "16.4 (1.4)", "\u22121.54", "\u22120.31"),
    ("Female (%)", "78.5", "67.5", "1.04\u2020", "\u2014"),
    ("__SECTION__", "Sleep\u1d47"),
    ("BIS total (0\u201342)", "17.6 (7.6)", "10.3 (6.9)", "4.89***", "0.99"),
    ("__SECTION__", "Attention (CPT-3 T-scores)\u1d9c"),
    ("Detectability (d\u2032)", "48.9 (7.8)", "44.3 (7.1)", "3.00**", "0.60"),
    ("Omissions", "47.4 (6.4)", "45.0 (1.6)", "2.79**", "0.45"),
    ("Commissions", "51.0 (9.1)", "48.0 (8.1)", "1.70", "0.34"),
    ("HRT", "48.4 (8.0)", "48.7 (8.8)", "\u22120.18", "\u22120.04"),
    ("__SECTION__", "Fatigue\u1d48"),
    ("Chalder total (0\u201311)", "6.4 (3.4)", "1.6 (2.5)", "7.37***", "1.55"),
    ("__SECTION__", "Emotional distress (HADS)\u1d49"),
    ("Anxiety (0\u201321)", "8.1 (4.2)", "4.2 (3.3)", "4.97***", "1.00"),
    ("Depression (0\u201321)", "4.7 (3.1)", "2.1 (2.3)", "4.52***", "0.90"),
    ("__SECTION__", "Neurocognition (RBANS index scores)\u1d9c"),
    ("Immediate Memory", "89.6 (16.1)", "98.3 (15.7)", "\u22122.65**", "\u22120.54"),
    ("Visuospatial", "94.0 (11.7)", "94.6 (12.4)", "\u22120.24", "\u22120.05"),
    ("Language", "98.2 (14.1)", "100.9 (13.9)", "\u22120.97", "\u22120.20"),
    ("Attention", "92.5 (12.2)", "100.0 (18.3)", "\u22122.22*", "\u22120.51"),
    ("Delayed Memory", "93.2 (15.0)", "101.8 (19.8)", "\u22122.30*", "\u22120.51"),
    ("Total Scale", "90.5 (13.2)", "99.2 (12.9)", "\u22123.25**", "\u22120.67"),
]

TABLE_1_NOTE = (
    "Note. \u2020\u03c7\u00b2 test for gender; all others are "
    "independent-samples Welch's t-tests. *p < .05; **p < .01; ***p < .001. "
    "Sample sizes vary by measure due to missing data: \u1d43HC n = 28; "
    "\u1d47IBS n = 58, HC n = 39; \u1d9cHC n = 37; \u1d48IBS n = 49, HC n = 35; "
    "\u1d49IBS n = 57, HC n = 36. Negative d values indicate IBS < HC. "
    "BIS = Bergen Insomnia Scale; CPT-3 = Conners' Continuous Performance "
    "Test, 3rd edition; HRT = Hit Reaction Time; HADS = Hospital Anxiety "
    "and Depression Scale; RBANS = Repeatable Battery for the Assessment "
    "of Neuropsychological Status."
)

TABLE_2_HEADER = ["Step", "Case 1: Focal sleep problems",
                   "Case 2: Multi-domain involvement"]

TABLE_2_ROWS = [
    ("1. Context",
     "Male, 38 yrs, 12 yrs education, IBS-D, moderate IBS severity.",
     "Female, 31 yrs, 16 yrs education, IBS-M, high IBS severity."),
    ("2. Sleep",
     "BIS = 16 (Moderate; 59th cohort percentile). Clinically elevated, with "
     "four items endorsed at \u2265 3 days/week.",
     "BIS = 32 (98th cohort percentile). Severe insomnia and highly elevated "
     "sleep-domain burden."),
    ("3. Fatigue",
     "Chalder = 3 (below caseness threshold). No fatigue flag.",
     "Chalder = 11 (97th cohort percentile). Maximum fatigue caseness."),
    ("4. Mood",
     "HADS-A = 2 and HADS-D = 2 (both Normal). Emotional distress not flagged.",
     "HADS-A = 12 (clinical range), HADS-D = 6 (Normal). Anxiety flagged "
     "without depressive caseness."),
    ("5. Attention",
     "CPT-3 Detectability T = 60 (mildly elevated), with remaining CPT "
     "metrics within normal limits.",
     "CPT-3 profile within expected range; sustained attention remained "
     "comparatively preserved."),
    ("6. Cognition",
     "RBANS Sum Raw = 233 (57th cohort percentile). Broadly mid-range "
     "profile; Word List approached the lower boundary of normal range.\u1d43",
     "RBANS Sum Raw = 213 (15th cohort percentile). Marked relative weakness "
     "in Language, with additional weakness in Immediate Memory, Delayed "
     "Memory, and Recognition.\u1d43"),
    ("7. Integration",
     "Flags span sleep and attention, supporting an interacting symptom "
     "pattern with potential sleep-related attentional inefficiency.",
     "Sleep, fatigue, anxiety, and cognition form a multi-domain pattern. "
     "The pipeline links insomnia and fatigue, notes the bidirectional "
     "mood-sleep relationship, and identifies anxiety as a contributor to "
     "cognitive inefficiency."),
    ("8. Prognosis",
     "Prognosis depends mainly on whether the flagged domains respond to "
     "targeted follow-up.",
     "Mood and cognitive inefficiency co-occur, so emotional stabilization "
     "may improve concentration and reduce apparent cognitive burden."),
]

TABLE_2_NOTE = (
    "Note. \u1d43RBANS scores are cohort-relative rather than "
    "population-normed. BIS = Bergen Insomnia Scale; CPT-3 = Conners' "
    "Continuous Performance Test, 3rd edition; HADS = Hospital Anxiety and "
    "Depression Scale; HADS-A = HADS Anxiety subscale; HADS-D = HADS "
    "Depression subscale; IBS = irritable bowel syndrome; IBS-D = "
    "diarrhea-predominant IBS; IBS-M = mixed IBS; RBANS = Repeatable "
    "Battery for the Assessment of Neuropsychological Status."
)

TABLE_3_HEADER = ["Audience", "Multi-panel figure", "Radar plot"]
TABLE_3_ROWS = [
    ("Clinical peers",
     "Full statistical detail: z-scores, percentiles, effect sizes, "
     "confidence intervals. Technical labels.",
     "Expanded 10-spoke version with Cohen's d inset."),
    ("Referring physicians",
     "Traffic-light color coding (OK/Monitor/Action). Brief annotations for "
     "clinical triage.",
     "Compact 5-spoke version. Traffic-light vertex coloring."),
    ("Patients & families",
     "Accessible infographic. Plain-language labels, qualitative anchors, "
     "warm palette, no raw scores.",
     "Compact 5 spokes with qualitative anchors and interpretation sentence."),
]

TABLE_3_NOTE = "Note. All variants display the same underlying data."


# ---------------------------------------------------------------------------
# Figure legends
# ---------------------------------------------------------------------------

FIGURE_LEGENDS = [
    ("Figure 1.",
     "Eight-step clinical reasoning chain. Step 1 provides demographic and "
     "clinical context. Steps 2\u20136 assess five domains independently "
     "(parallel). Step 7 integrates findings across domains, identifying "
     "co-occurring patterns. Step 8 produces the prognostic formulation."),

    ("Figure 2.",
     "Multi-panel domain profile (clinical version) for Case 1. Each panel "
     "shows the cohort distribution (violin plots split by IBS/HC group) "
     "with the patient's score marked as a blue diamond. Panel 1 (BIS): "
     "Insomnia total with clinical threshold. Panel 2 (CPT): Attention "
     "metrics with software-generated T-scores. Panel 3 (Chalder): Fatigue "
     "with caseness threshold. Panel 4 (HADS): Anxiety and Depression with "
     "classification zones. Panel 5 (RBANS): Raw-subtest-derived summary "
     "composites and cohort-relative position."),

    ("Figure 3.",
     "Audience-tailored radar plots for Case 1. All three variants display "
     "the same underlying data on a normalized percentile-of-wellness scale "
     "(higher = better), but differ in level of detail and visual language. "
     "(a) The clinical version uses an expanded 10-spoke layout with "
     "z-score annotations and a Cohen's d inset. (b) The physician version "
     "uses a compact 5-spoke layout with traffic-light coloring. (c) The "
     "patient version uses plain-language labels, qualitative anchors, and "
     "a warm palette with an interpretive sentence."),

    ("Figure 4.",
     "Multi-panel domain profile (clinical version) for Case 2. The "
     "pipeline output shows severe sleep disturbance, marked fatigue, "
     "clinically elevated anxiety, preserved CPT performance, and "
     "cohort-relative RBANS weakness concentrated in language and "
     "memory-related domains. As in Figure 2, each panel plots the "
     "patient's score against the cohort distribution."),

    ("Figure 5.",
     "Audience-tailored radar plots for Case 2. Across all three audience "
     "versions, the output depicts a more globally compromised profile "
     "than Case 1, driven by severe insomnia, maximal fatigue caseness, "
     "anxiety elevation, and cohort-relative cognitive weakness, while "
     "sustained attention remains comparatively preserved."),
]


# ---------------------------------------------------------------------------
# Document construction helpers
# ---------------------------------------------------------------------------

def add_indented_paragraph(doc, text):
    return add_para(doc, text, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                    first_line_indent=Cm(1.27))


def add_indented_paragraphs(doc, paragraphs):
    for t in paragraphs:
        if t.startswith("[INSERT"):
            add_para(doc, t, alignment=WD_ALIGN_PARAGRAPH.CENTER, bold=True,
                     space_before=Pt(12), space_after=Pt(12))
        else:
            add_indented_paragraph(doc, t)


def add_numbered_bullet_para(doc, lead_bold, body, *, number=None, marker_style="bullet"):
    p = doc.add_paragraph()
    _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.LEFT, line_spacing=LINE_SPACING,
                      first_line_indent=Cm(1.27))
    if marker_style == "number":
        prefix = f"{number}. "
    else:
        prefix = "\u2022 "
    run0 = p.add_run(prefix)
    _apply_default_font(run0, bold=False)
    run1 = p.add_run(lead_bold)
    _apply_default_font(run1, bold=True)
    run2 = p.add_run(body)
    _apply_default_font(run2)
    return p


def add_table_caption(doc, label, caption):
    p = doc.add_paragraph()
    _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.LEFT, line_spacing=1.15,
                      space_after=Pt(6), keep_with_next=True)
    r1 = p.add_run(f"{label}\n")
    _apply_default_font(r1, bold=True)
    r2 = p.add_run(caption)
    _apply_default_font(r2, italic=True)


def make_table(doc, headers, rows, *, note=None, col_widths_cm=None,
               subheader=None, full_width_section_label=False):
    n_cols = len(headers)
    table = doc.add_table(rows=1, cols=n_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Light Grid Accent 1"
    table.autofit = True

    # Header row
    hdr_cells = table.rows[0].cells
    for cell, header in zip(hdr_cells, headers):
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.CENTER, line_spacing=1.15,
                          space_after=Pt(0))
        run = p.add_run(header)
        _apply_default_font(run, bold=True)

    # Optional subheader row
    if subheader:
        sub_row = table.add_row().cells
        for cell, val in zip(sub_row, subheader):
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                              line_spacing=1.15, space_after=Pt(0))
            run = p.add_run(val)
            _apply_default_font(run, italic=True)

    # Data rows
    for row in rows:
        if isinstance(row, tuple) and len(row) == 2 and row[0] == "__SECTION__":
            r = table.add_row().cells
            # merge cells
            merged = r[0]
            for c in r[1:]:
                merged = merged.merge(c)
            p = merged.paragraphs[0]
            _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                              line_spacing=1.15, space_after=Pt(0))
            run = p.add_run(row[1])
            _apply_default_font(run, italic=True, bold=True)
        else:
            cells = table.add_row().cells
            for i, val in enumerate(row):
                cell = cells[i]
                p = cell.paragraphs[0]
                align = WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.CENTER
                _format_paragraph(p, alignment=align, line_spacing=1.15,
                                  space_after=Pt(0))
                run = p.add_run(val)
                _apply_default_font(run)

    if note:
        p = doc.add_paragraph()
        _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                          line_spacing=1.15, space_before=Pt(4),
                          space_after=Pt(0))
        run = p.add_run(note)
        _apply_default_font(run, italic=True, size=Pt(11))


def figure_to_png(pdf_path, png_path, *, density=300):
    """Convert PDF page to PNG using ImageMagick (idempotent)."""
    import subprocess
    if png_path.exists() and png_path.stat().st_mtime >= pdf_path.stat().st_mtime:
        return
    png_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["magick", "-density", str(density), str(pdf_path),
         "-background", "white", "-alpha", "remove", "-alpha", "off",
         "-colorspace", "sRGB", "-quality", "92", str(png_path)],
        check=True,
    )


def add_full_page_figure(doc, label, png_path, max_width_cm=15.5):
    """Add a centered figure on its own page with 'Figure n' caption."""
    p = doc.add_paragraph()
    _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.CENTER, line_spacing=LINE_SPACING)
    run = p.add_run()
    run.add_picture(str(png_path), width=Cm(max_width_cm))
    _apply_default_font(run)
    cap = doc.add_paragraph()
    _format_paragraph(cap, alignment=WD_ALIGN_PARAGRAPH.CENTER, line_spacing=1.15,
                      space_before=Pt(6))
    cr = cap.add_run(label)
    _apply_default_font(cr, bold=True)


# ---------------------------------------------------------------------------
# Build the document
# ---------------------------------------------------------------------------

def build():
    doc = Document()

    # --- Document-wide defaults ---
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
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.space_before = Pt(0)

    # Page setup: A4-ish with 2.5 cm margins on a single section
    section = doc.sections[0]
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    # Running head + page numbers from the start
    set_running_head(section, header_text=RUNNING_HEAD)
    set_page_number_footer(section)

    # Line numbering will be enabled on the manuscript-body section later.

    # ---------------- TITLE PAGE ----------------
    add_para(doc, RUNNING_HEAD, alignment=WD_ALIGN_PARAGRAPH.RIGHT,
             italic=True, line_spacing=1.0, space_after=Pt(12))

    add_para(doc, TITLE, bold=True, alignment=WD_ALIGN_PARAGRAPH.CENTER,
             space_before=Pt(24), space_after=Pt(18))

    # Authors (one paragraph with superscripts)
    p_auth = doc.add_paragraph()
    _format_paragraph(p_auth, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                      space_after=Pt(12))
    for i, (name, sup) in enumerate(AUTHORS):
        if i:
            sep_run = p_auth.add_run(", ")
            _apply_default_font(sep_run)
        name_run = p_auth.add_run(name)
        _apply_default_font(name_run)
        sup_run = p_auth.add_run(sup)
        _apply_default_font(sup_run)
        sup_run.font.superscript = True

    # Affiliations (one per line)
    for letter, aff in AFFILIATIONS:
        p = doc.add_paragraph()
        _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                          line_spacing=LINE_SPACING)
        sup = p.add_run(letter)
        _apply_default_font(sup)
        sup.font.superscript = True
        run = p.add_run(" " + aff)
        _apply_default_font(run)

    add_para(doc, "", space_before=Pt(12))

    # Corresponding author
    add_para(doc, "Corresponding author:", bold=True,
             alignment=WD_ALIGN_PARAGRAPH.LEFT, space_before=Pt(6),
             space_after=Pt(0))
    add_para(doc, CORRESPONDING_AUTHOR["name"], alignment=WD_ALIGN_PARAGRAPH.LEFT)
    add_para(doc, CORRESPONDING_AUTHOR["address"], alignment=WD_ALIGN_PARAGRAPH.LEFT)
    add_para(doc, "Email: " + CORRESPONDING_AUTHOR["email"],
             alignment=WD_ALIGN_PARAGRAPH.LEFT, space_after=Pt(12))

    # ORCID
    add_para(doc, "ORCID iDs:", bold=True, alignment=WD_ALIGN_PARAGRAPH.LEFT,
             space_before=Pt(6), space_after=Pt(0))
    for name, oid in ORCIDS:
        add_para(doc, f"{name}: https://orcid.org/{oid}",
                 alignment=WD_ALIGN_PARAGRAPH.LEFT)

    add_para(doc, "", space_before=Pt(12))

    # Word counts
    abstract_word_count = sum(
        len(t.split()) for t in [ABSTRACT_OBJECTIVE, ABSTRACT_METHOD,
                                  ABSTRACT_RESULTS, ABSTRACT_CONCLUSIONS]
    )
    # body_word_count computed after body building; we'll patch below.
    add_para(doc, f"Abstract word count: {abstract_word_count}",
             alignment=WD_ALIGN_PARAGRAPH.LEFT, space_before=Pt(12))
    p_word = add_para(doc, "Manuscript word count (excluding title page, "
                            "abstract, references, tables, and figures): "
                            "[INSERT BODY WORD COUNT]",
                       alignment=WD_ALIGN_PARAGRAPH.LEFT)

    add_page_break(doc)

    # ---------------- ABSTRACT (page 2) ----------------
    add_heading_apa(doc, "Abstract")

    abstract_blocks = [
        ("Objective. ", ABSTRACT_OBJECTIVE),
        ("Method. ", ABSTRACT_METHOD),
        ("Results. ", ABSTRACT_RESULTS),
        ("Conclusions. ", ABSTRACT_CONCLUSIONS),
    ]
    for label, body in abstract_blocks:
        p = doc.add_paragraph()
        _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                          line_spacing=LINE_SPACING, space_after=Pt(6))
        rl = p.add_run(label)
        _apply_default_font(rl, bold=True)
        rb = p.add_run(body)
        _apply_default_font(rb)

    # Keywords
    add_para(doc, "")
    p_kw = doc.add_paragraph()
    _format_paragraph(p_kw, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                      line_spacing=LINE_SPACING, space_before=Pt(6))
    kr = p_kw.add_run("Keywords: ")
    _apply_default_font(kr, bold=True)
    kr2 = p_kw.add_run("; ".join(KEYWORDS))
    _apply_default_font(kr2)

    add_page_break(doc)

    # ---------------- STATEMENT OF RESEARCH SIGNIFICANCE (page 3) ----------------
    add_heading_apa(doc, "Statement of Research Significance")

    for label, body in [
        ("Research Question(s) or Topic(s): ", SRS_RESEARCH_QUESTION),
        ("Main Findings: ", SRS_MAIN_FINDINGS),
        ("Study Contributions: ", SRS_STUDY_CONTRIBUTIONS),
    ]:
        p = doc.add_paragraph()
        _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                          line_spacing=LINE_SPACING, space_after=Pt(6))
        rl = p.add_run(label.rstrip())
        _apply_default_font(rl, underline=True, bold=True)
        rspace = p.add_run(" ")
        _apply_default_font(rspace)
        rb = p.add_run(body)
        _apply_default_font(rb)

    srs_word_count = sum(
        len(t.split()) for t in [SRS_RESEARCH_QUESTION, SRS_MAIN_FINDINGS,
                                  SRS_STUDY_CONTRIBUTIONS]
    )
    print(f"Statement of Research Significance: {srs_word_count} words")

    add_page_break(doc)

    # ---------------- BODY (page 4 onward) ----------------
    # Add a NEW section break so we can enable line numbering only here.
    new_section = doc.add_section(WD_SECTION_START.NEW_PAGE)
    new_section.page_height = Cm(29.7)
    new_section.page_width = Cm(21.0)
    new_section.top_margin = Cm(2.5)
    new_section.bottom_margin = Cm(2.5)
    new_section.left_margin = Cm(2.5)
    new_section.right_margin = Cm(2.5)
    set_running_head(new_section, header_text=RUNNING_HEAD)
    set_page_number_footer(new_section)
    enable_line_numbering(new_section, start=1)

    body_word_count_marker_start = sum(len(p.text.split()) for p in doc.paragraphs)

    # ---- INTRODUCTION ----
    add_heading_apa(doc, "Introduction")
    add_indented_paragraphs(doc, INTRODUCTION)

    # ---- METHOD ----
    add_heading_apa(doc, "Method")

    add_heading_apa(doc, "Participants", level=2)
    add_indented_paragraphs(doc, PARTICIPANTS_PARAS)

    add_heading_apa(doc, "Neuropsychological Instruments", level=2)
    add_indented_paragraphs(doc, INSTRUMENTS_PARAS)

    for i, (lead, body) in enumerate(INSTRUMENT_LIST, start=1):
        add_numbered_bullet_para(doc, lead, body, number=i, marker_style="number")
    add_indented_paragraph(doc, INSTRUMENTS_TAIL)

    add_heading_apa(doc, "The Deterministic Pipeline", level=2)
    add_heading_apa(doc, "Architecture overview", level=3)
    add_indented_paragraphs(doc, PIPELINE_OVERVIEW)
    add_runs_para(
        doc,
        [("Clarification on the role of AI. ", {"bold": True, "italic": True}),
         (CLARIFICATION_AI, {})],
        alignment=WD_ALIGN_PARAGRAPH.LEFT,
        first_line_indent=Cm(1.27),
    )
    add_indented_paragraph(doc, PIPELINE_STAGES_INTRO)
    roman = ["(i)", "(ii)", "(iii)", "(iv)", "(v)"]
    for i, (lead, body) in enumerate(PIPELINE_STAGES):
        add_numbered_bullet_para(doc, lead, body, number=roman[i],
                                 marker_style="number")

    add_para(doc, INSERT_FIGURE_1, alignment=WD_ALIGN_PARAGRAPH.CENTER, bold=True,
             space_before=Pt(12), space_after=Pt(12))

    add_heading_apa(doc, "Audience-tailored output design", level=3)
    add_indented_paragraphs(doc, AUDIENCE_DESIGN_PARAS)
    for lead, body in AUDIENCE_BULLETS:
        add_numbered_bullet_para(doc, lead, body, marker_style="bullet")
    add_indented_paragraph(doc, AUDIENCE_TAIL)

    add_heading_apa(doc, "Recommendation engine", level=3)
    add_indented_paragraphs(doc, RECOMMENDATIONS_PARAS)

    add_heading_apa(doc, "Computational reproducibility", level=3)
    add_indented_paragraphs(doc, REPRO_PARAS)

    add_heading_apa(doc, "Statistical Analysis", level=2)
    add_heading_apa(doc, "Cohort-level group comparisons", level=3)
    add_indented_paragraphs(doc, STATS_GROUP_PARAS)
    add_heading_apa(doc, "Pipeline output evaluation", level=3)
    add_indented_paragraphs(doc, STATS_PIPELINE_EVAL)

    # ---- RESULTS ----
    add_heading_apa(doc, "Results")

    add_heading_apa(doc, "Cohort Characteristics", level=2)
    add_indented_paragraphs(doc, RESULTS_COHORT)

    add_heading_apa(doc, "Group Differences Across Domains", level=2)
    add_indented_paragraphs(doc, RESULTS_GROUP_DIFF)

    add_heading_apa(doc, "Pipeline Output Summary", level=2)
    add_indented_paragraphs(doc, RESULTS_PIPELINE_OUTPUT)

    add_heading_apa(doc, "Distribution of clinical findings", level=3)
    add_indented_paragraph(doc, RESULTS_DISTRIBUTION_INTRO)
    for lead, body in RESULTS_DISTRIBUTION_BULLETS:
        add_numbered_bullet_para(doc, lead, body, marker_style="bullet")
    add_indented_paragraph(doc, RESULTS_DISTRIBUTION_TAIL)

    add_heading_apa(doc, "Case Illustrations", level=2)
    add_indented_paragraphs(doc, CASE_INTRO)

    add_heading_apa(doc, "Case 1: IBS patient with circumscribed sleep disturbance", level=3)
    add_indented_paragraph(doc, CASE_1["intro"])
    add_runs_para(doc, [(CASE_1["pipeline_lead"], {"bold": True, "italic": True}),
                        (CASE_1["pipeline_body"], {})],
                  alignment=WD_ALIGN_PARAGRAPH.LEFT, first_line_indent=Cm(1.27))
    add_indented_paragraph(doc, CASE_1["figures_para"])
    for callout in CASE_1["figure_callouts"]:
        add_para(doc, callout, alignment=WD_ALIGN_PARAGRAPH.CENTER, bold=True,
                 space_before=Pt(6), space_after=Pt(6))
    add_runs_para(doc, [(CASE_1["interp_lead"], {"bold": True, "italic": True}),
                        (CASE_1["interp_body"], {})],
                  alignment=WD_ALIGN_PARAGRAPH.LEFT, first_line_indent=Cm(1.27))

    add_heading_apa(doc, "Case 2: IBS patient with multi-domain involvement", level=3)
    add_indented_paragraph(doc, CASE_2["intro"])
    add_runs_para(doc, [(CASE_2["pipeline_lead"], {"bold": True, "italic": True}),
                        (CASE_2["pipeline_body"], {})],
                  alignment=WD_ALIGN_PARAGRAPH.LEFT, first_line_indent=Cm(1.27))
    add_indented_paragraph(doc, CASE_2["figures_para"])
    for callout in CASE_2["figure_callouts"]:
        add_para(doc, callout, alignment=WD_ALIGN_PARAGRAPH.CENTER, bold=True,
                 space_before=Pt(6), space_after=Pt(6))
    add_runs_para(doc, [(CASE_2["interp_lead"], {"bold": True, "italic": True}),
                        (CASE_2["interp_body"], {})],
                  alignment=WD_ALIGN_PARAGRAPH.LEFT, first_line_indent=Cm(1.27))

    # ---- DISCUSSION ----
    add_heading_apa(doc, "Discussion")
    add_heading_apa(doc, "Summary of findings", level=2)
    add_indented_paragraphs(doc, DISCUSSION_SUMMARY)
    add_heading_apa(doc, "Relation to prior work", level=2)
    add_indented_paragraphs(doc, DISCUSSION_PRIOR)
    add_heading_apa(doc, "Clinical implications", level=2)
    add_indented_paragraphs(doc, DISCUSSION_CLINICAL)
    add_heading_apa(doc, "Limitations", level=2)
    add_indented_paragraphs(doc, DISCUSSION_LIMITATIONS)
    add_heading_apa(doc, "Future directions", level=2)
    add_indented_paragraphs(doc, DISCUSSION_FUTURE)

    add_heading_apa(doc, "Conclusions")
    add_indented_paragraphs(doc, CONCLUSIONS)

    body_word_count_marker_end = sum(len(p.text.split()) for p in doc.paragraphs)
    body_word_count = body_word_count_marker_end - body_word_count_marker_start

    # ---- ACKNOWLEDGEMENTS ----
    add_heading_apa(doc, "Acknowledgements")
    add_indented_paragraph(
        doc,
        "The authors thank the participants in the Bergen "
        "Brain\u2013Gut\u2013Microbiota study for their contributions. The "
        "pipeline was developed using open-source Python tools and "
        "LaTeX, and was co-authored with AI assistance (Claude Opus 4.7, "
        "Anthropic, accessed via the Cursor IDE [https://cursor.com], "
        "April 2026). The AI coding assistant contributed to writing the "
        "Python code, designing the clinical decision rules, authoring the "
        "narrative text templates, implementing the visualizations, and "
        "drafting portions of the manuscript text for language, clarity, "
        "and consistency. All AI-generated content was reviewed, verified, "
        "and edited by the authors. The deployed deterministic pipeline "
        "uses no AI models at runtime."
    )

    add_heading_apa(doc, "Competing Interests", level=2)
    add_indented_paragraph(doc, "The authors declare none.")

    add_heading_apa(doc, "Sources of Support", level=2)
    add_indented_paragraph(
        doc,
        "This work was supported by the University of Bergen. The original "
        "data collection (Bergen Brain\u2013Gut\u2013Microbiota project) was "
        "funded by the Research Council of Norway (grant ID FRIMED-BIO276010 "
        "and project number 294594), Helse Vest's Research Funding (grant ID "
        "HV912243), and the Trond Mohn Research Foundation (grant number "
        "BFS2018TMT0)."
    )

    # ---- DATA AVAILABILITY ----
    add_heading_apa(doc, "Data Availability Statement", level=2)
    add_indented_paragraph(
        doc,
        "The cohort dataset contains clinical neuropsychological data "
        "collected under ethics approval and is not publicly available due "
        "to participant confidentiality and ethics approval conditions. "
        "Data may be made available upon reasonable request to the "
        "corresponding author, subject to institutional data sharing "
        "agreements. The pipeline source code and anonymised example "
        "outputs are openly available at "
        "https://github.com/arvidl/AI-driven-neuropsych-screening. The "
        "complete audience-tailored reports for the two case illustrations "
        "are provided as Supplementary Material S2 and S3."
    )

    # ---- SUPPLEMENTARY MATERIAL POINTER ----
    add_heading_apa(doc, "Supplementary Material", level=2)
    add_indented_paragraph(
        doc,
        "The supplementary material for this article can be found at "
        "[update to provide the DOI here]. Supplementary Material S1 "
        "(supplementary_methods.pdf) contains the prompt-development and "
        "rule-specification materials, including the complete system "
        "prompt specification, the five assessment domains, visualization "
        "designs, audience-tailored output variants, and the structured "
        "JSON output format. S1 also provides a transparent account of "
        "AI's role in the project (development time vs. runtime), followed "
        "by the complete set of explicit decision rules. Supplementary "
        "Material S2 (case_1_report.pdf) provides the complete "
        "audience-tailored pipeline report for Case 1. Supplementary "
        "Material S3 (case_2_report.pdf) provides the corresponding report "
        "for Case 2."
    )

    # ---- REFERENCES (still on numbered/line-numbered section) ----
    add_heading_apa(doc, "References")
    for ref in REFERENCES:
        p = doc.add_paragraph()
        _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                          line_spacing=LINE_SPACING, space_after=Pt(6))
        # APA hanging indent: first line at 0, subsequent at 1.27 cm
        p.paragraph_format.left_indent = Cm(1.27)
        p.paragraph_format.first_line_indent = Cm(-1.27)
        run = p.add_run(ref)
        _apply_default_font(run)

    # ---- TABLES (turn off line numbering for the appendix-like back matter) ----
    tables_section = doc.add_section(WD_SECTION_START.NEW_PAGE)
    tables_section.page_height = Cm(29.7)
    tables_section.page_width = Cm(21.0)
    tables_section.top_margin = Cm(2.5)
    tables_section.bottom_margin = Cm(2.5)
    tables_section.left_margin = Cm(2.5)
    tables_section.right_margin = Cm(2.5)
    set_running_head(tables_section, header_text=RUNNING_HEAD)
    set_page_number_footer(tables_section)
    disable_line_numbering(tables_section)

    add_table_caption(
        doc, "Table 1.",
        "Cohort demographics and neuropsychological domain scores by group.")
    make_table(doc, TABLE_1_HEADER, TABLE_1_ROWS,
               note=TABLE_1_NOTE, subheader=TABLE_1_SUBHEADER)

    add_page_break(doc)

    add_table_caption(
        doc, "Table 2.",
        "Comparative summary of the pipeline's eight-step clinical reasoning "
        "across the two illustrative cases.")
    make_table(doc, TABLE_2_HEADER, TABLE_2_ROWS, note=TABLE_2_NOTE)

    add_page_break(doc)

    add_table_caption(
        doc, "Table 3.",
        "Audience-tailored output design: content and visualization "
        "specifications.")
    make_table(doc, TABLE_3_HEADER, TABLE_3_ROWS, note=TABLE_3_NOTE)

    add_page_break(doc)

    # ---- FIGURE LEGENDS (separate page) ----
    add_heading_apa(doc, "Figure Legends")
    for label, body in FIGURE_LEGENDS:
        p = doc.add_paragraph()
        _format_paragraph(p, alignment=WD_ALIGN_PARAGRAPH.LEFT,
                          line_spacing=LINE_SPACING, space_after=Pt(6))
        rl = p.add_run(f"{label} ")
        _apply_default_font(rl, bold=True)
        rb = p.add_run(body)
        _apply_default_font(rb)

    add_page_break(doc)

    # ---- FIGURES (each on its own page) ----
    figure_files = [
        ("Figure 1", FIGURES_DIR / "Figure_1_reasoning_chain.pdf"),
        ("Figure 2", FIGURES_DIR / "Figure_2_case1_multipanel.pdf"),
        ("Figure 3", FIGURES_DIR / "Figure_3_case1_radar.pdf"),
        ("Figure 4", FIGURES_DIR / "Figure_4_case2_multipanel.pdf"),
        ("Figure 5", FIGURES_DIR / "Figure_5_case2_radar.pdf"),
    ]

    png_dir = JINS_DIR / "_docx_figures"
    png_dir.mkdir(parents=True, exist_ok=True)

    for i, (label, pdf_path) in enumerate(figure_files):
        png_path = png_dir / (pdf_path.stem + ".png")
        figure_to_png(pdf_path, png_path, density=300)
        # Choose width: multi-panel figures (2 and 4) and radar trios (3 and 5)
        # benefit from wider; reasoning chain (1) is taller-ish, fit narrower.
        if i in (1, 3):  # multi-panel pages
            width = 16.0
        elif i in (2, 4):  # radar trios
            width = 16.0
        else:
            width = 14.0
        add_full_page_figure(doc, label, png_path, max_width_cm=width)
        if i < len(figure_files) - 1:
            add_page_break(doc)

    # ---- Patch in the final body word count ----
    for p in doc.paragraphs:
        if "[INSERT BODY WORD COUNT]" in p.text:
            for run in p.runs:
                if "[INSERT BODY WORD COUNT]" in run.text:
                    run.text = run.text.replace(
                        "[INSERT BODY WORD COUNT]", str(body_word_count))
            break

    # Save
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(f"Saved: {OUTPUT}")
    print(f"Abstract words: {abstract_word_count}")
    print(f"Body words (Introduction..Conclusions): {body_word_count}")


if __name__ == "__main__":
    build()
