#!/usr/bin/env bash

CLEAN=0
ARGS=()

usage() {
    cat << EOT
Usage: $0 DOCKERFILE_DIR

Build a Docker image that will be used for RPM builds.

optional arguments:
  -h, --help        show this help
  -c, --clean       remove the Docker images instead of creating them
EOT
}

while [[ $# -gt 0 ]]; do
    key="$1"

    case $key in
        -h|--help)
        usage
        exit 0
        ;;
        -c|--clean)
        CLEAN=1
        shift # past argument or value
        ;;
        *)
        ARGS+=($key)
        shift # past argument or value
        ;;
    esac
done

if [ ${#ARGS[*]} -eq 0 ]; then
    echo 'Error: missing a Dockerfile directory.'
    usage
    exit 1
fi

# Build or clean the Docker images
for dockerfile_dir in ${ARGS[*]}; do
    docker_img=$(basename $dockerfile_dir)
    if [ $CLEAN -eq 1 ]; then
        docker rmi -f $docker_img
    else
        docker build -t $docker_img $dockerfile_dir
    fi
done
