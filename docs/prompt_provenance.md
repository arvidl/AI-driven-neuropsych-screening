# Prompt Provenance — AI-Assisted Development of the Pipeline

This document records **how** the deterministic pipeline
(`scripts/neuropsych_pipeline.py`) was produced with AI assistance, and it
reproduces the design/system prompts that guided that process.

> **Governing principle.** Artificial intelligence was used **only during
> development, never at runtime**, and **no real or identifiable patient data
> were provided to any model at any point**. Development used the published
> instrument specifications and synthetic or fully de-identified example records.
> The deployed pipeline contains **no model, no AI client library, and no network
> calls** — see [`docs/rules.md`](rules.md) for the deterministic logic it runs.

The concrete, human-verified rules the pipeline implements are catalogued
separately in [`docs/rules.md`](rules.md).

---

## 1. Prompting strategy — an iterative, clinician-led sequence

Development followed a **"design brief → draft → review → correct"** loop led by
the clinical authors, not a single prompt. The main stages were:

1. **Problem framing and design brief.** The clinical authors specified the
   intended use (pre-examination screening decision support), the five instruments
   and their published cutoffs, the three target audiences, and the required
   structured (JSON) output. This brief — not the model — defined every clinical
   rule and threshold.
2. **Initial elicitation** (`ORIGINAL_PROMPT_20260207`, Claude Opus 4.6). An
   exploratory prompt drafted a first reasoning-and-reporting structure and
   surfaced candidate domain logic. Outputs were treated as drafts only.
3. **Specification and refactoring** (`UPDATED_PROMPT_20260316` and
   `SYSTEM_PROMPT_for_analysis` v1.1, GPT-5.4). After the analysis-ready cohort
   file was prepared, the design brief was formalized into a system-prompt
   specification, and the assistant was asked to (re)implement the pipeline
   against that specification.
4. **Rule extraction and source verification.** Each AI-proposed classification
   rule, cutoff, and cross-domain trigger was checked line-by-line against the
   cited source instrument (BIS, CPT-3, Chalder, HADS, RBANS) and corrected where
   the draft diverged. Cutoffs were locked to published values; the model was not
   permitted to "choose" thresholds.
5. **Visualization and audience tailoring.** Prompts iterated on the multi-panel
   and radar figures and on the three audience variants (clinical peers, referring
   physicians, patients/families), with the authors adjusting labels, polarity
   (higher = better), and the color-blind-safe palette.
6. **Report assembly and reproducibility.** Final prompts addressed deterministic
   report generation (LaTeX/PDF), removal of any runtime model/network dependency,
   and packaging for reproducible execution (`environment.yml`).

A recurring pattern across stages was **correction**: the assistant's drafts were
frequently edited or rejected (e.g., tightening a cutoff to the published value,
removing an over-confident causal claim, or re-labelling a "diagnosis" as a
flagged finding). The final rules reflect author decisions, not model defaults.

## 2. Human-in-the-loop review and invariants

The authors acted as human-in-the-loop reviewers throughout the design phase
(principally February–March 2026). Every AI-proposed rule, cutoff, narrative
template, and figure was **accepted, corrected, or rejected** by an author before
being incorporated. Two invariants were maintained:

1. No real or identifiable patient data were ever entered into the assistant.
2. The deployed pipeline contains no model, no AI client library, and no network
   calls, so AI cannot influence any patient-level output at runtime.

## 3. Model cards (development-time assistants)

Concise summaries of the assistant models **as used in this project**. These are
not a substitute for the providers' official documentation; adopters should
consult the current official model cards, because versions, capabilities, and
terms change over time. Facts below were checked against providers' official cards
and Cursor's data-governance documentation (accessed June 2026).

| Field | Model A | Model B |
|---|---|---|
| Provider / version | Anthropic Claude Opus 4.6 (`claude-opus-4-6`) | OpenAI GPT-5.4 (`gpt-5.4`) |
| Access | via Cursor IDE; enterprise privacy/zero-retention (training disabled) | via Cursor IDE; enterprise privacy/zero-retention (training disabled) |
| Role in project | Initial elicitation of reasoning/reporting structure and candidate domain logic | Formalizing the system prompt and (re)implementing the pipeline |
| Inputs provided | Published instrument specs; design briefs; synthetic/de-identified examples; project source | Published instrument specs; formal system prompt; synthetic/de-identified examples; project source |
| Inputs **not** provided | No real/identifiable patient data; no cohort records | No real/identifiable patient data; no cohort records |
| Determinism | Generative, non-deterministic; outputs treated as drafts and verified | Generative, non-deterministic; outputs treated as drafts and verified |
| Runtime role | **None** (no model in the deployed pipeline) | **None** (no model in the deployed pipeline) |
| Limitations | May hallucinate; not a medical device; not for autonomous clinical use | May hallucinate; not a medical device; not for autonomous clinical use |

Provider documentation (accessed June 2026):
- [a] Anthropic, "Claude Opus 4.6" system card — https://www.anthropic.com/news/claude-opus-4-6
- [b] OpenAI, "GPT-5.4 Thinking System Card" — https://openai.com/index/gpt-5-4-thinking-system-card/
- [c] Cursor, "Privacy and Data Governance" — https://cursor.com/docs/enterprise/privacy-and-data-governance

---

## 4. Rendered project material (verbatim prompts)

Final pipeline produced with **Cursor 2.6.20 / GPT-5.4** on 2026-03-17. The prompts
below are the primary record of the AI-assisted design.

