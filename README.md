PyTortoize
========

Application to calculate ramachandran z-scores, now accessible from Python.

Building
--------
This package is a fork of the original PDB-REDO/tortoize repository. Its only goal is
to use tortoize from Python, primarily via the pixi package manager. It is also possible to generate
the library as a shared library with your system Python. 

Pixi installation
-----------------
It may be possible to simplify these instructions, but for now, do this:

```console
git clone https://github.com/diff-use/tortoize.git
cd tortoize
pixi install -e analysis && pixi run -e analysis python -m pip install .
```

If you then launch a python interpreter, e.g. `pixi run -e analysis ipython`, 
the library should be available. It is strongly recommended to test the installation:

```console
pixi run -e analysis python -m pytest test/test_python_api.py
```


Using from other pixi packages
------------------------------
To use this package from another pixi package, add it like so to your dependencies:
```toml
[dependencies]
...
py_tortoize = { git = "https://github.com/diff-use/tortoize.git", branch = "mdc-python-bindings" }
```

Installation with system python
-------------------------------

It is possible to install py_tortoize on Linux with the system python. In that case you will have 
install some dependencies first. On Debian this boils down to:

```console
sudo apt-get update && sudo apt-get install libcatch2-dev nlohmann-json3-dev libeigen3-dev
```

And on Ubuntu, slightly different:

```console
sudo apt-get update && sudo apt-get install catch2 nlohmann-json3-dev libeigen3-dev
```

After that, building and installing should be as simple as:

```console
git clone https://github.com/diff-use/tortoize.git
cd tortoize
cmake -S . -B build
cmake --build build
sudo cmake --install build
```

Note that PyTortoize requires that the binary distribution files under `rsrc` be in a folder
relative to where your Python is installed. E.g. if your Python is installed in `/usr/bin/python3`,
you should make sure the files are available in `/usr/share/libcifpp/.`. The installation should
take care of this, but be aware of it if you get strange file read errors.

Usage
-----

Right now, only one method is available:

```python
import py_tortoize
stats = py_tortoize.tortoize_compute_stats(cif_file)
```

`cif_file` is a _string_ path to a CIF file, and can be a gzip archive. The output is a dictionary 
including some metadata, summary statistics, and a list of residue-level metrics