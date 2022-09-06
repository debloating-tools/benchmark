# Copyright (c) 2022 SRI International All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from typing import List
import json
import os
import pprint

import click

from . import builder
from . import container
from . import core

OCCAM_IMAGE = "sricsl/occam:bionic"
OCCAM_CONTAINER_NAME = "pdb-occam"


class OccamConfig:
    def __init__(self) -> None:
        super().__init__()
        self.examples_volume = core.Volume(
            host_dir=core.project_relative_location("data/occam/volumes/examples"),
            container_dir="/pdbench/examples"
        )

        self.container_example_path = "/occam/examples"


occam_config = OccamConfig()
occam_container = container.ContainerWrapper(
    OCCAM_IMAGE, OCCAM_CONTAINER_NAME,
    [occam_config.examples_volume]
)


@core.cli.group(
    name="occam",
    help="Manage and run occam de-bloat container"
)
def occam():
    pass


@occam.command(
    name="start",
    help="Pull the occam image and start the container"
)
def occam_start():
    occam_container.start()


@occam.command(
    name="stop",
    help="Stop and **REMOVE** the occam docker container"
)
def occam_stop():
    occam_container.stop()


@occam.command(
    name="status",
    help="Check status of occam docker container"
)
def occam_status():
    occam_container.status()


@occam.command(
    name="shell",
    help="Start a shell in running occam docker container"
)
def occam_shell():
    occam_container.shell()

@occam.group(
    name="config",
    help="Modify or view config file"
)
def occam_config():
    pass

@occam_config.command(
    name="view",
    help="View current configrations"
)
def occam_config_view():
    with open('config.json','r') as file:
        occam_config = json.load(file)['OCCAM']
        pprint.pprint(occam_config,sort_dicts=False)
        
@occam_config.command(
    name="edit",
    help="Edit current configrations"
)
def occam_config_edit():
    with open('config.json','r+') as file:
        config=json.load(file)
        occam_config = config['OCCAM']['target-apps']
        occam_config=core.recursive_edit(occam_config,'Occam')
        config['OCCAM']['target-apps']=occam_config
    with open('config.json','w') as file:
        file.write(json.dumps(config, indent=4))

@occam_config.command(
    name="reset",
    help="Reset the configurations"
)
def occam_reset():
    with open('config.json','r+') as file:
        config=json.load(file)
        config_default=json.load(open('sources/default_config.json','r+'))
        config['OCCAM']=config_default['OCCAM']
    with open('config.json','w') as file:
        file.write(json.dumps(config, indent=4))
        print('Configurations reset to default')

@occam.command(
    name="run-config",
    help="Run the configurations for Occam in the config file"
)
def occam_run():
    OUTPUT_DIR=json.load(open('config.json','r+'))['OUTPUT_DIR']
    OUTPUT_DIR_OCCAM=os.path.join(OUTPUT_DIR,'Occam')
    OCCAM_CONTAINER_OUTPUT='/occam_bins'
    ARGS=['./sources/management_script.sh',OCCAM_IMAGE,'config.json','python3','adapter_occam.py',OUTPUT_DIR_OCCAM,OCCAM_CONTAINER_OUTPUT]
    core.process_check_call(ARGS)

@occam.group(
    name="examples",
    help="Copy and build default examples"
)


def occam_examples():
    pass


@occam_examples.command(
    name="copy",
    help="Copy defaults examples into examples volume"
)
def occam_copy_examples():
    # passing --interactive to keep the stdin active
    # in case the command requires some interactions
    core.process_check_call(
        [
            'docker', 'exec',
            '--interactive', OCCAM_CONTAINER_NAME,
            'cp', '-rv', f'{occam_config.container_example_path}/.',
            occam_config.examples_volume.container_dir
        ]
    )
    # The `/.` in the end of source indicates copy contents of
    # the directory instead of the directory itself


@occam_examples.command(
    name="list",
    help="List copied examples"
)
def occam_build_examples():
    for d in example_build_directories():
        print(d)


def filter_condition(dir_path: str, files: List[str]) -> bool:
    # Skipping darwin and freebsd

    return 'build.sh' in files and 'Makefile' in files and \
           not ('darwin' in dir_path or 'freebsd' in dir_path)


def example_build_directories():
    example_dir = occam_config.examples_volume.host_dir
    return core.find_rel_paths(example_dir, filter_condition)


def build_command(example: str) -> str:
    container_project_path = f"{occam_config.examples_volume.container_dir}/{example}"
    return f"cd {container_project_path} && make && ./build.sh"


@occam_examples.command(
    name="build",
    help="Build example(s) in examples volume"
)
@click.option('-e', '--example', help='Name of the example, if not specified, build all')
def occam_build_examples(example: str = None):
    b = builder.PdbBuilder('occam', OCCAM_CONTAINER_NAME)

    try:
        if example:
            b.build(example, build_command(example))

        else:
            for d in example_build_directories():
                b.build(d, build_command(d))

    finally:
        b.close()
