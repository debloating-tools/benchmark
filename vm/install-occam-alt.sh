#!/bin/bash

# Copyright (c) 2022 SRI International All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

docker pull sricsl/occam:bionic
docker run -v `pwd`:/host -it sricsl/occam:bionic

