# Copyright (c) 2022 SRI International All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import csv
import logging
import os
import subprocess
from datetime import datetime
from typing import Dict, Any, List

from . import core


class ResultWriter:

    def __init__(self, framework: str, columns: List[str]) -> None:
        self.framework = framework
        self.columns = columns
        self.results_file = core.project_relative_location(f'data/{framework}/{framework}-pdbench.csv')
        self.results = []

        logging.info(f'Saving results in {self.results_file}')

        exists = os.path.exists(self.results_file)

        mode = 'a' if exists else 'w'

        self._fp = open(self.results_file, mode, newline='')
        self.writer = csv.writer(self._fp, quoting=csv.QUOTE_MINIMAL)

        if not exists:
            self.writer.writerow(self.columns)

    def flush(self):
        if self._fp and not self._fp.closed:
            self._fp.flush()

    def close(self):
        core.print_table(self.results, self.columns)
        if self._fp and not self._fp.closed:
            self._fp.close()

    def add(self, result: Dict[str, Any]):
        row = [result[c] for c in self.columns]

        self.results.append(row)
        self.writer.writerow(row)
        self.flush()


class PdbBuilder:
    def __init__(self, framework: str, container_name: str) -> None:
        super().__init__()
        self.framework = framework
        self.container_name = container_name
        self.results = ResultWriter(
            framework, ['Project', 'ReturnCode', 'StartTime', 'Duration', 'LogPrefix']
        )

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self.results.close()

    def build(self, project_name: str, cmd: str) -> int:
        logging.info(f"Building project {project_name} in {self.container_name} container")

        core.make_dirs(core.project_relative_location(f"logs/{self.framework}"))

        docker_cmd = [
            'docker', 'exec',
            '--interactive', self.container_name,
            'bash', '-c', cmd
        ]

        e = project_name.replace('/', '_')

        start_time = datetime.now()
        d = start_time.strftime('%Y-%m-%d_%H-%M')

        docker_process = subprocess.Popen(
            docker_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout_process = subprocess.Popen(
            ["tee", core.project_relative_location(f"logs/{self.framework}/{e}-{d}.stdout")],
            stdin=docker_process.stdout
        )

        stderr_process = subprocess.Popen(
            ["tee", core.project_relative_location(f"logs/{self.framework}/{e}-{d}.stderr")],
            stdin=docker_process.stderr
        )

        docker_process.stdout.close()
        docker_process.stderr.close()

        stdout_process.communicate()
        stderr_process.communicate()

        return_code = docker_process.wait()
        end_time = datetime.now()

        if return_code != 0:
            logging.error(f"Failed to execute command {core.command_list_to_str(docker_cmd)}")

        delta = end_time - start_time
        duration = str(delta).split('.', 2)[0]  # Restricting resolution to second

        self.results.add(
            {
                'Project': d,
                'ReturnCode': return_code,
                'StartTime': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'Duration': duration,
                'LogPrefix': f"logs/{self.framework}/{e}-{d}"
            }
        )

        return return_code
