# Copyright (c) 2022 SRI International All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
from typing import List

import click
from . import core, container, builder

import json
import pprint
RAZOR_IMAGE = "martianmorning/razor:1.1"
RAZOR_CONTAINER_NAME = "pdb-razor"

examples_volume = core.Volume(
    core.project_relative_location('data/razor/volumes/examples'),
    '/pdbench/examples'
)
container_example_path = '/root/workspace/razor'

razor_container = container.ContainerWrapper(
    RAZOR_IMAGE, RAZOR_CONTAINER_NAME, [examples_volume]
)


@core.cli.group(
    name="razor",
    help="Manage and run razor de-bloat container"
)
def razor():
    pass


@razor.command(
    name="start",
    help="Pull the razor image and start the container"
)
def razor_start():
    razor_container.start()


@razor.command(
    name="stop",
    help="Stop and **REMOVE** the razor docker container"
)
def razor_stop():
    razor_container.stop()


@razor.command(
    name="status",
    help="Check status of razor docker container"
)
def razor_status():
    razor_container.status()


@razor.command(
    name="shell",
    help="Start a shell in running razor docker container"
)
def razor_shell():
    razor_container.shell()

@razor.group(
    name="config",
    help="Modify or view config file"
)
def razor_config():
    pass

@razor_config.command(
    name="view",
    help="View current configrations"
)
def razor_config_view():
    with open('config.json','r') as file:
        razor_config = json.load(file)['RAZOR']
        pprint.pprint(razor_config,sort_dicts=False)
@razor_config.command(
    name="Edit",
    help="Edit current configrations"
)
def razor_config_edit():
    with open('config.json','r+') as file:
        config=json.load(file)
        razor_config = config['RAZOR']['target-apps']
        razor_config=core.recursive_edit(razor_config,'Razor')
        config['RAZOR']['target-apps']=razor_config
    with open('config.json','w') as file:
        file.write(json.dumps(config, indent=4))

@razor_config.command(
    name="reset",
    help="Reset the configurations"
)
def razor_reset():
    with open('config.json','r+') as file:
        config=json.load(file)
        config_default=json.load(open('sources/default_config.json','r+'))
        config['RAZOR']=config_default['RAZOR']
    with open('config.json','w') as file:
        file.write(json.dumps(config, indent=4))
        print('Configurations reset to default')

@razor.command(
    name="run-config",
    help="Run the configurations for Razor in the config file"
)
def razor_run():
    OUTPUT_DIR=json.load(open('config.json','r+'))['OUTPUT_DIR']
    OUTPUT_DIR_RAZOR=os.path.join(OUTPUT_DIR,'Razor')
    RAZOR_CONTAINER_OUTPUT='/razor_bins'
    ARGS=['./sources/management_script.sh',RAZOR_IMAGE,'config.json','python3','adapter_razor.py',OUTPUT_DIR_RAZOR,RAZOR_CONTAINER_OUTPUT]
    core.process_check_call(ARGS)

@razor.group(
    name="examples",
    help="Copy and build default examples"
)
def razor_examples():
    pass


@razor_examples.command(
    name="copy",
    help="Copy defaults examples into examples volume"
)
def razor_examples_copy():
    core.process_check_call(
        [
            'docker', 'exec',
            '--interactive', RAZOR_CONTAINER_NAME,
            'cp', '-rv', f'{container_example_path}/.',
            examples_volume.container_dir
        ]
    )


@razor_examples.command(
    name="list",
    help="List examples"
)
def razor_examples_list():
    for d in example_build_directories():
        print(d)


def filter_condition(dir_path: str, files: List[str]) -> bool:
    # Skipping lib and original dirs
    return 'run_razor.py' in files or 'debloat_simple.py' in files


def example_build_directories():
    example_dir = examples_volume.host_dir
    return core.find_rel_paths(example_dir, filter_condition)


def build_command(example: str) -> str:
    # TODO add params for different heuristic of debloating
    # Might need to remember the current state manually

    if os.path.join(examples_volume.host_dir, example, 'debloat_simple.py'):
        if example == 'simple-demo':

            return f'cd {examples_volume.container_dir}/{example}' \
                    f' && python debloat_simple.py -c trace -a 1 -b y' \
                    f' && python debloat_simple.py -c trace -a 0 -b y' \
                    f' && python debloat_simple.py -c merge_log' \
                    f' && python debloat_simple.py -c dump_inst' \
                    f' && python debloat_simple.py -c instrument' \
                    f' && python debloat_simple.py -c rewrite'

        if example == 'heuristic-demo':

            return f'cd {examples_volume.container_dir}/{example}' \
                    f' && python debloat_simple.py -c trace -a 2 -b 1' \
                    f' && python debloat_simple.py -c trace -a 3 -b 1' \
                    f' && python debloat_simple.py -c merge_log' \
                    f' && python debloat_simple.py -c dump_inst' \
                    f' && python debloat_simple.py -c instrument' \
                    f' && python debloat_simple.py -c rewrite'

    if os.path.join(examples_volume.host_dir, example, 'run_razor.py'):

        return f'cd {examples_volume.container_dir}/{example}' \
               ' && python run_razor.py train' \
               ' && python run_razor.py debloat' \
               ' && python run_razor.py test' \
               ' && python run_razor.py extend_debloat 1'


@razor_examples.command(
    name="build",
    help="Build example(s) in examples volume"
)
@click.option('-e', '--example', help='Name of the example, if not specified, build all')
def razor_examples_build(example: str = None):
    b = builder.PdbBuilder('razor', RAZOR_CONTAINER_NAME)

    try:
        if example:
            b.build(example, build_command(example))

        else:
            for d in example_build_directories():
                b.build(d, build_command(d))

    finally:
        b.close()
