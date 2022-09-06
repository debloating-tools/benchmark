# Copyright (c) 2022 SRI International All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import logging
import os
import re
import shutil
import json
import pprint

import docker
import requests

from . import builder
from . import container
from . import core

PIECEWISE_IMAGE = "piecewise0001bloat/piecewise"
PIECEWISE_CONTAINER_NAME = "pdb-piecewise"

examples_volume = core.Volume(
    core.project_relative_location('data/piecewise/volumes/examples'),
    '/pdbench/examples'
)

piecewise_container = container.ContainerWrapper(
    PIECEWISE_IMAGE, PIECEWISE_CONTAINER_NAME, [examples_volume]
)


@core.cli.group(
    name="piecewise",
    help="Manage and run piecewise de-bloat container"
)
def piecewise():
    pass


@piecewise.command(
    name='load-image',
    help="Download and load piecewise docker image"
)
def piecewise_build_image_cmd():
    piecewise_load_image()


def piecewise_load_image():
    client = docker.from_env()
    existing_images = client.images.list(PIECEWISE_IMAGE)

    if existing_images:
        logging.info("Piecewise image found; to re-load remove from docker image")
        return

    piecewise_dir = core.project_relative_location('data/piecewise')
    docker_image_path = os.path.join(piecewise_dir, 'piece-wise.docker')

    if os.path.exists(docker_image_path):
        logging.info("Piecewise docker image found, to re-download remove it manually")
    else:
        download_piecewise_image(docker_image_path)

    logging.info("Loading piecewise image")

    core.process_check_call(
        ['docker', 'load', '--input', docker_image_path],
        cwd=piecewise_dir
    )


def download_piecewise_image(docker_image_path):
    requests_session = requests.session()
    google_file_id = "1-7gYC63Aaps7KGkGgWisEF_96ChxI9jV"

    file_url = f"https://docs.google.com/uc?export=download&id={google_file_id}"
    r = requests_session.get(file_url)

    m = re.search(r'confirm=([0-9A-Za-z_]+)', r.text)
    if not m:
        raise core.ProDeBenchError("Failed to parse confirm id from GoogleDrive download response")

    confirm_id = m.group(1)

    url = f"https://docs.google.com/uc?export=download&confirm={confirm_id}&id={google_file_id}"

    logging.info("Starting piecewise docker image download from google drive; might take a while")
    with requests_session.get(url, stream=True) as r:
        with open(docker_image_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)

    logging.info("Download complete")


@piecewise.command(
    name="start",
    help="Pull the piecewise image and start the container"
)
def piecewise_start():
    piecewise_load_image()
    piecewise_container.start(['--cap-add=SYS_PTRACE', '--security-opt', 'seccomp=unconfined'])


@piecewise.command(
    name="stop",
    help="Stop and **REMOVE** the piecewise docker container"
)
def piecewise_stop():
    piecewise_container.stop()


@piecewise.command(
    name="status",
    help="Check status of piecewise docker container"
)
def piecewise_status():
    piecewise_container.status()


@piecewise.command(
    name="shell",
    help="Start a shell in running piecewise docker container"
)
def piecewise_shell():
    piecewise_container.shell()
@piecewise.group(
    name="config",
    help="Modify or view config file"
)
def piecewise_config():
    pass

@piecewise_config.command(
    name="view",
    help="View current configrations"
)
def piecewise_config_view():
    with open('config.json','r') as file:
        piecewise_config = json.load(file)['PWISE']
        pprint.pprint(piecewise_config,sort_dicts=False)
@piecewise_config.command(
    name="edit",
    help="Edit current configrations"
)
def piecewise_config_edit():
    with open('config.json','r+') as file:
        config=json.load(file)
        pwise_config = config['PWISE']
        pwise_config=core.recursive_edit(pwise_config,'Piecewise')
        config['PWISE']=pwise_config
    with open('config.json','w') as file:
        file.write(json.dumps(config, indent=4))

@piecewise_config.command(
    name="reset",
    help="Reset the configurations"
)
def piecewise_reset():
    with open('config.json','r+') as file:
        config=json.load(file)
        config_default=json.load(open('sources/default_config.json','r+'))
        config['PWISE']=config_default['PWISE']
    with open('config.json','w') as file:
        file.write(json.dumps(config, indent=4))
        print('Configurations reset to default')

@piecewise.command(
    name="run-config",
    help="Run the configurations for Piecewise in the config file"
)
def piecewise_run():
    OUTPUT_DIR=json.load(open('config.json','r+'))['OUTPUT_DIR']
    OUTPUT_DIR_PIECEWISE=os.path.join(OUTPUT_DIR,'Piecewise')
    PIECEWISE_CONTAINER_OUTPUT='/piecewise_bins'
    ARGS=['./sources/management_script.sh',PIECEWISE_IMAGE,'config.json','python3','adapter_piecewise.py',OUTPUT_DIR_PIECEWISE,PIECEWISE_CONTAINER_OUTPUT]
    core.process_check_call(ARGS)

@piecewise.group(
    name='examples',
    help="Copy and build default examples"
)
def piecewise_examples():
    pass


def write_build_script():
    # This commands are from README.md in the container home
    cmds = '''#!/usr/bin/env bash

if [[ ! -d coreutils-8.25 ]]; then
    wget https://launchpad.net/ubuntu/+archive/primary/+files/coreutils_8.25.orig.tar.xz
    tar xvf coreutils_8.25.orig.tar.xz
fi

cd coreutils-8.25/
./configure --enable-no-install-program=csplit CC=musl-clang CFLAGS='-flto -O0' FORCE_UNSAFE_CONFIGURE=1
sed -i '152s/.*/#define FUNC_FFLUSH_STDIN -1/' ./lib/config.h
sed -i '148s/.*/#define FTELLO_BROKEN_AFTER_SWITCHING_FROM_READ_TO_WRITE 0/' ./lib/config.h
make || exit 1
'''

    core.make_dirs(examples_volume.host_dir)

    script_path = os.path.join(examples_volume.host_dir, 'build-core-utils.sh')
    core.write_executable_script(script_path, cmds)


@piecewise_examples.command(
    name="build",
    help="Build core utils with piecewise"
)
def piecewise_examples_build():
    write_build_script()

    logging.info("Building core utils in piecewise")

    b = builder.PdbBuilder('piecewise', PIECEWISE_CONTAINER_NAME)
    b.build('all', f'{examples_volume.container_dir}/build-core-utils.sh')
