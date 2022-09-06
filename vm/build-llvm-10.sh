#!/bin/bash

echo "Downloading LLVM code ..."

#llvm 10
mkdir sources/llvm-10
wget https://github.com/llvm/llvm-project/releases/download/llvmorg-10.0.0/llvm-10.0.0.src.tar.xz -P sources/llvm-10
wget https://github.com/llvm/llvm-project/releases/download/llvmorg-10.0.0/clang-10.0.0.src.tar.xz -P sources/llvm-10
wget https://github.com/llvm/llvm-project/releases/download/llvmorg-10.0.0/compiler-rt-10.0.0.src.tar.xz -P sources/llvm-10
wget https://github.com/llvm/llvm-project/releases/download/llvmorg-10.0.0/clang-tools-extra-10.0.0.src.tar.xz -P sources/llvm-10

echo "Extract source code ..."

mkdir -p binaries/llvm-10

tar -xf sources/llvm-10/llvm-10.0.0.src.tar.xz -C binaries/llvm-10
tar -xf sources/llvm-10/clang-10.0.0.src.tar.xz -C binaries/llvm-10
tar -xf sources/llvm-10/compiler-rt-10.0.0.src.tar.xz -C binaries/llvm-10
tar -xf sources/llvm-10/clang-tools-extra-10.0.0.src.tar.xz -C binaries/llvm-10

mv binaries/llvm-10/llvm-10.0.0.src binaries/llvm-10/llvm
mv binaries/llvm-10/clang-10.0.0.src binaries/llvm-10/clang
mv binaries/llvm-10/compiler-rt-10.0.0.src binaries/llvm-10/compiler-rt
mv binaries/llvm-10/clang-tools-extra-10.0.0.src binaries/llvm-10/clang-tools-extra

echo "Install dependencies ..."


sudo apt -y update
sudo apt -y install g++ build-essential libxml2-dev ocaml cmake libspdlog-dev libmlpack-dev

echo "Building LLVM ..."

mkdir -p binaries/llvm-10/build

pushd binaries/llvm-10/build

cmake -DLLVM_ENABLE_PROJECTS="clang;clang-tools-extra;compiler-rt" -DLLVM_INSTALL_UTILS=ON -DCMAKE_INSTALL_PREFIX=/usr/local/llvm -G "Unix Makefiles" -DLLVM_BUILD_LLVM_DYLIB=ON -DCMAKE_BUILD_TYPE=Release -DLLVM_USE_LINKER=gold ../llvm
make

mkdir /usr/local/llvm
sudo make install

popd

echo "
export LLVM_HOME=/usr/local/llvm

export PATH=\$PATH:~/bin:\$LLVM_HOME/bin
" >> ~/.bashrc
