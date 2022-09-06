## Prerequisites

1. VirtualBox
2. Docker
3. Vagrant

Debloating tools vs Requirements

| Tool      | LLVM version | Management |
|:---------:|:------------:|:----------:|
| OCCAM     | 10.0.0       | Vagrant    |
| Razor     | ---          | Docker     |
| Chisel    | 8.0.0        | Vagrant    |
| Piecewise | 4.0.0        | Docker     |

### Steps

1. Run `vagrant up` to create OCCAM and Chisel machines.
2. When machines are created, run `install-llvm.sh` from inside OCCAM VM to install llvm to it. After that
   run `install-occam.sh` to install occam inside the VM. Note that OCCAM also comes within a docker container, which
   can be downloaded by running `install-occam-alt.sh`.
3. Run `install-chisel.sh` to install Chisel and download chiselbench in the chisel VM.
4. Run `install-piecewise.sh` to download piecewise's Docker container.
5. Run `install-razor.sh` to download Razor's Docker container.
6. `run-*` scripts are to run the corresponding tools. `run` scripts corresponding to the tools installed in Vagrant VM
   should be run from inside the VM.

## FAQs:

1. How to solve "The permissions of the private key should be set to 0600" problem? Answer:

        mv /path/to/private_key /path/to/change/permission/
        chmod 0600 /path/to/change/permission/private_key
        ln /path/to/change/permission/private_key /path/to/private_key

2. How to change virtualbox's default machine folder? Answer:

        vboxmanage setproperty machinefolder /path/to/new/folder

3. Install disksize plugin. Answer:

        vagrant plugin install vagrant-disksize`
