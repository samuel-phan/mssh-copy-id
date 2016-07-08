#!/usr/bin/env bash

# We suppose that the Docker image "centos6-build-mssh-copy-id" or "centos7-build-mssh-copy-id" has been created and
# imported.

SUPPORTED_OSES=("centos6" "centos7")
PROJECT_DIR=$(dirname $(readlink -e $0))
RPMBUILD_DIR=$PROJECT_DIR/dist/rpmbuild
CONTAINER_RPMBUILD_DIR=/rpmbuild
CLEAN=0
ARGS=()

usage() {
    cat << EOT
Usage: $0 OS_TARGET [OS_TARGET..]

Build the RPM package.

positional arguments:
  OS_TARGET         "centos6" or "centos7"

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

if [ ${#ARGS[*]} -eq 0 ]; then
    echo 'Error: missing an OS target.'
    usage
    exit 1
else
    for os_target in ${ARGS[*]}; do
        if [[ ! ${SUPPORTED_OSES[*]} =~ "$os_target" ]]; then
            echo "Error: OS target \"${os_target}\" not supported."
            usage
            exit 1
        fi
    done
fi

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
for os_target in ${ARGS[*]}; do
    docker run -v $RPMBUILD_DIR:$CONTAINER_RPMBUILD_DIR ${os_target}-build-mssh-copy-id
done
