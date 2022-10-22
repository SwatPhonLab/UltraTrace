#!/bin/bash
#
# Set up a development environment for 'ultratrace'.
#
# Note that since this script is meant to be "source"d, we can't use
# the "set -euo pipefail" idiom (since that means that we would set
# those shell options in our host environment (this would cause bash
# to exit if we ran any command returning a non-zero exit code)).

export ULTRATRACE_ROOT="$(git rev-parse --show-toplevel)"
export ULTRATRACE_VENV="$ULTRATRACE_ROOT/venv/ultratrace"
export ULTRATRACE_PYTHON="${ULTRATRACE_PYTHON:-python3}"

# Create a virtual environment if we don't already have one.
if [ ! -e "$ULTRATRACE_VENV/bin/activate" ]; then
    echo "Creating a virtual environment at '$ULTRATRACE_VENV'" >&2
    rm -rf "$ULTRATRACE_VENV"
    "$ULTRATRACE_PYTHON" -m venv "$ULTRATRACE_VENV"
fi

# Activate the virtual environment.
source "$ULTRATRACE_VENV/bin/activate"

pip install --upgrade \
    pip==22.3 \
    setuptools==65.5.0 \
    wheel==0.38.0

pip install \
    nox==2022.8.7

pip install \
    --requirement "$ULTRATRACE_ROOT/requirements-dev.txt"
