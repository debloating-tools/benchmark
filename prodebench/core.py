# Copyright (c) 2022 SRI International All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import logging
import os
import shlex
import subprocess
from collections import namedtuple
from typing import List, Callable, Iterator
import click
import coloredlogs
from tabulate import tabulate

logging_format = '[%(asctime)s] %(levelname)s: %(message)s'
coloredlogs.install(level='INFO', logger=logging.getLogger(), fmt=logging_format)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
cli = click.Group(name='prodebench', help="ProDeBench management script", context_settings=CONTEXT_SETTINGS)

Volume = namedtuple('Volume', ['host_dir', 'container_dir'])


def command_list_to_str(cmd: List[str]) -> str:
    return ' '.join([shlex.quote(c) for c in cmd])


def process_check_call(cmd: List[str], cwd: str = None):
    try:
        if not cwd:
            cwd = project_relative_location()

        return subprocess.check_call(cmd, cwd=cwd, preexec_fn=os.setsid)
    except subprocess.CalledProcessError:
        raise ProDeBenchError(f"Failed to execute command {command_list_to_str(cmd)}")


def print_table(rows, headers):
    print(tabulate(rows, headers=headers, tablefmt="pipe", numalign="right"))


def project_relative_location(*args: str):
    return os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', *args))


def make_dirs(dir_path: str, mode=0o755):
    if not os.path.exists(dir_path):
        logging.info("Creating directory: {}".format(dir_path))
        os.makedirs(dir_path, mode=mode)


def make_parent_dirs(file_path: str, mode=0o755):
    make_dirs(os.path.dirname(file_path), mode)


def find_rel_paths(dir_path: str, condition: Callable[[str, List[str]], bool]) -> Iterator[str]:
    for folder, subs, files in os.walk(dir_path):

        if condition(folder, files):
            yield folder.replace(dir_path, '')[1:]

            # Ignoring sub directories
            del subs[:]


def write_executable_script(path: str, content: str):
    previous_mask = os.umask(0)

    try:
        logging.info(f"Writing build script at {path}")
        with open(os.open(path, os.O_CREAT | os.O_WRONLY, 0o755), 'w') as f:
            f.write(content)

    finally:
        os.umask(previous_mask)


class ProDeBenchError(click.ClickException):

    def __init__(self, message, exit_code=-1):
        super().__init__(message)
        self.exit_code = exit_code

    def show(self, file=None):
        if file:
            super().show(file)
            return

        logging.error(self.message)
        
def recursive_edit(config,s_param='',counter=0):
    if type(config)==dict:
        for param in config:
            if s_param!='':
                print(counter*'\t'+f'{s_param}:')
            config[param]=recursive_edit(config[param],param,counter+1)
        return config
    elif type(config)==list:
        return list(filter(lambda x: len(x), input(counter*'\t'+f'{s_param}'f'(comma separated): ').split(',')))
    else:
        return input(counter*'\t'+f'{s_param}: ')