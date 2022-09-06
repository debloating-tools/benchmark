#!/bin/bash

docker pull sricsl/occam:bionic
docker run -v `pwd`:/host -it sricsl/occam:bionic

