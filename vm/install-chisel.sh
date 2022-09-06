#!/bin/bash

sudo apt-get update
sudo apt install -y cmake libmlpack-dev
sudo apt install -y clang-8 libclang-8-dev llvm-8-dev

pushd /home/vagrant
git clone https://github.com/gabime/spdlog.git
cd spdlog && mkdir build && cd build
cmake .. && make -j
sudo make install
popd

export CC=clang-8
export CXX=clang++-8
set CMAKE_CXX_FLAGS "$CMAKE_CXX_FLAGS -frtti"
pushd /home/vagrant
git clone https://github.com/aspire-project/chisel.git
cd chisel
mkdir build && cd build
cmake ..
make
popd

echo 'export PATH=/home/vagrant/chisel/build/bin:$PATH' >> /home/vagrant/.bashrc

pushd /home/vagrant
git clone https://github.com/aspire-project/chiselbench
popd
