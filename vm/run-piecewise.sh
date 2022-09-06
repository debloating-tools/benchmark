#!/bin/bash

#run piecewise
sudo docker run -it --cap-add=SYS_PTRACE --security-opt seccomp=unconfined piecewise0001bloat/piecewise
