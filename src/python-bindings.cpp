//
// Marcus Collins, 1/16/26.
// marcus.collins@astera.org
// Copyright (c) 2026 Astera Institute
//

#define PYBIND11_DETAILED_ERROR_MESSAGES

#include "pybind11_json/pybind11_json.hpp"
#include <nlohmann/json.hpp>

#include "tortoize.hpp"
#include "revision.hpp"
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

    // inline test for debugging
    for (auto r: data["model"][std::to_string(1)]["residues"])
    {
        if (r.contains("torsion"))
            py::print("Warning for residue ", r["seqID"], r["compID"], " has z-score ", r["torsion"]["z-score"]);
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