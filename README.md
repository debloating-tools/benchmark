# Benchmark for Comparing Debloating Tools

A unified framework for debloating sources and binaries.

## Prerequisites

**Supported OS**: Ubuntu 20.04

Docker and python with virtual env

    ./init.sh docker-install

(Optional) Change image store directory, if `/var/lib/docker` is mounted in a limited spaced partition

    ./init.sh docker-change-dir <path to new dir>

Install python and virtualenv

    ./init.sh install

After this it will create a symbolic link in project name `pdbench`, use this to execute the project commands, e.g.,

    ./pdbench <framework> start

**Alternatively**, activate the virtualenv with `. venv/bin/activate` and use `pdbench` command, e.g.,

    pdbench <framework> start

## Managing the containers and building projects

Replace `<framework>` with any of `occam`, `piecewise`, `chisel`, `razor`

Pull and start a container

    ./pdbench <framework> start

Check status with `docker ps -a` or `./pdbench <framework> status`

Copy examples into a shared volume mapped in `data/<framework>/volumes/examples`

    ./pdbench <occam|chisel|razor> examples copy

List the examples in the mapped volume

    ./pdbench <occam|chisel|razor> examples list

_`piecewise` container does have examples copy and list command_

Build examples inside the container in the mapped volume

    ./pdbench <framework> examples build

Logs of the build is stored in `logs/<framework>/...` directory and
summary of the execution is saved in `data/<framework>/<framework>-pdbench.csv`

Stop and **remove** the container

    ./pdbench <framework> stop

## Tools

### OCCAM

- __Paper__: Automated Software Winnowing
- __Published__: ACM SAC 2015
- __Code__: <https://github.com/SRI-CSL/OCCAM>

### Piecewise

- __Paper__: Debloating Software through Piece-Wise Compilation and Loading
- __Published__: USENIX Security 2018
- __Code__: <https://github.com/bingseclab/piecewise>

### Chisel

- __Paper__: Effective Program Debloating via Reinforcement Learning.
- __Published__: ACM CCS 2018
- __Code__: <https://github.com/aspire-project/chisel>
- __Home__: <https://chisel.cis.upenn.edu/>

### Razor

- __Paper__: RAZOR: A Framework for Post-deployment Software Debloating
- __Published__: USENIX Security 2019
- __Code__: <https://github.com/cxreet/razor>
- __Wiki__: <https://github.com/cxreet/razor/wiki>

## Under the hood - Docker container management

We start the containers in a detached mode, i.e. running as daemon.

    docker run ... -d

We execute commands in the containers with `exec` command.

    docker exec ... bash -c "uname -a"

To interact with the container we can use same technique

    docker exec ... -it bash

---

This material is based upon work supported by the National Science Foundation (NSF) under Grant ACI-1440800 and the Office of Naval Research (ONR) under Contracts N68335-17-C-0558 and N00014-18-1-2660. Any opinions, findings, and conclusions or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of NSF or ONR.
