# Cover Letter — Journal of the International Neuropsychological Society

**Date:** 2026-04-22

**To:** The Editor-in-Chief
Journal of the International Neuropsychological Society
Cambridge University Press

**Re:** Manuscript submission — *"An AI-Initiated, Rule-Based Pipeline for Pre-Examination Screening in Clinical Neuropsychology"*

---

Dear Editor,

We are pleased to submit the enclosed manuscript, *"An AI-Initiated, Rule-Based Pipeline for Pre-Examination Screening in Clinical Neuropsychology,"* for consideration as a **Research Article** in the *Journal of the International Neuropsychological Society*. The paper falls squarely within JINS' interest in methodological innovation and clinical decision support that strengthens, rather than displaces, neuropsychological judgment.

## Contribution

The manuscript presents a fully deterministic, rule-based pipeline that automates the synthesis of multi-domain pre-examination screening data into a structured clinical formulation, audience-tailored reports, and visual summaries. We demonstrate the framework on N = 105 adults (65 patients with irritable bowel syndrome, 40 healthy controls) from the Bergen Brain–Gut–Microbiota study, using five established instruments (Bergen Insomnia Scale, Conners' CPT-3, Chalder Fatigue Scale, HADS, and RBANS). The pipeline applies published cutoffs together with cohort-relative interpretive rules, performs cross-domain reasoning (e.g., insomnia–fatigue–attention cascades), and emits PDF reports adapted to clinical peers, referring physicians, and patients.

Two contrasting case illustrations show how the pipeline differentiates a circumscribed sleep-centered profile from a broader multi-domain involvement, while explicitly highlighting where clinician interpretation must extend the rule-based output. Because every classification, flag, reasoning step, and recommendation traces back to an explicit rule, the framework offers transparency, reproducibility, and auditability — properties we consider essential for clinical neuropsychology.

## Use of AI

In line with Cambridge University Press's policy on the declaration of AI tools, we note explicitly:

- The pipeline source code and parts of the manuscript text were **co-developed with AI coding assistants** (Anthropic Claude Opus 4.6 and OpenAI GPT-5.4, accessed via the Cursor IDE between February and April 2026).
- All AI-generated content was reviewed, verified, and edited by the authors.
- **No AI is used at runtime.** The deployed pipeline contains no LLM API calls, no AI client libraries, and no network dependencies. All clinical classifications and recommendations are produced by deterministic, rule-based logic operating on published cutoffs and pre-authored text templates.
- A full account of AI's role (development time vs. runtime), together with the complete prompt and rule specifications, is provided in Supplementary Material S1.

## Standard declarations

- The manuscript is original, has not been published previously, and is not under consideration elsewhere.
- All listed authors approved the submitted version and meet the authorship criteria of Cambridge University Press.
- The original Bergen Brain–Gut–Microbiota study was approved by the Regional Committee for Medical and Health Research Ethics, South East Norway (REK2015-01621); all participants provided written informed consent.
- **Competing interests:** The authors declare none.
- **Funding:** University of Bergen; Research Council of Norway (FRIMED-BIO276010, project 294594); Helse Vest's Research Funding (HV912243); Trond Mohn Research Foundation (BFS2018TMT0).
- **Data availability:** The cohort dataset is restricted by ethics approval and is not publicly available; the pipeline source code, an analysis-ready blinded subset, the two anonymised example reports, and notebooks reproducing the public subset of Table 1 are openly available at <https://github.com/arvidl/AI-driven-neuropsych-screening>.

## Files included

- Main manuscript (`AI_driven_neuropsych_screening_20260422_docx.docx`) — Word format for typesetting
- Compiled PDF of the LaTeX source (`jins_main.pdf`) — for review reference
- Five figure files (Figure 1–5) — separate high-resolution PDF/TIFF
- Supplementary Material S1 — `supplementary_methods.pdf` (prompt and rule specifications)
- Supplementary Material S2 — `case_1_report.pdf` (full audience-tailored report, Case 1)
- Supplementary Material S3 — `case_2_report.pdf` (full audience-tailored report, Case 2)

## Suggested reviewers

We respectfully suggest the following experts as potential reviewers, with no recent collaboration or conflict of interest with the authors:

1. *(reviewer name, affiliation, email)* — AI in neuropsychological practice
2. *(reviewer name, affiliation, email)* — clinical decision support / report writing
3. *(reviewer name, affiliation, email)* — IBS and cognition / gut–brain axis
4. *(reviewer name, affiliation, email)* — computerised cognitive assessment

We have no non-preferred reviewers to declare.

---

We thank you and the editorial team in advance for considering our work and look forward to the review process.

Sincerely,

**Astri J. Lundervold, PhD** *(corresponding author)*
Department of Clinical and Biological Psychology, University of Bergen
Christies gate 12, 5015 Bergen, Norway
Email: astri.lundervold@uib.no
ORCID: 0000-0002-6819-6164

on behalf of co-authors Birgitte Berentsen and Arvid Lundervold
