#!/bin/bash
#
# Run all Python unit tests
#
cd "$(dirname $0)"
MY_BASEDIR="$(pwd)"

PYTHON=""
for py_ver in $(seq 13 -1 8); do
    PYTHON=$(which "python3.${py_ver}" 2> /dev/null)
    [[ -n "$PYTHON" ]] && break
done
if [[ -z "$PYTHON" ]]; then
    echo "Cannot find an appropriate Python3 version"
    exit 1
else
    echo "Using Python: $PYTHON"
fi

$PYTHON -m unittest discover -v */tests
