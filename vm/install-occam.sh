#!/bin/bash

# Copyright (c) 2022 SRI International All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

sudo apt-get update
sudo apt-get install -yqq software-properties-common
sudo apt-get update
sudo apt-get install -y wget libprotobuf-dev python-protobuf protobuf-compiler
sudo apt-get install -y python-pip
sudo apt install -y cmake

pip --version && \
    sudo pip install setuptools --upgrade && \
    sudo pip install wheel && \
    sudo pip install protobuf && \
    sudo pip install lit

sudo apt-get install -yqq libboost-dev libffi-dev

mkdir /home/vagrant/go
export GOPATH=/home/vagrant/go

sudo apt-get -y install golang-go && \
    go get github.com/SRI-CSL/gllvm/cmd/...

pushd /vagrant/binaries/llvm-10/build
sudo make install
popd

export OCCAM_HOME=/home/vagrant/occam
export LLVM_HOME=/usr/local/llvm
export LLVM_CONFIG=llvm-config

export PATH="$LLVM_HOME/bin:$GOPATH/bin:$PATH"

echo "
export GOPATH=/home/vagrant/go
export LLVM_HOME=/usr/local/llvm
export OCCAM_HOME=/home/vagrant/occam
export LLVM_CONFIG=llvm-config

export PATH="\$LLVM_HOME/bin:\$GOPATH/bin:\$PATH"
" >> ~/.bashrc

export CC=clang
export CXX=clang++
export LLVM_COMPILER=clang
export WLLVM_OUTPUT=WARNING

pushd /home/vagrant

git clone --recurse-submodules https://github.com/SRI-CSL/OCCAM.git occam --depth=10

 cd occam
 make
 sudo make install
 sudo echo "
__requires__ = 'razor==1.1.0'
import re
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(
        load_entry_point('razor==1.1.0', 'console_scripts', 'slash')()
    )
" > /usr/local/bin/slash


 make test
popd

