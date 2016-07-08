#!/usr/bin/env bash

# We suppose that the Docker image "ubuntu14.04-build-mssh-copy-id" has been created and imported.

PROJECT_DIR=$(dirname $(readlink -e $0))
DEBBUILD_DIR=$PROJECT_DIR/dist/deb
CONTAINER_DEBBUILD_DIR=/deb
CLEAN=0
ARGS=()

usage() {
    cat << EOT
Usage: $0

Build the deb package.

optional arguments:
  -h, --help        show this help
EOT
}

while [[ $# -gt 0 ]]; do
    key="$1"

    case $key in
        -h|--help)
        usage
        exit 0
        ;;
        *)
        ARGS+=($key)
        shift # past argument or value
        ;;
    esac
done

# Create directories layout
mkdir -p $DEBBUILD_DIR

# Copy the sources
cd $PROJECT_DIR
python setup.py sdist --dist-dir $DEBBUILD_DIR
cp -r $PROJECT_DIR/deb/debian $DEBBUILD_DIR
tar -xvf $DEBBUILD_DIR/mssh-copy-id-*.tar.gz -C $DEBBUILD_DIR

# Build the deb
docker run -v $DEBBUILD_DIR:$CONTAINER_DEBBUILD_DIR ubuntu14.04-build-mssh-copy-id
