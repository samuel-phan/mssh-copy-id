#!/usr/bin/env bash

# Change ownership of /rpmbuild
UIG_GID=$(stat -c '%u:%g' /rpmbuild)
chown -R root:root /rpmbuild/*

rpmbuild --define '_topdir /rpmbuild' -ba /rpmbuild/SPECS/mssh-copy-id.spec

# Revert ownership back of /rpmbuild
chown -R $UIG_GID /rpmbuild/*
