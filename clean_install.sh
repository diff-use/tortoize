#!/bin/bash

# a possibly over-thorough installation script

pixi clean && \
pixi install -e analysis && \
pixi run -e analysis python -m pip install . && \
pixi run -e analysis python -m pytest test/test_python_api.py