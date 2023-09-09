#!/bin/bash
#
# Run all Python unit tests
#
cd "$(dirname $0)"
MY_BASEDIR="$(pwd)"

python3 -m unittest discover -v */tests
