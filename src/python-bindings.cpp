//
// Created by Marcus Collins on 1/16/26.
// marcus.collins@astera.org
//


#include "pybind11_json/pybind11_json.hpp"
#include <nlohmann/json.hpp>

#include "tortoize.hpp"
#include "pybind11/pybind11.h"

namespace fs = std::filesystem;
namespace py = pybind11;
namespace nl = nlohmann;
using namespace pybind11::literals;


py::object tortoize_compute_stats(std::string const &structure_file_path) {
    nl::json data = tortoize_calculate(structure_file_path);

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