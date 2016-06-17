#!/usr/bin/env bash

# We suppose that the Docker image "mssh-copy-id-build-centos6" has been created & imported

PROJECT_DIR=$(dirname $(readlink -e $0))
RPMBUILD_DIR=$PROJECT_DIR/dist/rpmbuild
CONTAINER_RPMBUILD_DIR=/rpmbuild

# Create directories layout
mkdir -p $RPMBUILD_DIR/BUILD
mkdir -p $RPMBUILD_DIR/RPMS
mkdir -p $RPMBUILD_DIR/SOURCES
mkdir -p $RPMBUILD_DIR/SPECS
mkdir -p $RPMBUILD_DIR/SRPMS

# Copy the sources & spec file
cd $PROJECT_DIR
python setup.py sdist --dist-dir $RPMBUILD_DIR/SOURCES
cp -f $PROJECT_DIR/rpm/centos/mssh-copy-id.spec $RPMBUILD_DIR/SPECS

# Build the RPM
docker run -v $RPMBUILD_DIR:$CONTAINER_RPMBUILD_DIR mssh-copy-id-build-centos6
