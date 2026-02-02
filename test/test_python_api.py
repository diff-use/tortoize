# Copyright (c) 2026 Astera Institute
#
# run with `pixi run -e analysis python -m pytest test_python_api.py`
# this is a simple integration test to ensure that we get the expected results for the included cif

import json
import pathlib
import pytest

import py_tortoize


cif_file = pathlib.Path(__file__).parent / "1cbs.cif.gz"
json_file = pathlib.Path(__file__).parent / "1cbs.json"


def test_compute_stats():
    stats = py_tortoize.tortoize_compute_stats(str(cif_file))
    with open(json_file) as fp:
        ref_stats = json.load(fp)

    model = stats["model"]
    ref_model = ref_stats["model"]
    assert len(model) == len(ref_model)

    residues = stats["model"]["1"]["residues"]
    ref_residues = ref_stats["model"]["1"]["residues"]
    assert len(residues) == len(ref_residues)

    for n, (ress, resr) in enumerate(zip(residues, ref_residues, strict=True)):
        for k in ("asymID", "compID", "seqID", "pdb"):
            assert ress[k] == resr[k], f"Failed basic residue data at {n}"
        for k in ("torsion", "ramachandran"):
            if k == "torsion" and k not in ress and k not in resr:
                # not all side chains have torsion angles!
                continue
            # if the key is present in one or the other, it must be in both
            assert k in resr and k in ress, f"Missing {k} in residue at {n}"
            assert ress[k]["z-score"] == pytest.approx(resr[k]["z-score"], abs=1e-4), f"Failed z-score at {n}"
