# Copyright (c) 2026 Astera Institute
#
# run with `pixi run -e analysis python test_python_api.py`
# this is a simple integration test to ensure that we get the expected results for the included cif

import json, py_tortoize, pathlib

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
