#!/usr/bin/env bash

# Copyright (c) 2022 SRI International All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

set -euo pipefail

SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CONF_PATH="${SCRIPT_PATH}/.env"
# shellcheck source=.env
test -f "${CONF_PATH}" && source "${CONF_PATH}"
VENV_PATH="venv"

function usage {
    CMD="init.sh"

    cat <<EOT
Manage docker installation

Usage:
    ${CMD} help                         Print this message and quit

    ${CMD} docker-install               Install docker
    ${CMD} docker-change-dir [dir]      Change docker image directory
    ${CMD} docker-uninstall             Uninstall docker

    ${CMD} install                      Create virtualenv and install dependencies
    ${CMD} requirements                 Create requirements file
EOT
}

function cmd-docker-install() {

    if dpkg -s docker-ce >/dev/null 2>&1; then
        echo "docker-ce is already installed"
        return 0
    fi

    echo "Installing docker"

    sudo apt-get install -qy apt-transport-https ca-certificates curl gnupg-agent software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

    sudo apt-get update
    sudo apt-get install -yq docker-ce docker-ce-cli containerd.io docker-compose

    sudo usermod -a -G docker "${USER}"

    echo 'Restart the machine for user group association to get in affect'
}

function cmd-docker-change-dir() {

    if [[ -z "$*" ]]; then
        echo "Must provide a directory to set"
        return 1
    fi

    if [[ ! -d $1 ]]; then
        echo "Input $1 is not a directory"
        return 1
    fi

    echo 'Changing image directory in /etc/docker/daemon.json'

    cat <<EOM | sudo tee /etc/docker/daemon.json
{
    "graph": "$1",
    "storage-driver": "overlay2"
}
EOM

    sudo systemctl daemon-reload
    sudo systemctl restart docker

    docker info | grep "Docker Root Dir"
}

function cmd-docker-uninstall() {
    sudo apt-get purge docker-ce docker-ce-cli docker docker-engine docker.io containerd runc docker-compose
}

function python_version_check() {
    python3_version="$(python3 --version | sed 's_Python __')"

    if ! dpkg --compare-versions "${python3_version}" '>=' '3.6.0'; then
        echo "Minimum required python version is >= 3.6.0; current version: ${python3_version}"
        exit 1
    fi
}

function cmd-install() {

    python_version_check
    pushd "${SCRIPT_PATH}" >/dev/null || exit 1

    if [[ ! -d ${VENV_PATH} ]]; then
        sudo apt-get install -qy python3-venv
        python3 -m venv "${VENV_PATH}"
    fi

    pip="${VENV_PATH}/bin/pip"
    if [[ ! -x $pip ]]; then
        echo "venv exits but no pip found; inspect manually"
        exit 1
    fi

    "$pip" install -r requirements.txt
    "$pip" install -e .

    if [[ ! -L pdbench ]]; then
        echo 'Creating symlink'
        ln -sv "${VENV_PATH}/bin/pdbench" .
    fi

    for framework in occam razor chisel piecewise; do
        mkdir -p "data/${framework}/configs"
        mkdir -p "data/${framework}/volumes"
    done

    popd >/dev/null || exit 1
}

function cmd-requirements {
    pushd "${SCRIPT_PATH}" >/dev/null || exit 1

    echo 'Creating requirements file'
    "${VENV_PATH}/bin/pip" freeze | grep -e '#' -e '-e' -e 'pkg-resources==0.0.0' -v >'requirements.txt'

    popd >/dev/null || exit 1
}

if [[ -z "$*" || "$1" == '-h' || "$1" == '--help' || "$1" == 'help' ]]; then
    usage
    exit 0
fi

command="cmd-${1}"

if [[ $(type -t "${command}") != "function" ]]; then
    echo "Error: No command found"
    usage
    exit 1
fi

${command} "${@:2}"

