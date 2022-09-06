# Copyright (c) 2022 SRI International All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import logging
import os
from typing import List

import docker
from colorama import Fore

from .core import Volume, make_dirs, process_check_call, cli, print_table, ProDeBenchError


class ContainerWrapper:
    def __init__(self, image: str, name: str, volumes: List[Volume]) -> None:
        super().__init__()
        self.image = image
        self.name = name
        self.volumes = volumes

    def start(self, additional_args: List[str] = None):
        cmd = [
            'docker', 'run',
            '--name', self.name,
        ]

        if additional_args:
            cmd.extend(additional_args)

        for v in self.volumes:
            make_dirs(v.host_dir)

            cmd.append('-v')
            cmd.append(f"{v.host_dir}:{v.container_dir}")

        cmd.extend(['-t', '-d', self.image])
        process_check_call(cmd)

    def stop(self):
        logging.info(f"Stopping container {self.name}")
        process_check_call(["docker", "stop", self.name])

        self.remove()

    def remove(self):
        logging.info(f"Removing container {self.name}")
        process_check_call(["docker", "rm", self.name])

    def status(self):
        print_colored_status({'name': self.name})

    def shell(self, cmd: str = 'bash'):
        os.system(f'docker exec -it "{self.name}" {cmd}')


def print_colored_status(filters=None):
    client = docker.from_env()

    headers = ['Image', 'Container', 'Status']
    rows = []

    for c in client.containers.list(all=True, filters=filters):
        if c.status == 'exited':
            status_colored = Fore.RED + c.status + Fore.RESET
        elif c.status == 'running':
            status_colored = Fore.GREEN + c.status + Fore.RESET
        else:
            status_colored = c.status

        rows.append([','.join(c.image.tags), c.name, status_colored])

    print_table(rows, headers)


@cli.command(
    help="Check status of containers"
)
def status():
    print_colored_status()


@cli.command(
    help="Remove exited containers"
)
def remove():
    client = docker.from_env()

    to_remove = []
    for c in client.containers.list(all=True):
        if c.status == 'exited':
            to_remove.append(c.name)

    if not to_remove:
        logging.info("No existed container found")
        return

    for c in to_remove:
        try:
            logging.info(f"Removing container {c}")
            process_check_call(["docker", "rm", c])
        except ProDeBenchError as e:
            logging.warning(e.args[0])
