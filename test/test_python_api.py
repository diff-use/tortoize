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

    for n in range(len(stats["model"]["1"]["residues"])):
        ress, resr = stats["model"]["1"]["residues"][n], ref_stats["model"]["1"]["residues"][n]
        if any([ress[k] != resr[k] for k in ("asymID", "compID", "seqID", "pdb")]):
            raise ValueError(f"Failed basic residue data at {n}: DO NOT rely on this installation of py_tortoize")
        if any([k in ress and abs(ress[k]["z-score"] - resr[k]["z-score"]) > 0.0001 for k in ("torsion", "ramachandran")]):
            raise ValueError(f"Failed z-score at {n}: DO NOT rely on this installation of py_tortoize")


def test_compute_stats2():
    stats = py_tortoize.tortoize_compute_stats(str(cif_file))
    with open(json_file) as fp:
        ref_stats = json.load(fp)

    model = stats["model"]
    ref_model = ref_stats["model"]
    assert len(model) == len(ref_model)

    residues = stats["model"]["1"]["residues"]
    ref_residues = ref_stats["model"]["1"]["residues"]
    assert len(residues) == len(ref_residues)

    for n, (ress, resr) in enumerate(zip(residues, ref_residues)):
        for k in ("asymID", "compID", "seqID", "pdb"):
            assert ress[k] == resr[k], f"Failed basic residue data at {n}"
        for k in ("torsion", "ramachandran"):
            if k == "torsion" and k not in ress and k not in resr:
                # not all side chains have torsion angles!
                continue
            # if the key is present in one or the other, it must be in both
            assert k in resr and k in ress, f"Missing {k} in residue at {n}"
            assert ress[k]["z-score"] == pytest.approx(resr[k]["z-score"], abs=1e-4), f"Failed z-score at {n}"
