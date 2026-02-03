"""
* SPDX-License-Identifier: BSD-2-Clause
*
* Copyright (c) 2026 Astera Institute
* Authored by Marcus D. Collins marcus.collins@astera.org
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*
* 1. Redistributions of source code must retain the above copyright notice, this
*    list of conditions and the following disclaimer
* 2. Redistributions in binary form must reproduce the above copyright notice,
*    this list of conditions and the following disclaimer in the documentation
*    and/or other materials provided with the distribution.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
* ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
* WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
* ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
* (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
* LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
* ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
* (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
* SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from __future__ import annotations

import fnmatch
from argparse import ArgumentParser
from joblib import Parallel, delayed
from pathlib import Path
from typing import Any, Union

import pandas as pd
from loguru import logger
from pandas import DataFrame

from py_tortoize import tortoize_compute_stats


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        "--parent-directory", help="Directory to crawl for CIF files", required=True
    )
    parser.add_argument(
        "--output-file-prefix", help="Prefix for output file names", required=True
    )
    parser.add_argument(
        "--target-file-pattern",
        default="*.cif",
        help="Pattern to match target files, default is '*.cif'"
    )
    parser.add_argument(
        "--n-jobs",
        default=-1,
        type=int,
        help="Number of cpus to use for computing statistics. Default -1 (all cpus)"
    )
    return parser.parse_args()


def crawl_dir_by_depth(
        root_dir: Union[str, Path],
        target_pattern: str,
        n_levels: int,
) -> list[Path]:
    """
    Recursively crawl `root_dir` up to `n_levels` directory levels deep and return
    all files whose *name* matches `target_pattern` (fnmatch-style, e.g. "*.cif").

    Depth meaning:
      - n_levels = 0: only files directly in root_dir
      - n_levels = 1: root_dir + its immediate subdirectories
      - etc.
    """
    root = Path(root_dir)
    if n_levels < 0:
        return []

    results: list[Path] = []

    def _crawl(current: Path, levels_left: int) -> None:
        try:
            for entry in current.iterdir():
                if entry.is_file():
                    if fnmatch.fnmatch(entry.name, target_pattern):
                        results.append(entry)
                elif entry.is_dir() and levels_left > 0:
                    _crawl(entry, levels_left - 1)
        except (PermissionError, FileNotFoundError):
            # Skip unreadable or transient directories
            return

    _crawl(root, n_levels)
    return results


def flatten_residues(tortoize_json: dict[str, Any]) -> pd.DataFrame:
    """
    Flattens tortoize JSON into one dict per residue across all models.
    See test/1cbs.json for an example of the tortoize output JSON

    Output keys per residue:
      - model (e.g. "1")
      - asymID
      - compID
      - seqID
      - ss_type (taken from ramachandran["ss-type"] if present, else torsion["ss-type"])
      - ramachandran_z_score (ramachandran["z-score"])
      - torsion_z_score (torsion["z-score"])
    """
    out: list[dict[str, Any]] = []

    # This is possibly over-robust. Claude Sonnet wrote it and I checked/modified it.
    model_block = tortoize_json.get("model", {})
    for model_id, model_data in model_block.items():
        residues = (model_data or {}).get("residues", [])
        for r in residues:
            rama = (r or {}).get("ramachandran", {})
            tors = (r or {}).get("torsion", {})
            pdb_info = (r or {}).get("pdb", {})

            ss_type: str | None = rama.get("ss-type", None)
            if ss_type is None:
                ss_type = tors.get("ss-type", None)

            out.append(
                {
                    "model": str(model_id),
                    "asymID": r.get("asymID", None),
                    "compID": r.get("compID", None),
                    "seqID": r.get("seqID", None),
                    "strandID": pdb_info.get("strandID", None),
                    "insCode": pdb_info.get("insCode", None),
                    "ss_type": ss_type,
                    "ramachandran_z_score": rama.get("z-score", None),
                    "torsion_z_score": tors.get("z-score", None),
                }
            )

    return pd.DataFrame(out)


def get_protein_level_z_scores(tortoize_json: dict[str, Any]) -> pd.DataFrame:
    """
    Extracts protein-level z-scores for torsion and Ramachandran angles from tortoize JSON output.
    See test/1cbs.json for an example of the tortoize output JSON


    :param tortoize_json:
    :return: pd.DataFrame with keys:
      - model (e.g. "1")
      - ramachandran_z_score
      - torsion_z_score
      - ramachandran_jackknife_sd
      - torsion_jackknife_sd
      - residue_count
    """

    out: list[dict[str, Any]] = []
    model_block = tortoize_json.get("model", {})
    for model_id, model_data in model_block.items():
        out.append({
            "model": str(model_id),
            "ramachandran_z_score": model_data.get("ramachandran-z", None),
            "ramachandran_jackknife_sd": model_data.get("ramachandran-jackknife-sd", None),
            "torsion_z_score": model_data.get("torsion-z", None),
            "torsion_jackknife_sd": model_data.get("torsion-jackknife-sd", None)
        })
    return pd.DataFrame(out)

def get_stats_for_single_path(path: Path) -> tuple[DataFrame, DataFrame]:
    result = tortoize_compute_stats(str(path))
    residues = flatten_residues(result)
    residues["path"] = path

    protein_level_stats = get_protein_level_z_scores(result)
    protein_level_stats["path"] = path
    return residues, protein_level_stats


def main(parent_directory, output_file_prefix, target_file_pattern, jobs=-1):
    paths = crawl_dir_by_depth(parent_directory, target_file_pattern, 5)
    if not paths:
        logger.error("No CIF files were found to analyze. Exiting")
        return

    results = Parallel(n_jobs=jobs)(delayed(get_stats_for_single_path)(path) for path in paths)
    all_residue_results, all_protein_results = tuple(zip(*results, strict=True))

    output_file = f"{output_file_prefix}_residues.csv"
    pd.concat(all_residue_results).to_csv(output_file, index=False)
    logger.info(f"Residue results saved to {output_file}")

    output_file = f"{output_file_prefix}_protein_stats.csv"
    pd.concat(all_protein_results).to_csv(output_file, index=False)
    logger.info(f"Protein-level stats saved to {output_file}")


if __name__ == "__main__":
    args = parse_args()
    main(args.parent_directory, args.output_file_prefix, args.target_file_pattern, jobs=args.n_jobs)