### 4a. Original prompt — `ORIGINAL_PROMPT_20260207` (Claude Opus 4.6)

> Can you improve and refine this to be a better prompt:
>
> You are an AI-based clinical neuropsychologist, exposed to a cohort of 105
> subjects — some with IBS, some without IBS. You are an expert in
> neuropsychological reasoning and interpretation of neuropsychological test
> profiles in multiple domains: cognition, emotion, sleep, distress, etc. (cf.
> BIS, CPT, FSS / Chalder, HADS, RBANS) related to patient demographics (e.g.,
> Gender, Age, Education). The information you extract for each patient is
> actionable in terms of therapy advice, and the need or suggestion of further
> examinations. You are able to see the patient in context (cf. the cohort of 105
> subjects). You also provide your output in JSON format containing information
> about findings within the different domains, your reasoning steps, and your
> conclusions. You also provide a didactic diagram with domain-specific profiles
> (cf. BIS, CPT, FSS, HADS, RBANS) explaining the findings and empirical
> conclusions to your peers, to medical doctors, and to the patient and their
> closest persons.

### 4b. Updated prompt — `UPDATED_PROMPT_20260316` (GPT-5.4)

> I have now made an updated csv file
> (`data/BGA_merged_all_20260208_cleaned_for_analysis.csv`) and an updated Markdown
> file for the system prompt (`doc/SYSTEM_PROMPT_for_analysis.md`) for updating our
> automated pipeline (`neuropsych_pipeline.py`) used to generate comprehensive,
> audience-tailored neuropsychological reports from multi-domain test data. Can you
> suggest the updated Python pipeline in `scripts/neuropsych_pipeline_20260316.py`
> accordingly?

### 4c. System prompt for analysis — v1.1 (2026-03-16, GPT-5.4)

**Role.** An AI-based clinical neuropsychologist specializing in the
interpretation of neuropsychological test profiles, with access to a cohort
dataset of 105 subjects (IBS patients and healthy controls).

**Expertise / instruments.**
- Sleep / Insomnia: Bergen Insomnia Scale (BIS)
- Sustained attention / Executive function: Continuous Performance Test (CPT)
- Fatigue: Chalder Fatigue Scale (11 items, bimodal scoring 0–11)
- Emotional distress: Hospital Anxiety and Depression Scale (HADS)
- Neurocognitive function: RBANS
- Contextual variables: Gender, Age, Education, IBS status

**Tasks.**
1. **Profile interpretation** — patterns, elevations, deficits relative to norms
   and the cohort distribution.
2. **Contextual reasoning** — situate the profile within the full cohort (N=105)
   and demographic subgroups.
3. **Clinical reasoning chain** — step-by-step reasoning linking test patterns to
   plausible mechanisms (e.g., insomnia–fatigue–attention cascades, anxiety–sleep–
   cognition interactions, gut–brain-axis effects).
4. **Actionable recommendations** — therapy-relevant advice and suggestions for
   further examinations/referrals.
5. **Patient-specific graphical output** — a multi-panel domain-profile figure and
   a radar/spider plot, each in three audience variants, incorporating cohort
   context (Python + seaborn/matplotlib).

**Visualization A — multi-panel domain-profile figure.** Per domain (BIS, CPT,
Chalder, HADS, RBANS): a cohort-context layer (violin/strip/KDE split by IBS
status; normative/clinical cutoff lines; shaded normal/borderline/clinical zones)
plus an overlaid individual-patient layer (prominent marker + percentile rank), with
subscale breakdowns where relevant (HADS-A/HADS-D; the RBANS subtests; the CPT
metrics).

**Visualization B — radar/spider plot.** One radial axis per domain (compact
5-spoke or expanded up-to-10-spoke). **Normalize all scores to a common 0–100
percentile-of-wellness scale within the cohort, with consistent polarity
(higher = better)**, inverting instruments where high raw scores mean worse
outcomes (BIS, Chalder, HADS, CPT). Layers: healthy zone, IBS cohort median,
clinical-concern zone, and the individual patient polygon with per-vertex
percentile labels and plain-language axis descriptors.

**Audience tailoring (both figures).**
- **Clinical peers:** full statistical detail (z-scores, percentiles, effect
  sizes); technical labels; expanded radar.
- **Referring physicians:** simplified traffic-light (green/amber/red) summary;
  brief action points; compact radar.
- **Patients / close persons:** accessible infographic style; plain language;
  qualitative anchors; warm, non-alarming palette; compact radar.

**Structured JSON output** with keys: `patient_id`, `demographics`,
`domain_findings` (per-domain `scores` / `percentile_in_cohort` / `interpretation`
/ `flags`), `cross_domain_patterns`, `cohort_context`, `reasoning_chain`,
`recommendations` (`therapeutic`, `further_examinations`), and
`visualizations_generated`. (See any tracked `output_subj/<id>/<id>_report.json`
for the realized structure.)

**Guiding principles.** Ground interpretations in established norms; distinguish
statistical from clinical significance; be transparent about uncertainty and
cross-sectional limitations; tailor language/detail per audience; keep
visualizations colorblind-safe; in the radar plot always normalize to a common
percentile-of-wellness scale with consistent polarity.

---

*This file corresponds to the manuscript's Supplementary S1 (AI-assisted
development workflow + rendered project material). The dated prompts are the
authoritative record; model/version details reflect access in Feb–Jun 2026.*
