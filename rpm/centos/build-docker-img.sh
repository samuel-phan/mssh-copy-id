#!/usr/bin/env bash

SCRIPT_DIR=$(dirname $(readlink -e $0))
docker build -t mssh-copy-id-build-centos6 $SCRIPT_DIR/docker-img
