"""
Tests for the blinded subject pipeline inputs.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from neuropsych_pipeline import BLINDED_DATA_PATH, analyze_patient, get_all_patient_ids, load_cohort


@pytest.fixture(scope="module")
def blinded_df():
    """Load the blinded cohort once for all tests in this module."""
    return load_cohort(BLINDED_DATA_PATH)


def test_default_load_path_is_repo_safe():
    default_df = load_cohort()
    ids = get_all_patient_ids(default_df)

    assert isinstance(default_df, pd.DataFrame)
    assert len(default_df) == 105
    assert ids[0] == "subj_001"


def test_blinded_cohort_loads(blinded_df):
    assert isinstance(blinded_df, pd.DataFrame)
    assert len(blinded_df) == 105


def test_blinded_cohort_uses_subject_ids(blinded_df):
    ids = get_all_patient_ids(blinded_df)
    assert ids[0] == "subj_001"
    assert ids[-1] == "subj_105"
    assert all(pid.startswith("subj_") for pid in ids)


def test_blinded_cohort_tolerates_missing_education(blinded_df):
    assert "Education" in blinded_df.columns
    assert blinded_df["Education"].isna().all()


def test_blinded_analysis_has_public_safe_demographics(blinded_df):
    result = analyze_patient(blinded_df, "subj_001")
    demo = result["demographics"]

    assert result["patient_id"] == "subj_001"
    assert demo["gender"] in {"M", "F"}
    assert demo["age"] is not None
    assert demo["ibs_status"] in {"IBS", "HC"}
    assert demo["education"] is None


def test_blinded_analysis_tracks_blinded_cohort_sizes(blinded_df):
    result = analyze_patient(blinded_df, "subj_001")
    summary = result["cohort_summary"]

    assert summary["total_n"] == len(blinded_df)
    assert summary["group_counts"]["IBS"] + summary["group_counts"]["HC"] == len(blinded_df)


def test_blinded_reasoning_omits_missing_education(blinded_df):
    result = analyze_patient(blinded_df, "subj_001")
    assert "education None years" not in result["reasoning_chain"][0]
