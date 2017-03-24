#!/usr/bin/env bash

CONTAINER_DEBBUILD_DIR=/deb

# Change ownership of /deb
UIG_GID=$(stat -c '%u:%g' /deb)
chown -R root:root /deb/*

cd $CONTAINER_DEBBUILD_DIR/mssh-copy-id-*
dpkg-buildpackage -rfakeroot -b -us -uc

# Revert ownership back of /deb
chown -R $UIG_GID /deb/*
