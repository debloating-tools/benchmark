# Copyright (c) 2022 SRI International All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import logging
from typing import List
import os
import click
import docker
import requests

from . import builder
from . import container
from . import core


import json
import pprint

CHISEL_IMAGE = "chisel"
CHISEL_CONTAINER_NAME = "pdb-chisel"

examples_volume = core.Volume(
    core.project_relative_location('data/chisel/volumes/examples'),
    '/pdbench/examples'
)

chisel_container = container.ContainerWrapper(CHISEL_IMAGE, CHISEL_CONTAINER_NAME, [examples_volume])
container_example_path = '/chisel-bench'


@core.cli.group(
    name="chisel",
    help="Manage and run chisel de-bloat container"
)
def chisel():
    pass


@chisel.command(
    name='build-image',
    help="Download chisel Dockerfile and build the image"
)
def chisel_build_image_cmd():
    chisel_build_image()


def chisel_build_image():
    client = docker.from_env()
    existing_images = client.images.list(CHISEL_IMAGE)

    if existing_images:
        logging.info("Chisel image found; to rebuild remove it first")
        return

    url = 'https://raw.githubusercontent.com/keffinel/chisel/master/docker/Dockerfile'

    logging.info(f"Downloading chisel docker file from {url}")

    docker_file_dir = core.project_relative_location('data/chisel/docker')
    docker_file_path = os.path.join(docker_file_dir, 'Dockerfile')

    core.make_parent_dirs(docker_file_path)

    r = requests.get(url)
    with open(docker_file_path, 'w') as f:
        f.write(r.text)

    logging.info("Building chisel docker image")
    core.process_check_call(
        ['docker', 'build', '-t', CHISEL_IMAGE, '.'],
        cwd=docker_file_dir
    )

@chisel.command(
    name="start",
    help="Pull the chisel image and start the container"
)
def chisel_start():
    chisel_build_image()
    chisel_container.start(['--privileged'])


@chisel.command(
    name="stop",
    help="Stop and **REMOVE** the chisel docker container"
)
def chisel_stop():
    chisel_container.stop()


@chisel.command(
    name="status",
    help="Check status of chisel docker container"
)
def chisel_status():
    chisel_container.status()


@chisel.command(
    name="shell",
    help="Start a shell in running chisel docker container"
)
def chisel_shell():
    chisel_container.shell()

@chisel.command(
    name="commit",
    help="Commit your changes of chisel docker container"
)
def chisel_shell():
    chisel_container.commit()    

@chisel.group(
    name="config",
    help="Modify or view config file"
)
def chisel_config():
    pass

@chisel_config.command(
    name="view",
    help="View current configrations"
)
def chisel_config_view():
    with open('config.json','r') as file:
        chisel_config = json.load(file)['CHISEL']
        pprint.pprint(chisel_config,sort_dicts=False)

@chisel_config.command(
    name="edit",
    help="Edit current configrations"
)
def chisel_config_edit():
    with open('config.json','r+') as file:
        config=json.load(file)
        chisel_config = config['CHISEL']
        chisel_config=core.recursive_edit(chisel_config,'Chisel')
        config['CHISEL']=chisel_config
    with open('config.json','w') as file:
        file.write(json.dumps(config, indent=4))

@chisel_config.command(
    name="reset",
    help="Reset the configurations"
)
def chisel_reset():
    with open('config.json','r+') as file:
        config=json.load(file)
        config_default=json.load(open('sources/default_config.json','r+'))
        config['CHISEL']=config_default['CHISEL']
    with open('config.json','w') as file:
        file.write(json.dumps(config, indent=4))
        print('Configurations reset to default')

@chisel.command(
    name="run-config",
    help="Run the configurations for Chisel in the config file"
)
def chisel_run():
    OUTPUT_DIR=json.load(open('config.json','r+'))['OUTPUT_DIR']
    OUTPUT_DIR_CHISEL=os.path.join(OUTPUT_DIR,'Chisel')
    CHISEL_CONTAINER_OUTPUT='/chisel_bins'
    ARGS=['./sources/management_script.sh',CHISEL_IMAGE,'config.json','bash','adapter_chisel.sh',OUTPUT_DIR_CHISEL,CHISEL_CONTAINER_OUTPUT]
    core.process_check_call(ARGS)

@chisel.group(
    name="examples",
    help="Copy and build default examples"
)
def chisel_examples():
    pass


@chisel_examples.command(
    name="copy",
    help="Copy defaults examples into examples volume"
)
def chisel_examples_copy():
    core.process_check_call(
        [
            'docker', 'exec',
            '--interactive', CHISEL_CONTAINER_NAME,
            'cp', '-rv', f'{container_example_path}/.',
            examples_volume.container_dir
        ]
    )

    # This one needs us to source some variables before building
    # We are creating a wrapper bash script.

    cmds = '''#!/usr/bin/env bash


SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "$*" ]]; then
    echo "Need to pass project name"
    exit 1
fi

project="$1"
if [[ -d $project ]]; then
    echo "No directory found ${project}"
    exit 1
fi

# Sourcing the provided scripts
# . setenv
# Exporting variables manually, update accordingly

export CC=clang
export CHISEL_BENCHMARK_HOME="${SCRIPT_PATH}"

pushd "${SCRIPT_PATH}/${project}" > /dev/null || exit 1

# Needed if Chisel is being run with build system integration 
export NAME=`echo $(basename $(pwd)) | sed 's/bsysi_//g'`

# If the project being debloated has the bsysi_ prefix
if echo $(basename $(pwd)) | grep -q 'bsysi' ; then
    . ../prepare
    cp ../chisel_files/chisel.mk .
fi
echo "Reducing in ${project}"
make -f chisel.mk reduce || exit 1

popd > /dev/null || exit 1
'''

    script_path = os.path.join(examples_volume.host_dir, 'pdbench_wrapper.sh')
    core.write_executable_script(script_path, cmds)


@chisel_examples.command(
    name="list",
    help="List examples"
)
def chisel_examples_list():
    for d in example_build_directories():
        print(d)


def filter_condition(dir_path: str, files: List[str]) -> bool:
    # Skipping lib and original dirs
    IGNORE_DIRS = ['lib', 'original', 'chisel_files', '.git']
    return not any([dir in dir_path for dir in IGNORE_DIRS]) and \
        'bsysi_' in dir_path or 'chisel.mk' in files


def example_build_directories():
    example_dir = examples_volume.host_dir
    return core.find_rel_paths(example_dir, filter_condition)


def build_command(example: str) -> str:
    return f'{examples_volume.container_dir}/pdbench_wrapper.sh {example}'


@chisel_examples.command(
    name="build",
    help="Build example(s) in examples volume"
)
@click.option('-e', '--example', help='Name of the example, if not specified, build all')
def chisel_examples_build(example: str = None):
    b = builder.PdbBuilder('chisel', CHISEL_CONTAINER_NAME)

    try:
        if example:
            b.build(example, build_command(example))

        else:
            for d in example_build_directories():
                b.build(d, build_command(d))

    finally:
        b.close()
