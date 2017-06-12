#!/usr/bin/env bash

cd /deb/mssh-copy-id-*
dpkg-buildpackage -rfakeroot -b -us -uc
