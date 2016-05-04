#!/usr/bin/env bash

SCRIPT_DIR=$(dirname $(readlink -f $0))

cd ${SCRIPT_DIR}
py.test --cov msshcopyid --cov-report annotate --cov-report term-missing -v tests
