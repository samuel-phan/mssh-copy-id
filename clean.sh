#!/usr/bin/env bash

SCRIPT_DIR=$(dirname $(readlink -f $0))

cd ${SCRIPT_DIR}
rm -vrf .coverage .eggs build dist mssh_copy_id.egg-info
find . -name '*,cover' -exec rm -vf '{}' \;
