"""Provide tests for pattern_datalad."""

# Authors: Federico Raimondo <f.raimondo@fz-juelich.de>
#          Leonard Sasse <l.sasse@fz-juelich.de>
#          Synchon Mandal <s.mandal@fz-juelich.de>
# License: AGPL

from pathlib import Path

import pytest

from junifer.datagrabber.pattern_datalad import PatternDataladDataGrabber


_testing_dataset = {
    "example_bids": {
        "uri": "https://gin.g-node.org/juaml/datalad-example-bids",
        "id": "e2ce149bd723088769a86c72e57eded009258c6b",
    },
    "example_bids_ses": {
        "uri": "https://gin.g-node.org/juaml/datalad-example-bids-ses",
        "id": "3d08d55d1faad4f12ab64ac9497544a0d924d47a",
    },
}


def test_bids_pattern_datalad_datagrabber_missing_uri() -> None:
    """Test check of missing URI in pattern datalad datagrabber."""
    with pytest.raises(ValueError, match=r"`uri` must be provided"):
        PatternDataladDataGrabber(
            datadir=None,
            types=[],
            patterns={},
            replacements=[],
        )


def test_bids_PatternDataladDataGrabber(tmp_path: Path) -> None:
    """Test a subject-based BIDS datalad datagrabber.

    Parameters
    ----------
    tmp_path : pathlib.Path
        The path to the test directory.

    """
    # Define types
    types = ["T1w", "bold"]
    # Define patterns
    patterns = {
        "T1w": "{subject}/anat/{subject}_T1w.nii.gz",
        "bold": "{subject}/func/{subject}_task-rest_bold.nii.gz",
    }
    # Define replacements
    replacements = ["subject"]

    repo_uri = _testing_dataset["example_bids"]["uri"]
    rootdir = "example_bids"
    repo_commit = _testing_dataset["example_bids"]["id"]

    with PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri,
        types=types,
        patterns=patterns,
        replacements=replacements,
    ) as dg:
        subs = [x for x in dg]
        expected_subs = [f"sub-{i:02d}" for i in range(1, 10)]
        assert set(subs) == set(expected_subs)

        for elem in dg:
            t_sub = dg[elem]
            assert "path" in t_sub["T1w"]
            assert t_sub["T1w"]["path"] == (
                dg.datadir / f"{elem}/anat/{elem}_T1w.nii.gz"
            )
            assert "path" in t_sub["bold"]
            assert t_sub["bold"]["path"] == (
                dg.datadir / f"{elem}/func/{elem}_task-rest_bold.nii.gz"
            )

            assert "meta" in t_sub
            assert "datagrabber" in t_sub["meta"]
            dg_meta = t_sub["meta"]["datagrabber"]
            assert "class" in dg_meta
            assert dg_meta["class"] == "PatternDataladDataGrabber"
            assert "uri" in dg_meta
            assert dg_meta["uri"] == repo_uri
            assert "dataset_commit_id" in dg_meta
            assert dg_meta["dataset_commit_id"] == repo_commit

            with open(t_sub["T1w"]["path"], "r") as f:
                assert f.readlines()[0] == "placeholder"

    # datadir = tmp_path / "dataset"  # Need this for testing
    # patterns = {
    #     "T1w": "{subject}/anat/{subject}_T*w.nii.gz",
    #     "bold": "{subject}/func/{subject}_task-rest_*.nii.gz",
    # }
    # with PatternDataladDataGrabber(
    #     rootdir=rootdir,
    #     uri=repo_uri,
    #     types=types,
    #     patterns=patterns,
    #     datadir=datadir,
    #     replacements=replacements,
    # ) as dg:
    #     assert dg.datadir == datadir / rootdir
    #     for elem in dg:
    #         t_sub = dg[elem]
    #         assert "path" in t_sub["T1w"]
    #         assert t_sub["T1w"]["path"] == (
    #             dg.datadir / f"{elem}/anat/{elem}_T1w.nii.gz"
    #         )
    #         assert "path" in t_sub["bold"]
    #         assert t_sub["bold"]["path"] == (
    #             dg.datadir / f"{elem}/func/{elem}_task-rest_bold.nii.gz"
    #         )


def test_bids_PatternDataladDataGrabber_session():
    """Test a subject and session-based BIDS datalad datagrabber."""
    types = ["T1w", "bold"]
    patterns = {
        "T1w": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
        "bold": "{subject}/{session}/func/"
        "{subject}_{session}_task-rest_bold.nii.gz",
    }
    replacements = ["subject", "session"]

    with pytest.raises(ValueError, match=r"`uri` must be provided"):
        PatternDataladDataGrabber(
            datadir=None,
            types=types,
            patterns=patterns,
            replacements=replacements,
        )

    repo_uri = _testing_dataset["example_bids_ses"]["uri"]
    rootdir = "example_bids_ses"
    # repo_commit =  _testing_dataset['example_bids_ses']['id']

    # With T1W and bold, only 2 sessions are available
    with PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri,
        types=types,
        patterns=patterns,
        replacements=replacements,
    ) as dg:
        subs = [x for x in dg]
        expected_subs = [
            (f"sub-{i:02d}", f"ses-{j:02d}")
            for j in range(1, 3)
            for i in range(1, 10)
        ]
        assert set(subs) == set(expected_subs)

    # Test with a different T1w only, it should have 3 sessions
    types = ["T1w"]
    patterns = {
        "T1w": "{subject}/{session}/anat/{subject}_{session}_T1w.nii.gz",
    }
    with PatternDataladDataGrabber(
        rootdir=rootdir,
        uri=repo_uri,
        types=types,
        patterns=patterns,
        replacements=replacements,
    ) as dg:
        subs = [x for x in dg]
        expected_subs = [
            (f"sub-{i:02d}", f"ses-{j:02d}")
            for j in range(1, 4)
            for i in range(1, 10)
        ]
        assert set(subs) == set(expected_subs)
