#!/usr/bin/env bash

SCRIPT_DIR=$(dirname $(readlink -f $0))

cd ${SCRIPT_DIR}
rm -vrf .coverage .eggs build dist
find . \( -name '*,cover' -o -name '__pycache__' -o -name '*.py[co]' \) -exec rm -vrf '{}' \;
