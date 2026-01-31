/*-
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
 */


#define PYBIND11_DETAILED_ERROR_MESSAGES

#include "pybind11_json/pybind11_json.hpp"
#include <nlohmann/json.hpp>

#include "../cpp/tortoize.hpp"
#include "../cpp/revision.hpp"
#include "pybind11/pybind11.h"

namespace fs = std::filesystem;
namespace py = pybind11;
namespace nl = nlohmann;
using namespace pybind11::literals;


py::object tortoize_compute_stats(std::string const &structure_file_path) {
    py::print("Opening structure file to stream", structure_file_path);
    cif::gzio::ifstream xyzinFile(structure_file_path);
    if (not xyzinFile.is_open())
        throw std::runtime_error("Could not open xyzin file");

    // need to make sure we can access our dictionary files
    // this is a hacky way, but it works with pixi, so I'm keeping it for now.
    fs::path py_exec_path = extract_python_executable_path();
    fs::path mmcif_dic_path = py_exec_path.parent_path().parent_path() / "share/libcifpp/mmcif_pdbx.dic";
    py::print("Full mmcif dict path: ", std::string(mmcif_dic_path));
    cif::add_file_resource("mmcif_pdbx.dic", mmcif_dic_path);
    fs::path components_path = py_exec_path.parent_path().parent_path() / "share/libcifpp/components.cif";
    py::print("Full components dict path: ", std::string(components_path));
    cif::add_file_resource("components.cif", components_path);

    py::print("Structure file stream opened, reading in");
    cif::file structure_file = cif::pdb::read(xyzinFile);

    if (structure_file.empty())
        throw std::runtime_error("Invalid or empty mmCIF/PDB file");

    nl::json data{
		    { "software",
                { { "name", "py_tortoize" },
                    { "version", kVersionNumber },
                    { "reference", "Sobolev et al. A Global Ramachandran Score Identifies Protein Structures with Unlikely Stereochemistry, Structure (2020)" },
                    { "reference-doi", "https://doi.org/10.1016/j.str.2020.08.005" } } }
    };

    std::set<uint32_t> models;
    for (auto r : structure_file.front()["atom_site"])
    {
        if (not r["pdbx_PDB_model_num"].empty())
            models.insert(r["pdbx_PDB_model_num"].as<uint32_t>());
    }

    if (models.empty())
        models.insert(0);

    for (auto model : models)
    {
        py::print("Generating structure for ", std::to_string(model));
        cif::mm::structure structure(structure_file, model);

        py::print("Calculating z-scores for ", std::to_string(model));
        data["model"][std::to_string(model)] = calculateZScores(structure);
    }

    py::object pystats = data;
    return pystats;
}

PYBIND11_MODULE(py_tortoize, m)
{
    m.doc() = "Python bindings to PDB-REDO/tortoize module for computing side chain and backbone geometry statistics.";
    m.def("tortoize_compute_stats", &tortoize_compute_stats,
        R"pbdoc(Output tortoize statistics for a structure

        Parameters
        ----------
        structure_file_path: str
            path to the .cif or .pdb file containing coordinates to use for the calculations.

        We do not yet support restraint files.
        Returns
        -------
        list[dict[str, Any]]
            Various statistics for each residue in the .cif file.)pbdoc",
        py::arg("structure_file_path")
    );
}